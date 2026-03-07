import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

BAKUFU_HOME = Path(os.getenv("BAKUFU_HOME", Path.home() / ".config" / "bakufu"))
ACCOUNTS_PATH = BAKUFU_HOME / "accounts.json"
LEGACY_ACCOUNTS_PATH = Path(".bakufu") / "accounts.json"
KEYRING_SERVICE = "bakufu-cli"


def _load_raw() -> Dict[str, Any]:
    if ACCOUNTS_PATH.exists():
        return json.loads(ACCOUNTS_PATH.read_text())
    if LEGACY_ACCOUNTS_PATH.exists():
        return json.loads(LEGACY_ACCOUNTS_PATH.read_text())
    return {"default": None, "accounts": {}}


def _save_raw(data: Dict[str, Any]) -> None:
    ACCOUNTS_PATH.parent.mkdir(exist_ok=True)
    ACCOUNTS_PATH.write_text(json.dumps(data, indent=2))


def list_accounts() -> Dict[str, Any]:
    data = _load_raw()
    sanitized = {"default": data.get("default"), "accounts": {}}
    for name, account in data.get("accounts", {}).items():
        if not isinstance(account, dict):
            continue
        sanitized["accounts"][name] = {
            "server": account.get("server"),
            "username": account.get("username"),
            "passwordStored": bool(account.get("passwordStored", False) or account.get("password")),
        }
    return sanitized


def _password_key(name: str) -> str:
    return f"account:{name}:password"


def _get_keyring():
    try:
        import keyring  # type: ignore
    except Exception as exc:
        raise ValueError(
            "Missing dependency 'keyring'. Run `python -m pip install -e .` to install runtime dependencies."
        ) from exc
    return keyring


def _set_password(name: str, password: str) -> None:
    keyring = _get_keyring()
    keyring.set_password(KEYRING_SERVICE, _password_key(name), password)


def _get_password(name: str) -> Optional[str]:
    keyring = _get_keyring()
    return keyring.get_password(KEYRING_SERVICE, _password_key(name))


def add_account(name: str, server: str, username: str, password: str, make_default: bool = False) -> None:
    data = _load_raw()
    data.setdefault("accounts", {})
    data["accounts"][name] = {
        "server": server,
        "username": username,
        "passwordStored": True,
    }
    _set_password(name, password)
    if make_default or not data.get("default"):
        data["default"] = name
    _save_raw(data)


def set_default(name: str) -> None:
    data = _load_raw()
    if name not in data.get("accounts", {}):
        raise ValueError(f"Account not found: {name}")
    data["default"] = name
    _save_raw(data)


def resolve_account(explicit: Optional[str] = None) -> Optional[str]:
    if explicit:
        return explicit
    env = os.getenv("BAKUFU_ACCOUNT")
    if env:
        return env
    data = _load_raw()
    return data.get("default")


def get_account_credentials(name: str) -> Optional[Dict[str, str]]:
    data = _load_raw()
    account = data.get("accounts", {}).get(name)
    if not account:
        return None
    password = _get_password(name) or account.get("password")
    if not password:
        raise ValueError(
            f"Password not found in keyring for account '{name}'. Re-run `bakufu auth login {name}`."
        )
    return {
        "server": account.get("server"),
        "username": account.get("username"),
        "password": password,
    }
