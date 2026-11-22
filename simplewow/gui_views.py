from __future__ import annotations

import flet as ft

from .gui_controls import GUIControlsMixin
from .gui_theme import (
    ICE_BORDER,
    ICE_DIVIDER,
    ICE_PANEL,
    ICE_PANEL_ALT,
    ICE_PRIMARY,
)


class GUIViewsMixin(GUIControlsMixin):
    """Renderiza las 3 pantallas principales con temática Azul Hielo."""

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
                            self.update_banner,
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
