import json
import sys
from typing import Optional, List, Dict, Any

from .api import call_api, call_api_paginated
from .swagger import SwaggerSpec
from .mcp_helpers import HELPERS, WORKFLOWS, run_workflow


def _write_message(obj: Dict[str, Any]) -> None:
    payload = json.dumps(obj).encode("utf-8")
    header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def _read_message() -> Optional[Dict[str, Any]]:
    headers: Dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        decoded = line.decode("ascii", errors="ignore").strip()
        if ":" in decoded:
            key, value = decoded.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    length_raw = headers.get("content-length")
    if not length_raw:
        return None
    length = int(length_raw)
    body = sys.stdin.buffer.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _error(id_value: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_value, "error": {"code": code, "message": message}}


def _ok(id_value: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_value, "result": result}


def _tool_name(tag: str, operation_id: str) -> str:
    return f"{tag}.{operation_id}"


def build_tools(
    spec: SwaggerSpec,
    services: Optional[List[str]] = None,
    include_helpers: bool = False,
    include_workflows: bool = False,
) -> List[Dict[str, Any]]:
    ops_by_tag = spec.operations_by_tag()
    tools: List[Dict[str, Any]] = []

    for tag, ops in ops_by_tag.items():
        if services and tag not in services:
            continue
        for op in ops:
            tools.append(
                {
                    "name": _tool_name(tag, op.operation_id),
                    "description": op.summary or op.description or f"{op.method} {op.path}",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "params": {"type": "object"},
                            "json": {"type": "object"},
                            "pretty": {"type": "boolean"},
                            "pageAll": {"type": "boolean"},
                            "pageLimit": {"type": "integer"},
                            "pageMax": {"type": "integer"},
                            "pageDelay": {"type": "integer"},
                            "dryRun": {"type": "boolean"},
                            "account": {"type": "string"},
                        },
                    },
                }
            )

    if include_helpers:
        for name, meta in HELPERS.items():
            tools.append(
                {
                    "name": name,
                    "description": meta["description"],
                    "inputSchema": meta["inputSchema"],
                }
            )

    if include_workflows:
        for name, meta in WORKFLOWS.items():
            tools.append(
                {
                    "name": name,
                    "description": meta["description"],
                    "inputSchema": meta["inputSchema"],
                }
            )

    tools.sort(key=lambda t: t.get("name", ""))
    return tools


def _handle_initialize(id_value: Any, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    requested = None
    if isinstance(params, dict):
        requested = params.get("protocolVersion")
    protocol_version = requested or "2024-11-05"
    result = {
        "protocolVersion": protocol_version,
        "serverInfo": {"name": "bakufu-cli", "version": "0.1.0"},
        "capabilities": {"tools": {"listChanged": False}},
    }
    return _ok(id_value, result)


def _handle_tools_list(
    id_value: Any,
    spec: SwaggerSpec,
    services: Optional[List[str]],
    include_helpers: bool,
    include_workflows: bool,
) -> Dict[str, Any]:
    tools = build_tools(spec, services, include_helpers, include_workflows)
    return _ok(id_value, {"tools": tools})


def _handle_tools_call(
    id_value: Any,
    spec: SwaggerSpec,
    services: Optional[List[str]],
    include_helpers: bool,
    include_workflows: bool,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    name = params.get("name") if isinstance(params, dict) else None
    if not name:
        return _error(id_value, -32602, "Invalid tool name")

    if include_helpers and name in HELPERS:
        handler = HELPERS[name]["handler"]
        arguments = params.get("arguments", {}) if isinstance(params, dict) else {}
        try:
            result = handler(arguments)
        except Exception as exc:
            return _error(id_value, -32603, str(exc))
        return _ok(id_value, {"content": [{"type": "text", "text": json.dumps(result)}]})

    if include_workflows and name in WORKFLOWS:
        arguments = params.get("arguments", {}) if isinstance(params, dict) else {}
        try:
            result = run_workflow(name, arguments)
        except Exception as exc:
            return _error(id_value, -32603, str(exc))
        return _ok(id_value, {"content": [{"type": "text", "text": json.dumps(result)}]})

    if "." not in name:
        return _error(id_value, -32602, "Invalid tool name")

    tag, operation_id = name.split(".", 1)
    if services and tag not in services:
        return _error(id_value, -32602, f"Service not exposed: {tag}")

    op = spec.find_operation(tag, operation_id)
    if not op:
        return _error(id_value, -32602, f"Operation not found: {name}")

    arguments = params.get("arguments", {}) if isinstance(params, dict) else {}
    call_params = arguments.get("params") or {}
    json_body = arguments.get("json")
    pretty = bool(arguments.get("pretty", False))
    page_all = bool(arguments.get("pageAll", False))
    page_limit = int(arguments.get("pageLimit", 200) or 200)
    page_max = int(arguments.get("pageMax", 10) or 10)
    page_delay = int(arguments.get("pageDelay", 100) or 100)
    dry_run = bool(arguments.get("dryRun", False))
    account = arguments.get("account")

    if page_all:
        pages = call_api_paginated(
            op.path,
            params=call_params,
            limit=page_limit,
            max_pages=page_max,
            page_delay_ms=page_delay,
            method=op.method,
            data=json_body,
            pretty=pretty,
            dry_run=dry_run,
            account=account,
        )
        content = json.dumps(pages)
    else:
        response = call_api(
            op.path,
            method=op.method,
            params=call_params,
            data=json_body,
            pretty=pretty,
            dry_run=dry_run,
            account=account,
        )
        content = json.dumps(response)

    return _ok(id_value, {"content": [{"type": "text", "text": content}]})


def serve(
    services: Optional[List[str]] = None,
    include_helpers: bool = False,
    include_workflows: bool = False,
) -> None:
    spec = SwaggerSpec.load()
    initialized = False
    while True:
        request = _read_message()
        if request is None:
            break
        method = request.get("method")
        id_value = request.get("id")
        is_notification = "id" not in request
        params = request.get("params")

        if method == "initialize":
            initialized = True
            _write_message(_handle_initialize(id_value, params if isinstance(params, dict) else None))
            continue

        if method == "notifications/initialized":
            # MCP notification: no response expected.
            continue

        if method == "ping":
            if not is_notification:
                _write_message(_ok(id_value, {}))
            continue

        if not initialized:
            if not is_notification:
                _write_message(_error(id_value, -32002, "Server not initialized"))
            continue

        if method == "tools/list":
            _write_message(
                _handle_tools_list(id_value, spec, services, include_helpers, include_workflows)
            )
        elif method == "tools/call":
            _write_message(
                _handle_tools_call(
                    id_value,
                    spec,
                    services,
                    include_helpers,
                    include_workflows,
                    params if isinstance(params, dict) else {},
                )
            )
        else:
            if not is_notification:
                _write_message(_error(id_value, -32601, "Method not found"))
