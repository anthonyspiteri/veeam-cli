import json
import os
from pathlib import Path
from typing import Optional

from .accounts import resolve_account, get_account_credentials

DEFAULT_CREDENTIALS_PATH = Path("credentials.json")
TOKEN_DIR = Path(os.getenv("BAKUFU_HOME", Path.home() / ".config" / "bakufu"))
LEGACY_TOKEN_DIR = Path(".bakufu")


def truthy_env(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_credentials(account: Optional[str] = None):
    # Highest priority: explicit env var credentials
    server = os.getenv("BAKUFU_SERVER")
    username = os.getenv("BAKUFU_USER")
    password = os.getenv("BAKUFU_PASS")
    insecure_env = truthy_env(os.getenv("BAKUFU_INSECURE"))
    if server and username and password:
        return {"server": server, "username": username, "password": password, "insecure": insecure_env}

    # If account is specified or defaulted, use accounts.json
    resolved = resolve_account(account)
    if resolved:
        creds = get_account_credentials(resolved)
        if creds:
            merged = dict(creds)
            merged["account"] = resolved
            if "insecure" not in merged:
                merged["insecure"] = insecure_env
            return merged

    # Credentials file override
    credentials_file = os.getenv("BAKUFU_CREDENTIALS_FILE")
    path = Path(credentials_file) if credentials_file else DEFAULT_CREDENTIALS_PATH
    if path.exists():
        data = json.loads(path.read_text())
        return {
            "server": data.get("server"),
            "username": data.get("username"),
            "password": data.get("password"),
            "insecure": bool(data.get("insecure", insecure_env)),
        }

    return {"server": server, "username": username, "password": password, "insecure": insecure_env}


def token_path_for_account(account: Optional[str] = None) -> Path:
    resolved = resolve_account(account)
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)

    if resolved:
        preferred = TOKEN_DIR / f"token.{resolved}.json"
        legacy = LEGACY_TOKEN_DIR / f"token.{resolved}.json"
    else:
        preferred = TOKEN_DIR / "token.json"
        legacy = LEGACY_TOKEN_DIR / "token.json"

    if preferred.exists():
        return preferred
    if legacy.exists():
        return legacy
    return preferred
