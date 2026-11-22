"""Entry point (GUI-only cross-platform: Windows, Linux, macOS, Android)."""
from __future__ import annotations

import asyncio
import os
import sys
import threading
import flet as ft

from .definitions import LogLevel
from .game import Game
from .gui_ui import FletUI


def start_app(page: ft.Page) -> None:
    # Silenciar WinError 10022 conocido de asyncio ProactorEventLoop al cerrar Flet en Windows
    if sys.platform == "win32":
        loop = asyncio.get_running_loop()
        default_handler = loop.get_exception_handler()

        def ignore_winerror_10022(loop, context):
            exc = context.get("exception")
            if isinstance(exc, OSError) and getattr(exc, "winerror", None) == 10022:
                return
            if default_handler:
                default_handler(loop, context)
            else:
                loop.default_exception_handler(context)

        loop.set_exception_handler(ignore_winerror_10022)

    ui = FletUI()
    ui.attach_page(page)

    def on_connect(hostname: str, port: int, username: str, password: str) -> None:
        game = Game(
            ui_class=lambda: ui,
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            log_level=LogLevel.Info,
        )
        threading.Thread(target=game.start, daemon=True).start()

    ui.on_connect_callback = on_connect


def main(argv=None) -> int:
    ft.run(start_app)
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
