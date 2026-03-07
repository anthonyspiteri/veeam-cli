import json
import subprocess
from urllib.parse import urljoin

from .accounts import add_account


def _curl_json(url: str):
    cmd = ["curl", "-k", "-sS", "-w", "\\n%{http_code}", url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "curl failed")
    if "\n" in result.stdout:
        body, status = result.stdout.rsplit("\n", 1)
    else:
        body, status = result.stdout, ""
    parsed = None
    if body:
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = None
    return {"status": status, "body": body, "json": parsed}


def _curl_token(server: str, username: str, password: str):
    cmd = [
        "curl",
        "-k",
        "-s",
        "--fail",
        "-X",
        "POST",
        f"{server.rstrip('/')}/api/oauth2/token",
        "-H",
        "Content-Type: application/x-www-form-urlencoded",
        "-d",
        "grant_type=password",
        "-d",
        f"username={username}",
        "-d",
        f"password={password}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to obtain token")
    return json.loads(result.stdout)


def setup(server: str, username: str, password: str, account_name: str, make_default: bool = False):
    server = server.rstrip("/")

    # Validate API is reachable (serverInfo + swagger)
    server_info = _curl_json(urljoin(server + "/", "api/v1/serverInfo"))
    swagger = _curl_json(urljoin(server + "/", "swagger/v1.3-rev0/swagger.json"))

    if not swagger.get("json"):
        raise RuntimeError(f"Unable to fetch swagger spec (HTTP {swagger.get('status')})")

    # /api/v1/serverInfo may require auth; treat 200 or 401/403 as reachable
    if server_info.get("status") not in {"200", "401", "403"}:
        raise RuntimeError(f"Unable to fetch /api/v1/serverInfo (HTTP {server_info.get('status')})")

    # Validate credentials
    token_data = _curl_token(server, username, password)

    # Store account
    add_account(account_name, server, username, password, make_default=make_default)

    return {
        "server": server,
        "serverInfo": server_info.get("json"),
        "swaggerVersion": swagger.get("json", {}).get("info", {}).get("version"),
        "tokenExpiresIn": token_data.get("expires_in"),
    }
