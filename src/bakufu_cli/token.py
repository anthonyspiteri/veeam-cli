import json
import os
from datetime import datetime, timezone
import subprocess
import urllib.parse
from typing import Optional

from .config import load_credentials, token_path_for_account

TOKEN_SAFETY_SECONDS = 60


def _is_truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _parse_expires(value: str):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _token_is_valid(data: dict) -> bool:
    if not data:
        return False
    token = data.get("access_token")
    expires_raw = data.get(".expires") or data.get("expires_at")
    if not token or not expires_raw:
        return False
    expires_at = _parse_expires(expires_raw)
    if not expires_at:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    now = datetime.now(expires_at.tzinfo or timezone.utc)
    return (expires_at - now).total_seconds() > TOKEN_SAFETY_SECONDS


def load_cached_token(account: Optional[str] = None) -> dict:
    token_path = token_path_for_account(account)
    if not token_path.exists():
        return {}
    try:
        return json.loads(token_path.read_text())
    except json.JSONDecodeError:
        return {}


def request_token(account: Optional[str] = None) -> dict:
    creds = load_credentials(account)
    server = (creds.get("server") or "").rstrip("/")
    username = creds.get("username")
    password = creds.get("password")

    if not server or not username or not password:
        raise RuntimeError("Missing credentials. Set BAKUFU_SERVER/USER/PASS or credentials.json")

    insecure = _is_truthy(creds.get("insecure")) or _is_truthy(os.getenv("BAKUFU_INSECURE"))
    form_payload = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "username": username,
            "password": password,
        }
    )

    cmd = [
        "curl",
        "-s",
        "--show-error",
        "--fail",
        "-X",
        "POST",
        f"{server}/api/oauth2/token",
        "-H",
        "Content-Type: application/x-www-form-urlencoded",
        "--data-binary",
        "@-",
    ]
    if insecure:
        cmd.insert(1, "-k")

    result = subprocess.run(cmd, input=form_payload, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Failed to obtain token"
        raise RuntimeError(detail)

    data = json.loads(result.stdout)
    token_path = token_path_for_account(account)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(token_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    return data


def ensure_token(force_refresh: bool = False, account: Optional[str] = None) -> dict:
    if force_refresh:
        return request_token(account)
    cached = load_cached_token(account)
    if _token_is_valid(cached):
        return cached
    return request_token(account)


def get_access_token(force_refresh: bool = False, account: Optional[str] = None) -> str:
    env_token = os.getenv("BAKUFU_TOKEN")
    if env_token:
        return env_token
    token_data = ensure_token(force_refresh=force_refresh, account=account)
    token = token_data.get("access_token")
    if not token:
        raise RuntimeError("Token response missing access_token")
    return token
