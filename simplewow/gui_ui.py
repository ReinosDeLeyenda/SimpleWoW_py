from __future__ import annotations

import asyncio
import os
import queue
import threading
from typing import TYPE_CHECKING, Callable, List, Optional

import flet as ft

from .accounts import AccountManager
from .definitions import LogLevel, PlayerClass, Race, enum_name
from .gui_actions import GUIActionsMixin
from .gui_theme import LOG_COLORS, build_chat_text_control
from .gui_views import GUIViewsMixin
from .ui import GameUI

if TYPE_CHECKING:
    from .auth import WorldServerInfo, WorldServerList
    from .character import Character
    from .chat import ChatMessage
    from .game import Game


class FletUI(GUIViewsMixin, GUIActionsMixin, GameUI):
    """Interfaz gráfica multiplataforma (Windows, Linux, macOS, Android)."""

    def __init__(self) -> None:
        self.game: "Game"
        self.log_level: LogLevel = LogLevel.Info

        self._queue: queue.Queue = queue.Queue()
        self._realms: List["WorldServerInfo"] = []
        self._characters: List["Character"] = []
        self._closed = False
        self.page: Optional[ft.Page] = None
        self.account_manager = AccountManager()

        self.on_connect_callback: Optional[Callable[[str, int, str, str], None]] = None

    def attach_page(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "SimpleWoW Chat - Reinos de Leyenda"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#141414"
        self.page.padding = 16
        self.page.on_disconnect = self._on_app_close
        self.page.window.prevent_close = True
        self.page.window.on_event = self._on_window_event

        self._build_controls()
        self._refresh_saved_accounts()
        self._show_login_view()

        self.page.run_task(self._async_queue_worker)

    async def _on_window_event(self, e: ft.WindowEvent) -> None:
        if e.type == ft.WindowEventType.CLOSE:
            self._on_app_close()
            if self.page:
                await self.page.window.destroy()
            os._exit(0)

    def _on_app_close(self, e=None) -> None:
        self._closed = True
        if hasattr(self, "game") and self.game is not None:
            self.game.exit()

    # -- Métodos abstractos de GameUI --------------------------------------------------
    def update(self) -> None:
        threading.Event().wait(0.05)

    def exit(self) -> None:
        self._queue.put(("EXIT", None))

    def present_realm_list(self, realm_list: "WorldServerList") -> None:
        self._queue.put(("REALMS", list(realm_list)))

    def present_character_list(self, characters: "List[Character]") -> None:
        self._queue.put(("CHARS", list(characters)))

    def present_chat_message(self, message: "ChatMessage") -> None:
        self._queue.put(("CHAT", message))

    def world_entered(self) -> None:
        self.log_line("¡Has entrado al mundo!", LogLevel.Info)

    def no_characters(self) -> None:
        self.log_line("No se encontraron personajes en este reino.", LogLevel.Warning)

    def character_login_failed(self, result: int) -> None:
        self.log_line(f"Error al entrar con el personaje ({result}).", LogLevel.Error)

    def log(self, message: str, level: LogLevel = LogLevel.Info) -> None:
        if level >= self.log_level:
            self._queue.put(("LOG", (message, level)))

    def log_line(self, message: str = "", level: LogLevel = LogLevel.Info) -> None:
        self.log(message, level)

    def log_exception(self, message: str) -> None:
        self._queue.put(("LOG", (f"[EXCEPTION] {message}", LogLevel.Error)))

    def read_line(self) -> str:
        return ""

    def read_key(self, timeout: Optional[float] = None) -> Optional[str]:
        return None

    # -- Procesador asíncrono de red -> UI ---------------------------------------------
    async def _async_queue_worker(self) -> None:
        while not self._closed:
            if not self.page:
                await asyncio.sleep(0.02)
                continue

            updated = False
            try:
                while True:
                    event, payload = self._queue.get_nowait()
                    updated = True

                    if event == "REALMS":
                        self._realms = payload
                        self.realms_column.controls.clear()
                        for realm in self._realms:
                            self.realms_column.controls.append(
                                ft.Button(
                                    content=f"{realm.name} ({realm.address}:{realm.port})",
                                    bgcolor="#2d261c",
                                    color="#ffffff",
                                    on_click=lambda e, r=realm: self._select_realm(r),
                                )
                            )
                        self._show_selection_view()
                        if len(self._realms) == 1:
                            self._select_realm(self._realms[0])

                    elif event == "CHARS":
                        self._characters = payload
                        self.chars_column.controls.clear()
                        for char in self._characters:
                            race_str = enum_name(Race, char.race)
                            class_str = enum_name(PlayerClass, char.player_class)
                            self.chars_column.controls.append(
                                ft.Button(
                                    content=f"{char.name} - Nv. {char.level} ({race_str} {class_str})",
                                    bgcolor="#2d261c",
                                    color="#ffd100",
                                    on_click=lambda e, c=char: self._select_character(c),
                                )
                            )

                    elif event == "CHAT":
                        ctrl = build_chat_text_control(payload, self.game, self.target_input)
                        if ctrl is not None:
                            self.chat_list.controls.append(ctrl)

                    elif event == "LOG":
                        text, level = payload
                        if text.strip():
                            color = LOG_COLORS.get(level, "#CCCCCC")
                            self.selection_log.controls.append(ft.Text(text, color=color, size=12))
                            self.chat_list.controls.append(ft.Text(text, color=color, size=12))
                            if level == LogLevel.Error:
                                self.login_status.value = text
                                self.connect_btn.disabled = False

                    elif event == "EXIT":
                        self.connect_btn.disabled = False
                        self._show_login_view()

            except queue.Empty:
                pass

            if updated:
                self.page.update()

            await asyncio.sleep(0.015)
