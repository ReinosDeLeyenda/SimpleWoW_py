from __future__ import annotations

import flet as ft

from .gui_theme import (
    ICE_BORDER,
    ICE_BTN_BG,
    ICE_PANEL,
    ICE_PRIMARY,
)


class GUIControlsMixin:
    """Inicializa todos los controles de Flet para la interfaz Azul Hielo."""

    def _build_controls(self) -> None:
        # --- BUSCADOR DE ACTUALIZACIONES ---
        self.update_url: str = ""
        self.update_banner_text = ft.Text("", color="#38BDF8", size=12, expand=True)
        self.update_banner = ft.Container(
            visible=False,
            bgcolor="#132D46",
            border=ft.Border.all(1, ICE_BORDER),
            border_radius=8,
            padding=8,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Icon(ft.Icons.SYSTEM_UPDATE_ALT, color=ICE_BORDER, size=20),
                    self.update_banner_text,
#                    ft.Button(
#                        content="Descargar",
#                        bgcolor=ICE_BTN_BG,
#                        color=ICE_PRIMARY,
#                        height=32,
#                        on_click=self._on_download_update_click,
#                    ),
                ],
            ),
        )

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
