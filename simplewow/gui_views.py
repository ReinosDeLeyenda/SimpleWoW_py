from __future__ import annotations

import flet as ft

from .gui_theme import (
    ICE_BORDER,
    ICE_BTN_BG,
    ICE_DIVIDER,
    ICE_PANEL,
    ICE_PANEL_ALT,
    ICE_PRIMARY,
)


class GUIViewsMixin:
    """Define los controles y las vistas de pantalla de Flet con temática Azul Hielo."""

    def _build_controls(self) -> None:
        # --- ADMINISTRADOR DE CUENTAS ---
        self.saved_accounts_dropdown = ft.Dropdown(
            label="Cuentas guardadas",
            expand=True,
            border_color=ICE_BORDER,
            bgcolor=ICE_PANEL,
            on_select=self._on_select_saved_account,
        )
        self.delete_account_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color="#F87171",
            tooltip="Eliminar cuenta guardada",
            on_click=self._on_delete_saved_account,
        )

        # --- LOGIN ---
        self.host_input = ft.TextField(
            label="Host (Auth Server)",
            value="wow.reinosdeleyenda.org",
            border_color=ICE_BORDER,
            bgcolor=ICE_PANEL,
        )
        self.port_input = ft.TextField(
            label="Puerto",
            value="3724",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=ICE_BORDER,
            bgcolor=ICE_PANEL,
        )
        self.user_input = ft.TextField(
            label="Usuario",
            value="",
            border_color=ICE_BORDER,
            bgcolor=ICE_PANEL,
            on_submit=self._handle_connect_click,
        )
        self.pass_input = ft.TextField(
            label="Contraseña",
            value="",
            password=True,
            can_reveal_password=True,
            border_color=ICE_BORDER,
            bgcolor=ICE_PANEL,
            on_submit=self._handle_connect_click,
        )
        self.remember_checkbox = ft.Checkbox(
            label="Recordar cuenta (cifrado seguro)",
            value=True,
            active_color=ICE_BORDER,
            check_color="#08121E",
        )
        self.login_status = ft.Text("", color="#F87171")
        self.connect_btn = ft.Button(
            content="Conectar",
            bgcolor=ICE_BTN_BG,
            color=ICE_PRIMARY,
            height=45,
            on_click=self._handle_connect_click,
        )

        # --- SELECCIÓN REINO / PERSONAJE ---
        self.realms_column = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
        self.chars_column = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
        self.selection_log = ft.ListView(height=120, spacing=2, auto_scroll=True)

        # --- CHAT ---
        self.chat_header = ft.Text("En el mundo", size=18, weight=ft.FontWeight.BOLD, color=ICE_PRIMARY)
        self.chat_list = ft.ListView(expand=True, spacing=4, auto_scroll=True)

        self.channel_dropdown = ft.Dropdown(
            value="Guild",
            width=135,
            border_color=ICE_BORDER,
            bgcolor=ICE_PANEL,
            options=[
                ft.dropdown.Option("Say", "Decir (/s)"),
                ft.dropdown.Option("Yell", "Gritar (/y)"),
                ft.dropdown.Option("Guild", "Hermandad (/g)"),
                ft.dropdown.Option("Officer", "Oficial (/o)"),
                ft.dropdown.Option("Party", "Grupo (/p)"),
                ft.dropdown.Option("Raid", "Banda (/ra)"),
                ft.dropdown.Option("Whisper", "Susurrar (/w)"),
                ft.dropdown.Option("Channel", "Canal (/1)"),
            ],
        )
        self.target_input = ft.TextField(
            hint_text="Destino / Canal",
            width=145,
            border_color=ICE_BORDER,
            bgcolor=ICE_PANEL,
        )
        self.msg_input = ft.TextField(
            hint_text="Escribe un mensaje...",
            expand=True,
            border_color=ICE_BORDER,
            bgcolor=ICE_PANEL,
            on_submit=self._handle_send_chat,
        )
        self.send_btn = ft.IconButton(
            icon=ft.Icons.SEND,
            icon_color=ICE_BORDER,
            on_click=self._handle_send_chat,
        )

    def _show_login_view(self) -> None:
        if not self.page:
            return
        self.page.controls.clear()
        self.page.add(
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=ft.Container(
                    width=440,
                    padding=24,
                    bgcolor=ICE_PANEL,
                    border_radius=14,
                    border=ft.Border.all(1, ICE_DIVIDER),
                    content=ft.Column(
                        tight=True,
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.AC_UNIT, color=ICE_BORDER, size=28),
                                    ft.Text("SimpleWoW Chat", size=26, weight=ft.FontWeight.BOLD, color=ICE_PRIMARY),
                                ],
                            ),
                            ft.Row([self.saved_accounts_dropdown, self.delete_account_btn]),
                            ft.Divider(height=1, color=ICE_DIVIDER),
                            self.host_input,
                            self.port_input,
                            self.user_input,
                            self.pass_input,
                            self.remember_checkbox,
                            self.connect_btn,
                            self.login_status,
                        ],
                    ),
                ),
            )
        )
        self.page.update()

    def _show_selection_view(self) -> None:
        if not self.page:
            return
        self.page.controls.clear()
        self.page.add(
            ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.AC_UNIT, color=ICE_BORDER, size=22),
                            ft.Text("Reinos y Personajes", size=20, weight=ft.FontWeight.BOLD, color=ICE_PRIMARY),
                        ]
                    ),
                    ft.ResponsiveRow(
                        expand=True,
                        controls=[
                            ft.Container(
                                col={"xs": 12, "md": 6},
                                bgcolor=ICE_PANEL,
                                border_radius=10,
                                border=ft.Border.all(1, ICE_DIVIDER),
                                padding=12,
                                content=ft.Column([ft.Text("Reinos", weight=ft.FontWeight.BOLD, color=ICE_PRIMARY), self.realms_column]),
                            ),
                            ft.Container(
                                col={"xs": 12, "md": 6},
                                bgcolor=ICE_PANEL,
                                border_radius=10,
                                border=ft.Border.all(1, ICE_DIVIDER),
                                padding=12,
                                content=ft.Column([ft.Text("Personajes", weight=ft.FontWeight.BOLD, color=ICE_PRIMARY), self.chars_column]),
                            ),
                        ],
                    ),
                    ft.Container(
                        bgcolor=ICE_PANEL_ALT,
                        border_radius=8,
                        border=ft.Border.all(1, ICE_DIVIDER),
                        padding=8,
                        content=self.selection_log,
                    ),
                ],
            )
        )
        self.page.update()

    def _show_chat_view(self) -> None:
        if not self.page:
            return
        self.page.controls.clear()
        self.page.add(
            ft.Column(
                expand=True,
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row([ft.Icon(ft.Icons.AC_UNIT, color=ICE_BORDER, size=20), self.chat_header]),
                            ft.OutlinedButton(
                                content="Desconectar",
                                style=ft.ButtonStyle(color=ICE_PRIMARY, side=ft.BorderSide(1, ICE_BORDER)),
                                on_click=self._handle_disconnect,
                            ),
                        ],
                    ),
                    ft.Container(
                        expand=True,
                        bgcolor=ICE_PANEL_ALT,
                        border_radius=10,
                        border=ft.Border.all(1, ICE_DIVIDER),
                        padding=12,
                        content=self.chat_list,
                    ),
                    ft.Row(spacing=6, controls=[self.channel_dropdown, self.target_input, self.msg_input, self.send_btn]),
                ],
            )
        )
        self.page.update()
