import json
import subprocess
import urllib.parse
from urllib.parse import urljoin

from .accounts import add_account


def _curl_json(url: str, insecure: bool = False):
    cmd = ["curl", "-sS", "-w", "\\n%{http_code}", url]
    if insecure:
        cmd.insert(1, "-k")
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


def _curl_token(server: str, username: str, password: str, insecure: bool = False):
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
        f"{server.rstrip('/')}/api/oauth2/token",
        "-H",
        "Content-Type: application/x-www-form-urlencoded",
        "--data-binary",
        "@-",
    ]
    if insecure:
        cmd.insert(1, "-k")
    result = subprocess.run(cmd, input=form_payload, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to obtain token")
    return json.loads(result.stdout)


def setup(
    server: str,
    username: str,
    password: str,
    account_name: str,
    make_default: bool = False,
    insecure: bool = False,
):
    server = server.rstrip("/")

    # Validate API is reachable (serverInfo + swagger)
    server_info = _curl_json(urljoin(server + "/", "api/v1/serverInfo"), insecure=insecure)
    swagger = _curl_json(urljoin(server + "/", "swagger/v1.3-rev0/swagger.json"), insecure=insecure)

    if not swagger.get("json"):
        raise RuntimeError(f"Unable to fetch swagger spec (HTTP {swagger.get('status')})")

    # /api/v1/serverInfo may require auth; treat 200 or 401/403 as reachable
    if server_info.get("status") not in {"200", "401", "403"}:
        raise RuntimeError(f"Unable to fetch /api/v1/serverInfo (HTTP {server_info.get('status')})")

    # Validate credentials
    token_data = _curl_token(server, username, password, insecure=insecure)

    # Store account
    add_account(account_name, server, username, password, make_default=make_default, insecure=insecure)

    return {
        "server": server,
        "serverInfo": server_info.get("json"),
        "swaggerVersion": swagger.get("json", {}).get("info", {}).get("version"),
        "tokenExpiresIn": token_data.get("expires_in"),
    }
