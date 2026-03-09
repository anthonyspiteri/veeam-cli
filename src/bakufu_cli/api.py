import json
import os
import tempfile
import urllib.parse
import subprocess
from typing import Any, Optional, Dict

from .config import load_credentials
from .token import get_access_token


def _is_truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _redact_cmd(cmd: list[str]) -> list[str]:
    redacted = []
    for part in cmd:
        if part.lower().startswith("authorization: bearer "):
            redacted.append("Authorization: Bearer ***")
        else:
            redacted.append(part)
    return redacted


def _encode_query(params: dict[str, Any]) -> str:
    return urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)


def _substitute_path(path: str, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    remaining = dict(params)
    for key in list(params.keys()):
        token = "{" + key + "}"
        if token in path:
            path = path.replace(token, str(params[key]))
            remaining.pop(key, None)
    return path, remaining


def _curl_request(
    url: str,
    method: str,
    token: str,
    data: Optional[str],
    dry_run: bool = False,
    insecure: bool = False,
):
    header_fd, header_path = tempfile.mkstemp(prefix="bakufu_headers_")
    try:
        cmd = ["curl", "-sS", "-D", header_path, "-X", method, "-H", f"Authorization: Bearer {token}"]
        if insecure:
            cmd.insert(1, "-k")
        if data is not None:
            cmd += ["-H", "Content-Type: application/json", "-d", data]
        cmd.append(url)

        if dry_run:
            return {"cmd": _redact_cmd(cmd), "status": None, "headers": {}, "body": ""}

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "curl failed")

        body = result.stdout
        with open(header_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_headers = f.read().splitlines()
        headers = {}
        status = None
        for line in raw_headers:
            if line.lower().startswith("http/"):
                parts = line.split()
                if len(parts) >= 2:
                    status = parts[1]
            elif ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        return {"cmd": cmd, "status": status, "headers": headers, "body": body}
    finally:
        try:
            os.close(header_fd)
            os.unlink(header_path)
        except OSError:
            pass


def call_api(
    path: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    pretty: bool = False,
    refresh: bool = False,
    dry_run: bool = False,
    account: Optional[str] = None,
):
    creds = load_credentials(account)
    server = (creds.get("server") or "").rstrip("/")
    if not server:
        raise RuntimeError("Missing server. Set BAKUFU_SERVER or credentials.json")

    if not path.startswith("/"):
        path = "/" + path

    params = params or {}
    path, query_params = _substitute_path(path, params)
    query = _encode_query(query_params)
    url = f"{server}{path}" + (f"?{query}" if query else "")

    token = get_access_token(force_refresh=refresh, account=account)
    payload = json.dumps(data) if data is not None else None
    insecure = _is_truthy(creds.get("insecure")) or _is_truthy(os.getenv("BAKUFU_INSECURE"))

    response = _curl_request(
        url,
        method=method,
        token=token,
        data=payload,
        dry_run=dry_run,
        insecure=insecure,
    )

    if dry_run:
        return response

    body = response["body"]
    if pretty:
        try:
            body_json = json.loads(body) if body else None
            body = json.dumps(body_json, indent=2) if body_json is not None else ""
        except json.JSONDecodeError:
            pass

    return {
        "status": response["status"],
        "headers": response["headers"],
        "body": body,
    }


def call_api_paginated(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    limit: int = 200,
    max_pages: int = 10,
    page_delay_ms: int = 100,
    **kwargs,
):
    import time

    params = dict(params or {})
    results = []
    skip = params.get("skip", 0)
    pages = 0

    while pages < max_pages:
        params["skip"] = skip
        params["limit"] = limit
        response = call_api(path, params=params, **kwargs)
        if isinstance(response, dict) and response.get("body"):
            try:
                data = json.loads(response["body"])
            except json.JSONDecodeError:
                return results
            results.append(data)
            pagination = data.get("pagination", {}) if isinstance(data, dict) else {}
            total = pagination.get("total")
            count = pagination.get("count")
            if not isinstance(total, int) or not isinstance(count, int):
                break
            skip += count
            pages += 1
            if skip >= total:
                break
            time.sleep(page_delay_ms / 1000.0)
        else:
            break
    return results
