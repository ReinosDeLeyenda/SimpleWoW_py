from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes as wintypes
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

APP_NAME = "SimpleWoWChat"
CONFIG_DIR = Path.home() / ".simplewow"
ACCOUNTS_FILE = CONFIG_DIR / "accounts.json"


# ==============================================================================
# CIFRADO NATIVO WINDOWS (DPAPI - CryptProtectData / CryptUnprotectData)
# ==============================================================================
class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi_encrypt(plaintext: str) -> str:
    data = plaintext.encode("utf-8")
    blob_in = _DATA_BLOB(len(data), ctypes.create_string_buffer(data, len(data)))
    blob_out = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    if not crypt32.CryptProtectData(
        ctypes.byref(blob_in),
        "SimpleWoW Account",
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    ):
        raise OSError("Error al cifrar contraseña con Windows DPAPI.")

    try:
        encrypted_bytes = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        return base64.b64encode(encrypted_bytes).decode("ascii")
    finally:
        kernel32.LocalFree(blob_out.pbData)


def _dpapi_decrypt(ciphertext_b64: str) -> str:
    raw = base64.b64decode(ciphertext_b64.encode("ascii"))
    blob_in = _DATA_BLOB(len(raw), ctypes.create_string_buffer(raw, len(raw)))
    blob_out = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    if not crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    ):
        raise OSError("Error al descifrar contraseña con Windows DPAPI.")

    try:
        decrypted_bytes = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        return decrypted_bytes.decode("utf-8")
    finally:
        kernel32.LocalFree(blob_out.pbData)


# ==============================================================================
# GESTOR MULTIPLATAFORMA DE CUENTAS
# ==============================================================================
class AccountManager:
    """Guarda cuentas cifrando contraseñas con DPAPI (Windows) o Keychain/SecretService (Linux/macOS/Android)."""

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._accounts: Dict[str, dict] = self._load_metadata()

    def _load_metadata(self) -> Dict[str, dict]:
        if not ACCOUNTS_FILE.exists():
            return {}
        try:
            return json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_metadata(self) -> None:
        ACCOUNTS_FILE.write_text(json.dumps(self._accounts, indent=2), encoding="utf-8")
        if os.name != "nt":
            try:
                os.chmod(ACCOUNTS_FILE, 0o600)
            except OSError:
                pass

    def list_accounts(self) -> List[dict]:
        """Devuelve la lista de cuentas guardadas (sin contraseñas en claro)."""
        return list(self._accounts.values())

    def save_account(self, host: str, port: int, username: str, password: str) -> None:
        key = f"{username.lower()}@{host.lower()}:{port}"
        entry = {
            "id": key,
            "host": host,
            "port": port,
            "username": username,
            "backend": "none",
            "secret": "",
        }

        if sys.platform == "win32":
            entry["backend"] = "dpapi"
            entry["secret"] = _dpapi_encrypt(password)
        else:
            # Linux (SecretService/KWallet), macOS (Keychain), etc.
            try:
                import keyring

                keyring.set_password(APP_NAME, key, password)
                entry["backend"] = "keyring"
            except Exception:
                # Fallback obfuscado en sistemas headless / Android sin daemon keyring
                entry["backend"] = "obfuscated"
                entry["secret"] = base64.b64encode(password.encode("utf-8")).decode("ascii")

        self._accounts[key] = entry
        self._save_metadata()

    def get_password(self, account_id: str) -> Optional[str]:
        entry = self._accounts.get(account_id)
        if not entry:
            return None

        backend = entry.get("backend")
        try:
            if backend == "dpapi" and sys.platform == "win32":
                return _dpapi_decrypt(entry["secret"])
            elif backend == "keyring":
                import keyring

                return keyring.get_password(APP_NAME, account_id)
            elif backend == "obfuscated":
                return base64.b64decode(entry["secret"].encode("ascii")).decode("utf-8")
        except Exception:
            return None
        return None

    def delete_account(self, account_id: str) -> None:
        entry = self._accounts.pop(account_id, None)
        if not entry:
            return
        if entry.get("backend") == "keyring":
            try:
                import keyring

                keyring.delete_password(APP_NAME, account_id)
            except Exception:
                pass
        self._save_metadata()
