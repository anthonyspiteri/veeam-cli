import json
import re
import sys
from typing import Optional, List, Dict, Any

try:
    from importlib.metadata import version as _pkg_version
    _SERVER_VERSION = _pkg_version("bakufu-cli")
except Exception:
    _SERVER_VERSION = "0.0.0"

from .api import call_api, call_api_paginated
from .swagger import SwaggerSpec, Operation
from .mcp_helpers import HELPERS, WORKFLOWS, run_workflow

PROTOCOL_VERSION = "2025-03-26"


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
    """JSON-RPC protocol-level error (for malformed requests, unknown methods, etc.)."""
    return {"jsonrpc": "2.0", "id": id_value, "error": {"code": code, "message": message}}


def _ok(id_value: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_value, "result": result}


def _tool_result(id_value: Any, text: str, is_error: bool = False) -> Dict[str, Any]:
    """Successful JSON-RPC response wrapping a tool call result.

    Per the MCP spec, tool execution errors must be returned as successful
    JSON-RPC responses with isError=True so the LLM can see and recover from
    them — NOT as JSON-RPC protocol-level errors.
    """
    result: Dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["isError"] = True
    return _ok(id_value, result)


def _sanitize(s: str) -> str:
    """Replace any character outside [a-zA-Z0-9_-] with an underscore."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", s)


_MAX_TOOL_NAME_LENGTH = 64


def _tool_name(tag: str, operation_id: str) -> str:
    # Use __ as the separator so we can unambiguously split even when the
    # sanitized tag contains underscores (e.g. "Active_Directory_Domains").
    name = f"{_sanitize(tag)}__{operation_id}"
    if len(name) > _MAX_TOOL_NAME_LENGTH:
        # Truncate the tag portion to fit; the operation_id is the unique part.
        suffix = f"__{operation_id}"
        max_tag_len = _MAX_TOOL_NAME_LENGTH - len(suffix)
        if max_tag_len < 1:
            # Operation ID alone exceeds limit — truncate the whole name.
            name = name[:_MAX_TOOL_NAME_LENGTH]
        else:
            name = f"{_sanitize(tag)[:max_tag_len]}{suffix}"
    return name


def _build_swagger_input_schema(op: Operation) -> Dict[str, Any]:
    """Build a rich inputSchema for a Swagger operation, surfacing actual query params."""
    query_props: Dict[str, Any] = {}
    required_params: List[str] = []

    for param in op.parameters:
        if not isinstance(param, dict):
            continue
        if param.get("in") != "query":
            continue
        name = param.get("name")
        if not name:
            continue
        schema = param.get("schema") or {}
        prop: Dict[str, Any] = {"type": schema.get("type", "string")}
        desc = param.get("description")
        if desc:
            prop["description"] = desc
        if "enum" in schema:
            prop["enum"] = schema["enum"]
        if "default" in schema:
            prop["default"] = schema["default"]
        query_props[name] = prop
        if param.get("required"):
            required_params.append(name)

    params_schema: Dict[str, Any] = {
        "type": "object",
        "description": "Query parameters for the API call",
    }
    if query_props:
        params_schema["properties"] = query_props
    if required_params:
        params_schema["required"] = required_params

    has_body = op.request_body is not None
    json_desc = "Request body (required for POST/PUT/PATCH)" if has_body else "Request body (not used by this operation)"

    return {
        "type": "object",
        "properties": {
            "params": params_schema,
            "json": {"type": "object", "description": json_desc},
            "pretty": {"type": "boolean", "description": "Pretty-print JSON output"},
            "pageAll": {"type": "boolean", "description": "Fetch all pages automatically (NDJSON output)"},
            "pageLimit": {"type": "integer", "description": "Items per page when paginating (default 200)"},
            "pageMax": {"type": "integer", "description": "Maximum pages to fetch (default 10)"},
            "pageDelay": {"type": "integer", "description": "Delay between page requests in ms (default 100)"},
            "dryRun": {"type": "boolean", "description": "Preview the request without executing it"},
            "account": {"type": "string", "description": "Named account to use for authentication"},
        },
    }


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
                    "inputSchema": _build_swagger_input_schema(op),
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
    # Always respond with the version this server implements, regardless of what
    # the client requests.  The client is responsible for disconnecting if it
    # cannot handle our version.
    result = {
        "protocolVersion": PROTOCOL_VERSION,
        "serverInfo": {"name": "bakufu-cli", "version": _SERVER_VERSION},
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

    arguments = params.get("arguments", {}) if isinstance(params, dict) else {}

    if include_helpers and name in HELPERS:
        handler = HELPERS[name]["handler"]
        try:
            result = handler(arguments)
        except Exception as exc:
            return _tool_result(id_value, str(exc), is_error=True)
        return _tool_result(id_value, json.dumps(result))

    if include_workflows and name in WORKFLOWS:
        try:
            result = run_workflow(name, arguments)
        except Exception as exc:
            return _tool_result(id_value, str(exc), is_error=True)
        return _tool_result(id_value, json.dumps(result))

    if "__" not in name:
        return _error(id_value, -32602, f"Unknown tool: {name}")

    sanitized_tag, operation_id = name.split("__", 1)

    # Reverse-lookup the original tag name from the sanitized form.
    op = None
    for tag, ops in spec.operations_by_tag().items():
        if _sanitize(tag) != sanitized_tag:
            continue
        if services and tag not in services:
            return _error(id_value, -32602, f"Service not exposed: {tag}")
        op = next((o for o in ops if o.operation_id == operation_id), None)
        break

    if not op:
        return _error(id_value, -32602, f"Operation not found: {name}")

    call_params = arguments.get("params") or {}
    json_body = arguments.get("json")
    pretty = bool(arguments.get("pretty", False))
    page_all = bool(arguments.get("pageAll", False))
    page_limit = int(arguments.get("pageLimit", 200) or 200)
    page_max = int(arguments.get("pageMax", 10) or 10)
    page_delay = int(arguments.get("pageDelay", 100) or 100)
    dry_run = bool(arguments.get("dryRun", False))
    account = arguments.get("account")

    try:
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
    except Exception as exc:
        return _tool_result(id_value, str(exc), is_error=True)

    return _tool_result(id_value, content)


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
            # Client confirms it is ready — no response expected for notifications.
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
