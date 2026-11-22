from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import flet as ft

from .definitions import ChatMessageType, Language, LogLevel, is_horde
from .opcodes import WorldCommand
from .packets import OutPacket

if TYPE_CHECKING:
    from .auth import WorldServerInfo
    from .character import Character


class GUIActionsMixin:
    """Maneja las acciones del usuario y la gestión de cuentas en la UI."""

    def _refresh_saved_accounts(self, auto_fill_first: bool = True) -> None:
        accounts = self.account_manager.list_accounts()
        self.saved_accounts_dropdown.options = [
            ft.dropdown.Option(acc["id"], f"{acc['username']} @ {acc['host']}:{acc['port']}")
            for acc in accounts
        ]
        if accounts and auto_fill_first:
            first = accounts[0]
            self.saved_accounts_dropdown.value = first["id"]
            self._load_account_into_fields(first["id"])
        elif not accounts:
            self.saved_accounts_dropdown.value = None

    def _load_account_into_fields(self, account_id: str) -> None:
        accounts = {a["id"]: a for a in self.account_manager.list_accounts()}
        acc = accounts.get(account_id)
        if not acc:
            return
        self.host_input.value = acc["host"]
        self.port_input.value = str(acc["port"])
        self.user_input.value = acc["username"]
        self.pass_input.value = self.account_manager.get_password(account_id) or ""

    def _on_select_saved_account(self, e) -> None:
        acc_id = self.saved_accounts_dropdown.value
        if acc_id:
            self._load_account_into_fields(acc_id)
            if self.page:
                self.page.update()

    def _on_delete_saved_account(self, e) -> None:
        acc_id = self.saved_accounts_dropdown.value
        if not acc_id:
            return
        self.account_manager.delete_account(acc_id)
        self.user_input.value = ""
        self.pass_input.value = ""
        self._refresh_saved_accounts(auto_fill_first=True)
        if self.page:
            self.page.update()

    def _handle_connect_click(self, e) -> None:
        host = (self.host_input.value or "").strip()
        port = int((self.port_input.value or "3724").strip())
        user = (self.user_input.value or "").strip()
        password = (self.pass_input.value or "").strip()

        if not host or not user or not password:
            self.login_status.value = "Rellena todos los campos."
            self.page.update()
            return

        if self.remember_checkbox.value:
            self.account_manager.save_account(host, port, user, password)
            self._refresh_saved_accounts(auto_fill_first=False)
            self.saved_accounts_dropdown.value = f"{user.lower()}@{host.lower()}:{port}"

        self.connect_btn.disabled = True
        self.login_status.value = "Conectando..."
        self.page.update()

        if self.on_connect_callback:
            self.on_connect_callback(host, port, user, password)

    def _select_realm(self, realm: "WorldServerInfo") -> None:
        self.log_line(f"Conectando a {realm.name}...", LogLevel.Info)
        threading.Thread(target=self.game.connect_to, args=(realm,), daemon=True).start()

    def _select_character(self, char: "Character") -> None:
        pkt = OutPacket(WorldCommand.CMSG_PLAYER_LOGIN)
        pkt.write_u64(char.guid)
        self.game.send_packet(pkt)
        self.game.world.selected_character = char

        self.chat_header.value = f"{char.name} (Nv. {char.level})"
        self._show_chat_view()

    def _handle_send_chat(self, e) -> None:
        text = (self.msg_input.value or "").strip()
        if not text:
            return
        self.msg_input.value = ""
        self.page.update()

        selected_char = self.game.world.selected_character
        if selected_char is None:
            return

        channel_name = self.channel_dropdown.value or "Guild"
        chat_type = getattr(ChatMessageType, channel_name, ChatMessageType.Guild)
        target = (self.target_input.value or "").strip()

        if chat_type in (ChatMessageType.Whisper, ChatMessageType.Channel) and not target:
            self.chat_list.controls.append(
                ft.Text("[ERROR]: Escribe el nombre del jugador o canal en 'Destino / Canal'.", color="#FF4444")
            )
            self.page.update()
            return

        pkt = OutPacket(WorldCommand.CMSG_MESSAGECHAT)
        pkt.write_u32(chat_type)
        pkt.write_u32(Language.Orcish if is_horde(selected_char.race) else Language.Common)
        if chat_type in (ChatMessageType.Whisper, ChatMessageType.Channel):
            pkt.write_cstring(target)
        pkt.write_cstring(text)
        self.game.send_packet(pkt)

    def _handle_disconnect(self, e) -> None:
        if hasattr(self, "game") and self.game is not None:
            self.game.exit()
        self._show_login_view()
