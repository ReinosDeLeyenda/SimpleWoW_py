from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from .definitions import ChatMessageType, ChatTag, Language, LogLevel

if TYPE_CHECKING:
    from .chat import ChatMessage
    from .game import Game

# Paleta Azul Hielo (Wrath of the Lich King)
ICE_BG_DARK = "#08121E"       # Fondo principal abismo glacial
ICE_PANEL = "#0F2137"         # Paneles y tarjetas
ICE_PANEL_ALT = "#0A1829"     # Contenedor de chat y logs
ICE_BORDER = "#38BDF8"        # Azul hielo brillante (bordes y acentos)
ICE_PRIMARY = "#7DD3FC"       # Azul escarcha claro (títulos)
ICE_BTN_BG = "#163859"        # Fondo de botones principales
ICE_BTN_ITEM = "#132D46"      # Fondo de botones de reinos/personajes
ICE_TEXT_MAIN = "#E0F2FE"     # Texto blanco azulado
ICE_DIVIDER = "#1E3A5F"       # Líneas divisoras

CHAT_COLORS = {
    ChatMessageType.Channel: "#FFC0C0",
    ChatMessageType.Whisper: "#FF80FF",
    ChatMessageType.WhisperInform: "#FF80FF",
    ChatMessageType.WhisperForeign: "#FF80FF",
    ChatMessageType.System: "#7DD3FC",
    ChatMessageType.Money: "#FDE047",
    ChatMessageType.TargetIcons: "#FDE047",
    ChatMessageType.Achievement: "#38BDF8",
    ChatMessageType.Emote: "#FB7185",
    ChatMessageType.TextEmote: "#FB7185",
    ChatMessageType.MonsterEmote: "#FB7185",
    ChatMessageType.Party: "#93C5FD",
    ChatMessageType.PartyLeader: "#38BDF8",
    ChatMessageType.Raid: "#FB923C",
    ChatMessageType.RaidLeader: "#F97316",
    ChatMessageType.RaidWarning: "#F43F5E",
    ChatMessageType.Guild: "#4ADE80",
    ChatMessageType.GuildAchievement: "#4ADE80",
    ChatMessageType.Officer: "#22C55E",
    ChatMessageType.Yell: "#F87171",
    ChatMessageType.Say: "#E0F2FE",
}

LOG_COLORS = {
    LogLevel.Debug: "#64748B",
    LogLevel.Detail: "#94A3B8",
    LogLevel.Warning: "#FBBF24",
    LogLevel.Info: "#BAE6FD",
    LogLevel.Error: "#F87171",
}


def build_chat_text_control(message: "ChatMessage", game: "Game", target_input: ft.TextField) -> ft.Text | None:
    """Convierte un ChatMessage recibido en un control ft.Text coloreado."""
    if message.language == Language.Addon:
        return None

    chat_type = message.sender.type
    prefix = "Para: " if chat_type == ChatMessageType.WhisperInform else chat_type.name
    if chat_type == ChatMessageType.Channel:
        prefix += f" [{message.sender.channel_name}]"
    elif chat_type == ChatMessageType.Whisper:
        game.world.last_whisperers.append(message.sender.sender)
        if not target_input.value:
            target_input.value = message.sender.sender

    tags = ""
    if message.chat_tag & ChatTag.Gm:
        tags += "<GM>"
    if message.chat_tag & ChatTag.Afk:
        tags += "<AFK>"
    if message.chat_tag & ChatTag.Dnd:
        tags += "<DND>"

    sender_name = message.sender.sender
    formatted = f"{prefix} [{tags}{sender_name}]: {message.message}" if sender_name else f"{prefix}: {message.message}"
    color = CHAT_COLORS.get(chat_type, ICE_TEXT_MAIN)
    return ft.Text(formatted, color=color, selectable=True)
