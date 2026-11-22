from __future__ import annotations

import json
import os
import sys
import urllib.request
from dataclasses import dataclass
from typing import Optional

from . import __version__

# Cambia esto por tu usuario/repositorio real de GitHub
GITHUB_REPO = "ReinosDeLeyenda/simplewow-py"
LATEST_RELEASE_API = f"https://github.com{GITHUB_REPO}/releases/latest"


@dataclass
class UpdateInfo:
    version: str
    download_url: str
    release_url: str
    notes: str


def _parse_version(v: str) -> tuple[int, ...]:
    """Convierte 'v0.2.1' o '0.20' en una tupla comparable (0, 2, 1)."""
    clean = v.strip().lstrip("vV")
    parts = []
    for p in clean.split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _pick_asset_for_current_os(assets: list[dict], fallback_url: str) -> str:
    """Selecciona el binario adecuado según el sistema operativo."""
    is_android = "ANDROID_ARGUMENT" in os.environ or "FLET_APP_STORAGE_DATA" in os.environ and sys.platform == "linux"
    platform = sys.platform

    for asset in assets:
        name = asset.get("name", "").lower()
        url = asset.get("browser_download_url", "")
        if not url:
            continue

        if is_android and name.endswith(".apk"):
            return url
        if platform == "win32" and name.endswith(".exe"):
            return url
        if platform == "darwin" and ("macos" in name or name.endswith(".dmg") or name.endswith(".zip")):
            return url
        if platform.startswith("linux") and not is_android and "linux" in name:
            return url

    return fallback_url


def check_for_updates(current_version: str = __version__) -> Optional[UpdateInfo]:
    """Consulta GitHub Releases y devuelve UpdateInfo si hay una versión más reciente."""
    req = urllib.request.Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SimpleWoW-Chat-Updater",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    tag_name = data.get("tag_name", "")
    if not tag_name:
        return None

    if _parse_version(tag_name) > _parse_version(current_version):
        release_url = data.get("html_url", f"https://github.com{GITHUB_REPO}/releases/latest")
        assets = data.get("assets", [])
        download_url = _pick_asset_for_current_os(assets, release_url)
        return UpdateInfo(
            version=tag_name.lstrip("vV"),
            download_url=download_url,
            release_url=release_url,
            notes=data.get("body", ""),
        )

    return None
