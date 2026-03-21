import argparse
import base64
import difflib
import importlib.metadata
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .api import call_api, call_api_paginated
from .token import ensure_token
from .swagger import SwaggerSpec
from .accounts import add_account, list_accounts, set_default
from .mcp_server import serve
from .mcp_helpers import run_workflow, run_helper, WORKFLOWS, HELPERS
from .auth_setup import setup as auth_setup

# When running as a PyInstaller frozen binary, bundled data files live under
# sys._MEIPASS (the extraction dir).  In a normal source/venv install they
# live two levels above this package file (the repo / installed root).
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _DATA_ROOT = Path(sys._MEIPASS)
else:
    _DATA_ROOT = Path(__file__).resolve().parents[2]

DOCS_SKILLS_PATH = _DATA_ROOT / "docs" / "skills.md"


class CliError(Exception):
    def __init__(self, code: str, message: str, hint: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.details = details or {}


class BakufuArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        hint = None
        bad_choice = re.search(r"invalid choice: '([^']+)'", message)
        if bad_choice:
            token = bad_choice.group(1)
            choices_match = re.search(r"\(choose from ([^)]+)\)", message)
            if choices_match:
                raw_choices = [c.strip().strip("'") for c in choices_match.group(1).split(",")]
                suggestion = difflib.get_close_matches(token, raw_choices, n=1)
                if suggestion:
                    hint = f"Did you mean `{suggestion[0]}`?"
        if "argument services_cmd" in message:
            hint = "Use `bakufu services list` or run an operation with `bakufu run <Tag> <OperationId>`."
        raise CliError("CLI_USAGE_ERROR", message, hint=hint)


def _parse_json_arg(value: Optional[str]):
    if value is None:
        return None
    if value.startswith("@"):
        payload = Path(value[1:]).read_text()
        return json.loads(payload)
    return json.loads(value)


def cmd_auth_token(args):
    from .token import load_cached_token, _token_is_valid, _parse_expires
    from datetime import datetime, timezone

    if args.refresh:
        try:
            data = ensure_token(force_refresh=True, account=args.account)
        except Exception as exc:
            raise CliError(
                "AUTH_TOKEN_FAILED",
                str(exc),
                hint="Run `bakufu auth setup <account>` and verify network/DNS.",
            )
    else:
        data = load_cached_token(account=args.account)

    if not data:
        raise CliError(
            "AUTH_TOKEN_MISSING",
            "No token found for this account.",
            hint="Run `bakufu auth token --refresh` to obtain a token.",
        )

    valid = _token_is_valid(data)
    expires_raw = data.get(".expires") or data.get("expires_at") or ""
    expires_at = _parse_expires(expires_raw) if expires_raw else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    status = "valid" if valid else "expired"
    rows = [
        ["Status", status],
        ["Account", args.account or "(default)"],
    ]
    if expires_at:
        now = datetime.now(timezone.utc)
        remaining = expires_at - now
        total_sec = int(remaining.total_seconds())
        if total_sec > 0:
            hours, rem = divmod(total_sec, 3600)
            mins = rem // 60
            rows.append(["Expires", expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")])
            rows.append(["Remaining", f"{hours}h {mins}m"])
        else:
            rows.append(["Expires", expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")])
            rows.append(["Remaining", "expired"])

    if getattr(args, "show", False):
        rows.append(["Token", data.get("access_token", "")])

    col_width = max(len(r[0]) for r in rows)
    for label, value in rows:
        print(f"{label:<{col_width}}  {value}")


def cmd_auth_login(args):
    server = args.server
    username = args.username
    password = args.password
    if password:
        print("Warning: passing --password on the command line exposes it in shell history and process lists. Omit it to use the secure interactive prompt.", file=sys.stderr)
    if not server:
        server = input("Server URL: ").strip()
    if not username:
        username = input("Username: ").strip()
    if not password:
        import getpass

        password = getpass.getpass("Password: ")
    if not server or not username or not password:
        raise CliError("AUTH_INPUT_INVALID", "Missing server/username/password")
    add_account(
        args.account_name,
        server,
        username,
        password,
        make_default=args.default,
        insecure=bool(args.insecure) or os.environ.get("BAKUFU_INSECURE", "").lower() in ("1", "true", "yes", "on"),
    )
    print("OK")


def cmd_auth_setup(args):
    server = args.server
    username = args.username
    password = args.password
    if password:
        print("Warning: passing --password on the command line exposes it in shell history and process lists. Omit it to use the secure interactive prompt.", file=sys.stderr)
    if not server:
        server = input("Server URL: ").strip()
    if not username:
        username = input("Username: ").strip()
    if not password:
        import getpass

        password = getpass.getpass("Password: ")
    if not server or not username or not password:
        raise CliError("AUTH_INPUT_INVALID", "Missing server/username/password")
    insecure = bool(args.insecure) or os.environ.get("BAKUFU_INSECURE", "").lower() in ("1", "true", "yes", "on")
    result = auth_setup(
        server,
        username,
        password,
        args.account_name,
        make_default=args.default,
        insecure=insecure,
    )
    server = result.get("server") or ""
    default_flag = " (default)" if args.default else ""
    swagger_ver = result.get("swaggerVersion") or "unknown"
    token_expiry = result.get("tokenExpiresIn")
    print(f"Account '{args.account_name}' saved{default_flag}")
    print(f"  Server   : {server}")
    print(f"  Swagger  : {swagger_ver}")
    if token_expiry:
        print(f"  Token    : expires in {token_expiry}s")


def cmd_auth_list(_args):
    from .token import load_cached_token, _token_is_valid
    data = list_accounts()
    default_account = data.get("default")
    accounts = data.get("accounts", {})
    if not accounts:
        print("No accounts configured. Run `bakufu auth setup <name>` to add one.")
        return
    headers = ["ACCOUNT", "SERVER", "USERNAME", "PASSWORD", "INSECURE", "TOKEN", "DEFAULT"]
    rows = []
    for name, info in accounts.items():
        token_data = load_cached_token(account=name)
        if not token_data:
            token_status = "none"
        elif _token_is_valid(token_data):
            token_status = "valid"
        else:
            token_status = "expired"
        rows.append([
            name,
            info.get("server") or "",
            info.get("username") or "",
            "stored" if info.get("passwordStored") else "missing",
            "yes" if info.get("insecure") else "no",
            token_status,
            "*" if name == default_account else "",
        ])
    col_widths = [max(len(str(r[i])) for r in ([headers] + rows)) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in col_widths))
    for row in rows:
        print(fmt.format(*row))


def cmd_auth_default(args):
    set_default(args.account_name)
    print("OK")


def cmd_call(args):
    params = _parse_json_arg(args.params) or {}
    data = _parse_json_arg(args.body)
    response = call_api(
        args.path,
        method=args.method,
        params=params,
        data=data,
        pretty=False,
        refresh=args.refresh,
        dry_run=args.dry_run,
        account=args.account,
    )
    _print_response(response, args)


def cmd_services_list(_args):
    spec = SwaggerSpec.load()
    for tag in spec.list_tags():
        print(tag)


def cmd_operations_list(args):
    spec = SwaggerSpec.load()
    if args.tag:
        ops = spec.operations_by_tag().get(args.tag, [])
    else:
        ops = spec.iter_operations()
    for op in ops:
        print(f"{op.tags[0] if op.tags else 'untagged'}\t{op.operation_id}\t{op.method}\t{op.path}")


def cmd_run(args):
    spec = SwaggerSpec.load()
    canonical_tag = next((t for t in spec.list_tags() if t.lower() == args.tag.lower()), None)
    if not canonical_tag:
        close_tags = difflib.get_close_matches(args.tag, spec.list_tags(), n=3, cutoff=0.5)
        hint = "Run `bakufu services list` to view available tags."
        if close_tags:
            hint = f"Did you mean tag `{close_tags[0]}`?"
        raise CliError("TAG_NOT_FOUND", f"Tag not found: {args.tag}", hint=hint, details={"suggestions": close_tags})

    op = spec.find_operation(canonical_tag, args.operation_id)
    if not op:
        tag_ops = [o.operation_id for o in spec.operations_by_tag().get(canonical_tag, [])]
        close_ops = difflib.get_close_matches(args.operation_id, tag_ops, n=5, cutoff=0.5)
        hint = f"Run `bakufu operations --tag \"{canonical_tag}\"` to list operations."
        if close_ops:
            hint = f"Did you mean `bakufu run {canonical_tag} {close_ops[0]}`?"
        raise CliError(
            "OPERATION_NOT_FOUND",
            f"Operation not found: {canonical_tag} {args.operation_id}",
            hint=hint,
            details={"tag": canonical_tag, "suggestions": close_ops},
        )

    params = _parse_json_arg(args.params) or {}
    data = _parse_json_arg(args.body)

    if args.page_all:
        pages = call_api_paginated(
            op.path,
            params=params,
            limit=args.page_limit,
            max_pages=args.page_max,
            page_delay_ms=args.page_delay,
            method=op.method,
            data=data,
            pretty=False,
            refresh=args.refresh,
            dry_run=args.dry_run,
            account=args.account,
        )
        if args.dry_run:
            print(json.dumps(pages, indent=2))
            return
        output = getattr(args, "output", "table")
        if output == "raw":
            for page in pages:
                print(json.dumps(page, separators=(",", ":")))
            return
        if output == "json":
            print(json.dumps(pages, indent=2))
            return

        # Default table mode: merge known list payloads across pages, then render once.
        merged_rows = []
        for page in pages:
            if isinstance(page, dict):
                extracted = False
                for field in ("data", "items", "records", "workloads", "tenantResources"):
                    candidate = page.get(field)
                    if isinstance(candidate, list) and candidate and all(isinstance(item, dict) for item in candidate):
                        merged_rows.extend(candidate)
                        extracted = True
                        break
                if extracted:
                    continue
                for value in page.values():
                    if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                        merged_rows.extend(value)
                        extracted = True
                        break
                if not extracted:
                    merged_rows.append(page)
            elif isinstance(page, list) and all(isinstance(item, dict) for item in page):
                merged_rows.extend(page)

        if merged_rows:
            rendered = _render_table({"data": merged_rows})
            if rendered:
                print(rendered)
                return
        print(json.dumps(pages, indent=2))
        return

    response = call_api(
        op.path,
        method=op.method,
        params=params,
        data=data,
        pretty=False,
        refresh=args.refresh,
        dry_run=args.dry_run,
        account=args.account,
    )
    _print_response(response, args)


def cmd_schema(args):
    spec = SwaggerSpec.load()
    op = spec.find_operation_by_id(args.operation_id)
    if not op:
        raise CliError("SCHEMA_OPERATION_NOT_FOUND", f"Operation not found: {args.operation_id}")

    result = {
        "operationId": op.operation_id,
        "method": op.method,
        "path": op.path,
        "summary": op.summary,
        "parameters": op.parameters,
        "requestBody": op.request_body,
        "responses": op.responses,
    }
    output = getattr(args, "output", "table")
    if output == "raw":
        print(json.dumps(result, separators=(",", ":")))
        return
    if output == "json":
        print(json.dumps(result, indent=2))
        return

    summary = _render_object(
        {
            "operationId": result["operationId"],
            "method": result["method"],
            "path": result["path"],
            "summary": result["summary"] or "",
        }
    )
    if summary:
        print(summary)

    parameters = result.get("parameters") or []
    if parameters:
        print("\nparameters")
        rendered_params = _render_table(parameters)
        if rendered_params:
            print(rendered_params)
        else:
            print(json.dumps(parameters, indent=2))

    request_body = result.get("requestBody")
    if request_body:
        print("\nrequestBody")
        rendered_body = _render_object(request_body) if isinstance(request_body, dict) else None
        if rendered_body:
            print(rendered_body)
        else:
            print(json.dumps(request_body, indent=2))

    responses = result.get("responses")
    if responses:
        print("\nresponses")
        rendered_responses = _render_object(responses) if isinstance(responses, dict) else None
        if rendered_responses:
            print(rendered_responses)
        else:
            print(json.dumps(responses, indent=2))


def cmd_jobs_list(args):
    response = call_api("/api/v1/jobs", pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    if getattr(args, "filter", None):
        body = json.loads(response.get("body") or "{}")
        response = dict(response, body=json.dumps(_apply_filter(body, args.filter)))
    _print_response(response, args)


def cmd_jobs_start(args):
    path = f"/api/v1/jobs/{args.job_id}/start"
    response = call_api(path, method="POST", data={}, pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_sessions_show(args):
    path = f"/api/v1/sessions/{args.session_id}"
    response = call_api(path, pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_sessions_logs(args):
    path = f"/api/v1/sessions/{args.session_id}/logs"
    response = call_api(path, pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_license_show(args):
    response = call_api("/api/v1/license", pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_license_install_file(args):
    lic_path = Path(args.license_file).expanduser()
    if not lic_path.exists():
        raise CliError("LICENSE_FILE_NOT_FOUND", f"License file not found: {lic_path}")
    if not lic_path.is_file():
        raise CliError("LICENSE_FILE_INVALID", f"License path is not a file: {lic_path}")
    raw = lic_path.read_bytes()
    # Some downloaded .lic files include UTF-8 BOM; VBR may reject it on XML parse.
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    payload: Dict[str, Any] = {
        "license": base64.b64encode(raw).decode("ascii")
    }
    if args.force_standalone_mode:
        payload["forceStandaloneMode"] = True
    response = call_api(
        "/api/v1/license/install",
        method="POST",
        data=payload,
        pretty=False,
        refresh=args.refresh,
        dry_run=args.dry_run,
        account=args.account,
    )
    _print_response(response, args)


def _apply_filter(data: Any, filter_expr: Optional[str]) -> Any:
    """Apply a simple key=value or key~=substring filter to a list of dicts."""
    if not filter_expr:
        return data
    rows = None
    if isinstance(data, dict):
        for field in ("data", "items", "records"):
            if isinstance(data.get(field), list):
                rows = data[field]
                wrapper_key = field
                break
    elif isinstance(data, list):
        rows = data
        wrapper_key = None
    if rows is None:
        return data
    filtered = []
    for expr in filter_expr.split(","):
        expr = expr.strip()
        if "~=" in expr:
            key, val = expr.split("~=", 1)
            filtered = [r for r in rows if val.lower() in str(r.get(key.strip(), "")).lower()]
        elif "=" in expr:
            key, val = expr.split("=", 1)
            filtered = [r for r in rows if str(r.get(key.strip(), "")).lower() == val.lower()]
        else:
            filtered = rows
        rows = filtered
    if isinstance(data, dict) and wrapper_key:
        result = dict(data)
        result[wrapper_key] = filtered
        return result
    return filtered


def cmd_repos_list(args):
    response = call_api("/api/v1/backupInfrastructure/repositories",
                        pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    if args.filter:
        body = json.loads(response.get("body") or "{}")
        response = dict(response, body=json.dumps(_apply_filter(body, args.filter)))
    _print_response(response, args)


def cmd_repos_show(args):
    path = f"/api/v1/backupInfrastructure/repositories/{args.repo_id}"
    response = call_api(path, pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_repos_states(args):
    response = call_api("/api/v1/backupInfrastructure/repositories/states",
                        pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    if args.filter:
        body = json.loads(response.get("body") or "{}")
        response = dict(response, body=json.dumps(_apply_filter(body, args.filter)))
    _print_response(response, args)


def cmd_jobs_show(args):
    path = f"/api/v1/jobs/{args.job_id}"
    response = call_api(path, pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_stop(args):
    path = f"/api/v1/jobs/{args.job_id}/stop"
    response = call_api(path, method="POST", data={}, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_enable(args):
    path = f"/api/v1/jobs/{args.job_id}/enable"
    response = call_api(path, method="POST", data={}, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_disable(args):
    path = f"/api/v1/jobs/{args.job_id}/disable"
    response = call_api(path, method="POST", data={}, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_retry(args):
    path = f"/api/v1/jobs/{args.job_id}/retry"
    response = call_api(path, method="POST", data={}, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_delete(args):
    if not args.force:
        confirm = input(f"Delete job {args.job_id}? This cannot be undone. Type 'yes' to confirm: ").strip()
        if confirm.lower() != "yes":
            print("Aborted.")
            return
    path = f"/api/v1/jobs/{args.job_id}"
    response = call_api(path, method="DELETE", pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_clone(args):
    path = f"/api/v1/jobs/{args.job_id}/clone"
    body: Dict[str, Any] = {}
    if args.name:
        body["name"] = args.name
    response = call_api(path, method="POST", data=body, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_update(args):
    spec = _parse_json_arg(args.spec)
    if not spec:
        raise CliError("JOBS_UPDATE_SPEC_REQUIRED", "A --spec JSON body or @file is required for update.")
    path = f"/api/v1/jobs/{args.job_id}"
    response = call_api(path, method="PUT", data=spec, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_states(args):
    params: Dict[str, Any] = {}
    if args.limit:
        params["limit"] = args.limit
    if args.name_filter:
        params["nameFilter"] = args.name_filter
    if args.type_filter:
        params["typeFilter"] = args.type_filter
    if args.last_result_filter:
        params["lastResultFilter"] = args.last_result_filter
    if args.status_filter:
        params["statusFilter"] = args.status_filter
    if args.repo_id:
        params["repositoryIdFilter"] = args.repo_id
    if args.last_run_after:
        params["lastRunAfterFilter"] = args.last_run_after
    if args.high_priority:
        params["isHighPriorityJobFilter"] = "true"
    response = call_api("/api/v1/jobs/states", params=params, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    if args.filter:
        body = json.loads(response.get("body") or "{}")
        response = dict(response, body=json.dumps(_apply_filter(body, args.filter)))
    _print_response(response, args)


def cmd_jobs_quick_backup(args):
    spec = _parse_json_arg(args.spec) if args.spec else {}
    response = call_api("/api/v1/jobs/quickBackup/vSphere", method="POST", data=spec, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_export(args):
    body: Dict[str, Any] = {}
    if args.job_ids:
        body["jobIds"] = [j.strip() for j in args.job_ids.split(",")]
    if args.spec:
        body = _parse_json_arg(args.spec) or body
    response = call_api("/api/v1/automation/jobs/export", method="POST", data=body, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    if args.output_file:
        raw = response.get("body") or ""
        Path(args.output_file).write_text(raw)
        print(f"Exported to {args.output_file}")
    else:
        _print_response(response, args)


def cmd_jobs_import(args):
    import_path = Path(args.import_file).expanduser()
    if not import_path.exists():
        raise CliError("JOBS_IMPORT_FILE_NOT_FOUND", f"File not found: {import_path}")
    body = json.loads(import_path.read_text())
    response = call_api("/api/v1/automation/jobs/import", method="POST", data=body, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_apply_policy(args):
    path = f"/api/v1/jobs/{args.job_id}/applyConfiguration"
    response = call_api(path, method="POST", data={}, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_clear_cache(args):
    path = f"/api/v1/jobs/{args.job_id}/clearCache"
    response = call_api(path, method="POST", data={}, pretty=False,
                        refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_sessions_list(args):
    params: Dict[str, Any] = {}
    if args.limit:
        params["limit"] = args.limit
    if args.job_id:
        params["jobIdFilter"] = args.job_id
    if args.state:
        params["stateFilter"] = args.state
    if args.result:
        params["resultFilter"] = args.result
    response = call_api("/api/v1/sessions", params=params,
                        pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    if args.filter:
        body = json.loads(response.get("body") or "{}")
        response = dict(response, body=json.dumps(_apply_filter(body, args.filter)))
    _print_response(response, args)


def cmd_proxies_list(args):
    response = call_api("/api/v1/backupInfrastructure/proxies",
                        pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    if args.filter:
        body = json.loads(response.get("body") or "{}")
        response = dict(response, body=json.dumps(_apply_filter(body, args.filter)))
    _print_response(response, args)


def cmd_proxies_states(args):
    response = call_api("/api/v1/backupInfrastructure/proxies/states",
                        pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_sobr_list(args):
    response = call_api("/api/v1/backupInfrastructure/scaleOutRepositories",
                        pretty=False, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    if args.filter:
        body = json.loads(response.get("body") or "{}")
        response = dict(response, body=json.dumps(_apply_filter(body, args.filter)))
    _print_response(response, args)


def cmd_auth_test(args):
    import time
    account = args.account
    # Step 1: config
    from .accounts import list_accounts, get_account_credentials, resolve_account
    resolved = resolve_account(account)
    if not resolved:
        raise CliError("AUTH_TEST_NO_ACCOUNT",
                       "No account configured.",
                       hint="Run `bakufu auth setup <name>` first.")
    creds = get_account_credentials(resolved)
    server = creds.get("server", "") if creds else ""
    insecure = creds.get("insecure", False) if creds else False
    print(f"Account   : {resolved}")
    print(f"Server    : {server}")
    print(f"Insecure  : {'yes' if insecure else 'no'}")

    # Step 2: token
    print("Token     : ", end="", flush=True)
    t0 = time.time()
    try:
        ensure_token(force_refresh=True, account=account)
        print(f"OK ({int((time.time()-t0)*1000)}ms)")
    except Exception as exc:
        print(f"FAIL — {exc}")
        raise CliError("AUTH_TEST_TOKEN_FAILED", str(exc),
                       hint="Check credentials with `bakufu auth setup`.")

    # Step 3: API reachability
    print("API       : ", end="", flush=True)
    t0 = time.time()
    try:
        resp = call_api("/api/v1/serverInfo", pretty=False, account=account)
        body = json.loads(resp.get("body") or "{}")
        ver = body.get("buildVersion") or body.get("serverVersion") or "unknown"
        print(f"OK ({int((time.time()-t0)*1000)}ms) — VBR {ver}")
    except Exception as exc:
        print(f"FAIL — {exc}")
        raise CliError("AUTH_TEST_API_FAILED", str(exc))

    print("Result    : PASS")


def cmd_mcp_config(args):
    import shutil
    binary = shutil.which("bakufu") or sys.executable
    # If running in a venv, prefer the venv binary
    if getattr(sys, "frozen", False):
        binary = sys.executable

    config = {
        "mcpServers": {
            "bakufu": {
                "command": binary,
                "args": ["mcp"],
                "env": {}
            }
        }
    }

    account = args.account
    if account:
        config["mcpServers"]["bakufu"]["args"].extend(["--account", account])

    if args.services and args.services != "all":
        config["mcpServers"]["bakufu"]["args"].extend(["--services", args.services])

    print("# Paste into your MCP client config (e.g. claude_desktop_config.json)")
    print(json.dumps(config, indent=2))
    print()
    print("# Claude Desktop config path:")
    print("#   macOS  : ~/Library/Application Support/Claude/claude_desktop_config.json")
    print("#   Windows: %APPDATA%\\Claude\\claude_desktop_config.json")
    print("#   Linux  : ~/.config/Claude/claude_desktop_config.json")
    print()
    print(f"# Binary detected at: {binary}")


def cmd_update(args):
    import urllib.request
    import platform

    print("Checking for updates...")
    try:
        url = "https://api.github.com/repos/anthonyspiteri/veeam-cli/releases/latest"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                    "User-Agent": "bakufu-cli"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            release = json.loads(resp.read())
    except Exception as exc:
        raise CliError("UPDATE_CHECK_FAILED", f"Could not reach GitHub: {exc}")

    latest_tag = release.get("tag_name", "").lstrip("v")
    try:
        current = importlib.metadata.version("bakufu-cli")
    except importlib.metadata.PackageNotFoundError:
        current = "unknown"

    print(f"Current   : {current}")
    print(f"Latest    : {latest_tag}")

    if current == latest_tag:
        print("Already up to date.")
        return

    if args.check:
        print(f"Update available: {current} -> {latest_tag}")
        print("Run `bakufu update` without --check to install.")
        return

    # Detect platform and pick asset
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        asset_name = "bakufu-macos-arm64"
    elif system == "linux":
        asset_name = "bakufu-linux-x86_64"
    elif system == "windows":
        asset_name = "bakufu-windows-x86_64.exe"
    else:
        raise CliError("UPDATE_PLATFORM_UNSUPPORTED", f"Unsupported platform: {system}")

    assets = release.get("assets", [])
    asset = next((a for a in assets if a.get("name") == asset_name), None)
    if not asset:
        raise CliError("UPDATE_ASSET_NOT_FOUND",
                       f"Binary '{asset_name}' not found in release {latest_tag}.",
                       hint="Try installing manually via the install script.")

    print(f"Downloading {asset_name}...")
    import shutil
    import stat
    import tempfile

    download_url = asset["browser_download_url"]
    with tempfile.NamedTemporaryFile(delete=False, suffix="-bakufu-new") as tmp:
        tmp_path = tmp.name
        req2 = urllib.request.Request(download_url, headers={"User-Agent": "bakufu-cli"})
        with urllib.request.urlopen(req2, timeout=60) as r:
            shutil.copyfileobj(r, tmp)

    # Find current install path
    install_path = shutil.which("bakufu")
    if not install_path:
        install_path = "/usr/local/bin/bakufu"

    os.chmod(tmp_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    try:
        shutil.move(tmp_path, install_path)
    except PermissionError:
        import subprocess
        subprocess.run(["sudo", "mv", tmp_path, install_path], check=True)

    print(f"Updated to {latest_tag} at {install_path}")


def cmd_doctor(args):
    import time
    import shutil
    import platform

    ok = True

    def check(label: str, fn):
        nonlocal ok
        print(f"  {label:<30}", end="", flush=True)
        try:
            result = fn()
            print(f"OK  {result or ''}")
        except Exception as exc:
            print(f"FAIL  {exc}")
            ok = False

    print(f"\nbakufu doctor\n{'='*50}")
    print(f"\nSystem")

    try:
        ver = importlib.metadata.version("bakufu-cli")
    except importlib.metadata.PackageNotFoundError:
        ver = "unknown"

    check("bakufu version", lambda: ver)
    check("python version", lambda: platform.python_version())
    check("platform", lambda: f"{platform.system()} {platform.machine()}")
    check("curl available", lambda: shutil.which("curl") or (_ for _ in ()).throw(Exception("not found")))

    print(f"\nAuth config")
    from .accounts import list_accounts, resolve_account, get_account_credentials
    data = list_accounts()
    accounts = data.get("accounts", {})
    if not accounts:
        print("  No accounts configured — run `bakufu auth setup <name>`")
        ok = False
    else:
        default = data.get("default")
        for name, info in accounts.items():
            marker = " (default)" if name == default else ""
            check(f"account '{name}'{marker}", lambda n=name, i=info: i.get("server", "?"))

    print(f"\nConnectivity")
    resolved = resolve_account(args.account)
    if resolved:
        check("token refresh", lambda: ensure_token(force_refresh=True, account=resolved) and "valid")

        def _api_check():
            t0 = time.time()
            resp = call_api("/api/v1/serverInfo", pretty=False, account=resolved)
            body = json.loads(resp.get("body") or "{}")
            ms = int((time.time() - t0) * 1000)
            ver = body.get("buildVersion") or body.get("serverVersion") or "?"
            return f"VBR {ver} ({ms}ms)"
        check("API reachable", _api_check)
    else:
        print("  Skipped — no account configured")

    print(f"\nData files")
    check("skills.md", lambda: str(DOCS_SKILLS_PATH) if DOCS_SKILLS_PATH.exists() else (_ for _ in ()).throw(Exception("missing")))

    def _swagger_check():
        spec = SwaggerSpec.load()
        ops = list(spec.iter_operations())
        return f"{len(ops)} operations"
    check("swagger spec", _swagger_check)

    print(f"\n{'='*50}")
    print("Result: PASS" if ok else "Result: FAIL — see errors above")
    print()


def cmd_skills_list(_args):
    print(DOCS_SKILLS_PATH.read_text())


def _schema_params_summary(schema: Dict[str, Any]) -> str:
    """Return a compact human-readable param summary from a JSON schema object."""
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    parts = []
    for key, meta in props.items():
        if key == "account":
            continue
        desc = meta.get("description", "")
        if key in required:
            parts.append(f"--{_flag(key)}  (required)")
        else:
            # shorten long descriptions to 50 chars
            short = desc[:50] + "..." if len(desc) > 50 else desc
            parts.append(f"--{_flag(key)}  [{short}]")
    return "\n    ".join(parts) if parts else "--account  (optional)"


def _flag(camel: str) -> str:
    """Convert camelCase param name to kebab-case CLI flag."""
    s = re.sub(r"([A-Z])", r"-\1", camel).lower().lstrip("-")
    return s


def _print_catalog(title: str, entries: Dict[str, Dict], strip_prefix: str = "bakufu_") -> None:
    """Print a formatted catalog of workflows or helpers."""
    rows = []
    for full_key, meta in entries.items():
        short_id = full_key[len(strip_prefix):] if full_key.startswith(strip_prefix) else full_key
        desc = meta.get("description", "")
        schema = meta.get("inputSchema", {})
        required = [k for k in schema.get("required", []) if k != "account"]
        optional = [k for k, v in schema.get("properties", {}).items()
                    if k not in schema.get("required", []) and k != "account"]
        req_str = "  ".join(f"--{_flag(k)}" for k in required) if required else ""
        opt_str = "  ".join(f"[--{_flag(k)}]" for k in optional) if optional else ""
        params = "  ".join(filter(None, [req_str, opt_str])) or "[no extra params]"
        rows.append((short_id, desc, params))

    if not rows:
        print(f"No {title.lower()} found.")
        return

    id_w = max(len(r[0]) for r in rows)
    desc_w = min(60, max(len(r[1]) for r in rows))
    print(f"\n  {'NAME':<{id_w}}  {'DESCRIPTION':<{desc_w}}  PARAMS")
    print(f"  {'-' * id_w}  {'-' * desc_w}  {'-' * 40}")
    for short_id, desc, params in rows:
        desc_trunc = desc[:desc_w - 3] + "..." if len(desc) > desc_w else desc
        print(f"  {short_id:<{id_w}}  {desc_trunc:<{desc_w}}  {params}")
    print()


def cmd_workflow(args):
    if not args.workflow_id:
        print("Curated multi-step workflows.\n")
        print("Usage:  bakufu workflows <workflow> [flags]  [--describe]\n")
        _print_catalog("Workflows", WORKFLOWS, strip_prefix="bakufu_workflows_")
        print("  --account        Use a named account (overrides default)")
        print("  --describe       Show full parameter schema for a workflow")
        print("  --wait           Wait for async workflows to complete")
        print("  --interval-ms    Poll interval when --wait is used (default 2000)")
        print("  --timeout-ms     Max wait time when --wait is used (default 300000)")
        print()
        return

    workflow_name = f"bakufu_workflows_{args.workflow_id}"
    if workflow_name not in WORKFLOWS:
        raise CliError("WORKFLOW_NOT_FOUND", f"Workflow not found: {args.workflow_id}")

    if getattr(args, "describe", False):
        meta = WORKFLOWS[workflow_name]
        print(json.dumps({
            "workflow": args.workflow_id,
            "description": meta["description"],
            "inputSchema": meta["inputSchema"],
        }, indent=2))
        return

    payload: Dict[str, Any] = {"account": args.account}
    if args.job_id:
        payload["jobId"] = args.job_id
    if args.job_name:
        payload["jobName"] = args.job_name
    if args.spec:
        payload["repoSpec"] = _parse_json_arg(args.spec)
    if getattr(args, "wait", False):
        payload["wait"] = True
        payload["intervalMs"] = int(getattr(args, "interval_ms", 2000) or 2000)
        payload["timeoutMs"] = int(getattr(args, "timeout_ms", 300000) or 300000)
    result = run_workflow(workflow_name, payload)
    output = getattr(args, "output", "table")
    if output == "raw":
        print(json.dumps(result, separators=(",", ":")))
        return
    if output == "table":
        rendered = _render_table(result)
        if rendered is None and isinstance(result, dict):
            rendered = _render_object(result)
        if rendered:
            print(rendered)
            return
    print(json.dumps(result, indent=2))


def cmd_helpers_list(_args):
    print("Low-level helpers — focused operations that may chain a few API calls.\n")
    print("Usage:  bakufu helpers <helper> [flags]  [--describe]\n")
    _print_catalog("Helpers", HELPERS)
    print("  --account        Use a named account (overrides default)")
    print("  --describe       Show full parameter schema for a helper")
    print()


def cmd_helper(args):
    if not args.helper_id:
        cmd_helpers_list(args)
        return

    helper_name = f"bakufu_{args.helper_id}"
    if helper_name not in HELPERS:
        raise CliError("HELPER_NOT_FOUND", f"Helper not found: {args.helper_id}",
                       hint=f"Run `bakufu helpers` to list available helpers.")

    if getattr(args, "describe", False):
        meta = HELPERS[helper_name]
        print(json.dumps({
            "helper": args.helper_id,
            "description": meta["description"],
            "inputSchema": meta["inputSchema"],
        }, indent=2))
        return

    payload: Dict[str, Any] = {"account": args.account}
    if getattr(args, "name", None):
        payload["name"] = args.name
    if getattr(args, "job_id", None):
        payload["jobId"] = args.job_id
    if getattr(args, "session_id", None):
        payload["sessionId"] = args.session_id
    if getattr(args, "server_id", None):
        payload["serverId"] = args.server_id
    if getattr(args, "spec", None):
        payload["spec"] = _parse_json_arg(args.spec)
    if getattr(args, "schedule", None):
        payload["schedule"] = _parse_json_arg(args.schedule)
    if getattr(args, "storage", None):
        payload["storage"] = _parse_json_arg(args.storage)
    if getattr(args, "interval_ms", None):
        payload["intervalMs"] = int(args.interval_ms)
    if getattr(args, "timeout_ms", None):
        payload["timeoutMs"] = int(args.timeout_ms)

    result = run_helper(helper_name, payload)
    output = getattr(args, "output", "table")
    if output == "raw":
        print(json.dumps(result, separators=(",", ":")))
        return
    if output == "table":
        rendered = _render_table(result)
        if rendered is None and isinstance(result, dict):
            rendered = _render_object(result)
        if rendered:
            print(rendered)
            return
    print(json.dumps(result, indent=2))


def cmd_mcp(args):
    services = None
    if args.services and args.services != "all":
        services = [s.strip() for s in args.services.split(",") if s.strip()]
    serve(services=services, include_helpers=args.helpers, include_workflows=args.workflows)


def _completion_script_bash() -> str:
    return r"""_bakufu_complete() {
  local cur prev cmd subcmd
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  cmd="${COMP_WORDS[1]}"
  subcmd="${COMP_WORDS[2]}"
  local top="auth auth-setup auth-login call services operations run schema jobs sessions repos proxies sobr workflows helpers skills mcp mcp-config license completion getting-started update doctor version"

  if [[ $COMP_CWORD -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "$top --account --insecure -h --help" -- "$cur") )
    return 0
  fi

  case "$cmd" in
    auth)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "setup login list default token test" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--server --username --password --default --refresh --account --insecure -h --help" -- "$cur") )
      fi
      ;;
    jobs)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "list states show start stop retry enable disable delete clone update quick-backup export import apply-policy clear-cache" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--filter --name-filter --type-filter --last-result-filter --status-filter --repo-id --last-run-after --high-priority --limit --name --spec --job-ids --output-file --force --json --raw --refresh --dry-run -h --help" -- "$cur") )
      fi
      ;;
    sessions)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "list show logs" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--filter --limit --job-id --state --result --json --raw --refresh --dry-run -h --help" -- "$cur") )
      fi
      ;;
    services) COMPREPLY=( $(compgen -W "list -h --help" -- "$cur") ) ;;
    skills) COMPREPLY=( $(compgen -W "list -h --help" -- "$cur") ) ;;
    repos)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "list show states" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--filter --json --raw --refresh --dry-run -h --help" -- "$cur") )
      fi
      ;;
    proxies)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "list states" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--filter --json --raw --refresh --dry-run -h --help" -- "$cur") )
      fi
      ;;
    sobr)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "list" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--filter --json --raw --refresh --dry-run -h --help" -- "$cur") )
      fi
      ;;
    workflows)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "investigateFailedJob createWasabiRepo capacityReport runSecurityAnalyzer validateImmutability dailyJobHealth weeklyJobHealth rerunFailedJob repositoryHealthReview emergencyStopJob" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--job-id --job-name --spec --wait --interval-ms --timeout-ms --describe --json --raw -h --help" -- "$cur") )
      fi
      ;;
    helpers)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "jobs_startByName jobs_lastResult jobs_create jobs_updateSchedule sessions_follow sessions_logs repos_capacity repos_addWasabi cloudCredentials_add objectStorage_browse proxies_states sobr_list managedServers_rescan malwareDetection_scan" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--name --job-id --session-id --server-id --spec --schedule --storage --interval-ms --timeout-ms --describe --json --raw -h --help" -- "$cur") )
      fi
      ;;
    run)
      if [[ $COMP_CWORD -eq 2 ]]; then
        local tags
        tags="$(bakufu services list 2>/dev/null)"
        COMPREPLY=( $(compgen -W "$tags" -- "$cur") )
      elif [[ $COMP_CWORD -eq 3 ]]; then
        local ops
        ops="$(bakufu operations --tag "${COMP_WORDS[2]}" 2>/dev/null | awk '{print $2}')"
        COMPREPLY=( $(compgen -W "$ops" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--params --body --json --raw --refresh --dry-run --page-all --page-limit --page-max --page-delay -h --help" -- "$cur") )
      fi
      ;;
    call) COMPREPLY=( $(compgen -W "--method --params --body --json --raw --refresh --dry-run --insecure -h --help" -- "$cur") ) ;;
    operations) COMPREPLY=( $(compgen -W "--tag -h --help" -- "$cur") ) ;;
    mcp) COMPREPLY=( $(compgen -W "-s --services -e --helpers --no-helpers -w --workflows --no-workflows --insecure -h --help" -- "$cur") ) ;;
    mcp-config) COMPREPLY=( $(compgen -W "--account --services -h --help" -- "$cur") ) ;;
    update) COMPREPLY=( $(compgen -W "--check -h --help" -- "$cur") ) ;;
    doctor) COMPREPLY=( $(compgen -W "--account -h --help" -- "$cur") ) ;;
    license)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "show install-file" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--json --raw --refresh --dry-run --force-standalone-mode -h --help" -- "$cur") )
      fi
      ;;
    completion) COMPREPLY=( $(compgen -W "bash zsh -h --help" -- "$cur") ) ;;
    getting-started) COMPREPLY=( $(compgen -W "--demo --script --persona --json --raw -h --help backup-admin backup-operator security-admin dr-operator auditor storage-admin infrastructure-engineer" -- "$cur") ) ;;
    version) COMPREPLY=( $(compgen -W "-h --help" -- "$cur") ) ;;
  esac
}
complete -F _bakufu_complete bakufu
"""


def _completion_script_zsh() -> str:
    return r"""#compdef bakufu
_bakufu() {
  local state
  _arguments -C \
    '--account[Use named account]:account:' \
    '--insecure[Disable TLS certificate verification]' \
    '1:command:->cmds' \
    '*::arg:->args'

  case $state in
    cmds)
      _values 'command' \
        auth auth-setup auth-login call services operations run schema \
        jobs sessions repos proxies sobr workflows helpers skills \
        mcp mcp-config license completion getting-started update doctor version
      ;;
    args)
      case $words[2] in
        auth) _values 'auth command' setup login list default token test ;;
        jobs) _values 'jobs command' list states show start stop retry enable disable delete clone update quick-backup export import apply-policy clear-cache ;;
        sessions) _values 'sessions command' list show logs ;;
        services) _values 'services command' list ;;
        skills) _values 'skills command' list ;;
        repos) _values 'repos command' list show states ;;
        proxies) _values 'proxies command' list states ;;
        sobr) _values 'sobr command' list ;;
        workflows) _values 'workflow' investigateFailedJob createWasabiRepo capacityReport runSecurityAnalyzer validateImmutability dailyJobHealth weeklyJobHealth rerunFailedJob repositoryHealthReview emergencyStopJob ;;
        helpers) _values 'helper' jobs_startByName jobs_lastResult jobs_create jobs_updateSchedule sessions_follow sessions_logs repos_capacity repos_addWasabi cloudCredentials_add objectStorage_browse proxies_states sobr_list managedServers_rescan malwareDetection_scan ;;
        mcp) _values 'options' -s --services -e --helpers --no-helpers -w --workflows --no-workflows --insecure ;;
        mcp-config) _values 'options' --account --services ;;
        update) _values 'options' --check ;;
        doctor) _values 'options' --account ;;
        license) _values 'license command' show install-file ;;
        run)
          if (( CURRENT == 3 )); then
            local -a _tags
            _tags=("${(@f)$(bakufu services list 2>/dev/null)}")
            compadd -- ${_tags}
          elif (( CURRENT == 4 )); then
            local -a _ops
            _ops=("${(@f)$(bakufu operations --tag "$words[3]" 2>/dev/null | awk '{print $2}')}")
            compadd -- ${_ops}
          else
            _values 'run options' --params --body --json --raw --refresh --dry-run --page-all --page-limit --page-max --page-delay --insecure
          fi
          ;;
        license) _values 'license command' show install-file ;;
        completion) _values 'shell' bash zsh ;;
        getting-started) _values 'options' --demo --script --persona --json --raw backup-admin backup-operator security-admin dr-operator auditor storage-admin infrastructure-engineer ;;
        version) _values 'options' ;;
      esac
      ;;
  esac
}
compdef _bakufu bakufu
"""


def cmd_completion(args):
    if args.shell == "bash":
        print(_completion_script_bash())
        return
    if args.shell == "zsh":
        print(_completion_script_zsh())
        return
    raise CliError("COMPLETION_SHELL_UNSUPPORTED", f"Unsupported shell: {args.shell}")


def cmd_version(_args):
    try:
        print(importlib.metadata.version("bakufu-cli"))
    except importlib.metadata.PackageNotFoundError:
        print("unknown")


def cmd_getting_started(args):
    persona_playbooks: Dict[str, Dict[str, Any]] = {
        "backup-admin": {
            "title": "Backup Admin",
            "goal": "Govern backup architecture, repository posture, and operational reliability.",
            "focus": [
                "Repository capacity and immutability",
                "Infrastructure component health",
                "Policy and schedule quality",
            ],
            "commands": [
                "bakufu auth setup demo-lab --default --server \"https://vbr-demo.example.local:9419\" --username \"backupadmin\"",
                "bakufu auth token --refresh --account demo-lab",
                "bakufu license show --account demo-lab",
                "bakufu workflows capacityReport --account demo-lab",
                "bakufu workflows validateImmutability --account demo-lab",
                "bakufu run Repositories GetAllRepositories --account demo-lab",
            ],
            "recipes": [
                "recipe-capacity-report",
                "recipe-validate-immutability",
                "recipe-repository-online-check",
            ],
        },
        "backup-operator": {
            "title": "Backup Operator",
            "goal": "Run daily backup operations and triage failures quickly.",
            "focus": [
                "Job status and recent session outcomes",
                "Failed session diagnostics",
                "Rerun safety and handoff reporting",
            ],
            "commands": [
                "bakufu auth token --refresh --account demo-lab",
                "bakufu run Jobs GetAllJobs --account demo-lab",
                "bakufu workflows investigateFailedJob --job-name \"Demo Nightly Backup\" --account demo-lab",
                "bakufu run Sessions GetAllSessions --params '{\"limit\":20}' --account demo-lab",
                "bakufu sessions logs <session-id> --account demo-lab",
            ],
            "recipes": [
                "recipe-investigate-failed-job",
                "recipe-rerun-failed-job",
                "recipe-daily-job-health",
            ],
        },
        "security-admin": {
            "title": "Security Admin",
            "goal": "Operate security controls, analyzer findings, and malware evidence.",
            "focus": [
                "Security Analyzer run state and findings",
                "Malware event review",
                "Encryption and immutability posture",
            ],
            "commands": [
                "bakufu auth token --refresh --account demo-lab",
                "bakufu workflows runSecurityAnalyzer --account demo-lab",
                "bakufu run Security GetBestPracticesComplianceResult --account demo-lab",
                "bakufu run Malware\\ Detection GetAllMalwareEvents --account demo-lab",
                "bakufu workflows validateImmutability --account demo-lab",
            ],
            "recipes": [
                "recipe-security-analyzer-run",
                "recipe-best-practices-review",
                "recipe-malware-events-review",
            ],
        },
        "dr-operator": {
            "title": "DR Operator",
            "goal": "Validate recoverability and execute failover/failback safely.",
            "focus": [
                "Restore-point coverage",
                "Failover and failback readiness",
                "Session SLA and dependency risks",
            ],
            "commands": [
                "bakufu auth token --refresh --account demo-lab",
                "bakufu run Restore\\ Points GetAllRestorePoints --account demo-lab",
                "bakufu run Replicas GetAllReplicas --account demo-lab",
                "bakufu run Failover GetAllFailoverPlans --account demo-lab",
                "bakufu run Failback GetAllFailbackPlans --account demo-lab",
            ],
            "recipes": [
                "recipe-restore-point-coverage",
                "recipe-restore-readiness-check",
                "recipe-dr-failover-readiness",
            ],
        },
        "auditor": {
            "title": "Auditor",
            "goal": "Collect evidence for compliance and operational audit reporting.",
            "focus": [
                "Session and task evidence",
                "Security and authorization event evidence",
                "License and infrastructure posture",
            ],
            "commands": [
                "bakufu auth token --refresh --account demo-lab",
                "bakufu run Sessions GetAllSessions --params '{\"limit\":50}' --account demo-lab",
                "bakufu run Security GetAllAuthorizationEvents --account demo-lab",
                "bakufu license show --account demo-lab",
                "bakufu workflows capacityReport --account demo-lab",
            ],
            "recipes": [
                "recipe-audit-four-eyes-events",
                "recipe-auditor-monthly-pack",
                "recipe-job-session-export",
            ],
        },
    }

    if args.persona:
        playbook = persona_playbooks[args.persona]
        lines = [
            f"bakufu persona onboarding: {playbook['title']}",
            "",
            f"Goal: {playbook['goal']}",
            "",
            "Primary focus:",
        ]
        for item in playbook["focus"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("Step-by-step commands:")
        for i, cmd in enumerate(playbook["commands"], start=1):
            lines.append(f"{i}. {cmd}")
        lines.append("")
        lines.append("Recommended recipes:")
        for r in playbook["recipes"]:
            lines.append(f"- {r}")
        lines.append("")
        lines.append("Tip: replace demo values with your real account/server before execution.")
        print("\n".join(lines))
        return

    if args.script:
        print(
            """# bakufu first-run demo script (read-only)
# 1) configure auth once (interactive)
bakufu auth setup demo-lab --default \
  --server "https://vbr-demo.example.local:9419" \
  --username "backupadmin"
# (password prompt will appear)

# 2) validate auth
bakufu auth token --refresh --account demo-lab

# 3) basic server checks
bakufu GetServerTime
bakufu call /api/v1/serverInfo --account demo-lab
bakufu license show --account demo-lab

# 4) discover command surface
bakufu services list
bakufu operations --tag Service
bakufu Service GetServerTime
bakufu schema GetAllJobs

# 5) output modes
bakufu GetServerTime --raw
bakufu run Services GetAllServices --account demo-lab

# 6) workflow recipes
bakufu workflows capacityReport --account demo-lab
bakufu workflows investigateFailedJob --job-name "Demo Nightly Backup" --account demo-lab

# 7) skills + MCP
bakufu skills list
bakufu mcp --services Service,Jobs,Sessions --helpers --workflows
"""
        )
        return

    if not args.demo:
        text = """bakufu quick start (safe examples with fake values)

1) Configure auth (example values):
   bakufu auth setup demo-lab --default \\
     --server "https://vbr-demo.example.local:9419" \\
     --username "backupadmin"
   # password is prompted securely

2) Validate token:
   bakufu auth token --refresh --account demo-lab

3) Read-only smoke checks:
   bakufu GetServerTime
   bakufu call /api/v1/serverInfo --account demo-lab
   bakufu license show --account demo-lab

4) Discover API surface:
   bakufu services list
   bakufu operations --tag Jobs
   bakufu run Jobs GetAllJobs --account demo-lab
   bakufu schema GetAllJobs

5) Shorthand power:
   bakufu Service GetServerTime
   bakufu GetServerTime

6) Output modes:
   bakufu GetServerTime --raw
   bakufu run Services GetAllServices --account demo-lab

7) Recipes:
   bakufu workflows capacityReport --account demo-lab
   bakufu workflows runSecurityAnalyzer --account demo-lab
   bakufu workflows investigateFailedJob --job-name "Demo Nightly Backup" --account demo-lab

8) Skills and MCP:
   bakufu skills list
   bakufu mcp --services Service,Jobs,Sessions --helpers --workflows

9) Shell completion:
   bakufu completion zsh > ~/.bakufu-completion.zsh
   source ~/.bakufu-completion.zsh
"""
        print(text)
        return

    report: Dict[str, Any] = {"demo": "read-only", "steps": []}
    checks = [
        (
            "auth.list",
            "bakufu auth list",
            "Check whether at least one account exists.",
            lambda: list_accounts(),
        ),
        (
            "auth.token.refresh",
            "bakufu auth token --refresh",
            "Validate credentials and obtain a fresh token.",
            lambda: ensure_token(force_refresh=True, account=args.account),
        ),
        (
            "service.time",
            "bakufu GetServerTime",
            "Read-only unauthenticated server-time endpoint check.",
            lambda: call_api("/api/v1/serverTime", pretty=False, account=args.account),
        ),
        (
            "service.info",
            "bakufu call /api/v1/serverInfo",
            "Read-only authenticated server information check.",
            lambda: call_api("/api/v1/serverInfo", pretty=False, account=args.account),
        ),
        (
            "license.show",
            "bakufu license show",
            "Read current license status and edition.",
            lambda: call_api("/api/v1/license", pretty=False, account=args.account),
        ),
    ]
    for index, (name, command, hint_text, fn) in enumerate(checks, start=1):
        try:
            result = fn()
            if isinstance(result, dict) and "status" in result:
                status = int(result.get("status") or 0)
                ok = status < 400
                item = {
                    "step": index,
                    "name": name,
                    "command": command,
                    "hint": hint_text,
                    "ok": ok,
                    "httpStatus": status,
                }
                if result.get("body"):
                    item["bodyPreview"] = str(result["body"])[:300]
                report["steps"].append(item)
            else:
                report["steps"].append(
                    {
                        "step": index,
                        "name": name,
                        "command": command,
                        "hint": hint_text,
                        "ok": True,
                    }
                )
        except Exception as exc:
            report["steps"].append(
                {
                    "step": index,
                    "name": name,
                    "command": command,
                    "hint": hint_text,
                    "ok": False,
                    "error": str(exc),
                }
            )

    report["ok"] = all(step.get("ok") for step in report["steps"])
    output = getattr(args, "output", "table")
    if output == "raw":
        print(json.dumps(report, separators=(",", ":")))
        return
    if output == "json":
        print(json.dumps(report, indent=2))
        return

    print("bakufu getting-started demo (read-only)")
    print("")
    for step in report["steps"]:
        status = "PASS" if step.get("ok") else "FAIL"
        print(f"[{step['step']}] {status}  {step['name']}")
        print(f"$ {step['command']}")
        print(f"hint: {step['hint']}")
        if step.get("httpStatus") is not None:
            print(f"http: {step['httpStatus']}")
        if step.get("error"):
            print(f"error: {step['error']}")
        if step.get("bodyPreview"):
            print(f"preview: {step['bodyPreview'][:180]}")
        print("")

    if report["ok"]:
        print("Result: READY")
    else:
        print("Result: NOT READY")
        print("Next: run `bakufu auth setup <account> --default` then `bakufu auth token --refresh` and retry.")


def _raise_for_http_error(response: Dict[str, Any]) -> None:
    status_raw = response.get("status")
    try:
        status = int(status_raw) if status_raw is not None else 0
    except ValueError:
        status = 0
    if status < 400:
        return

    body = response.get("body") or ""
    error_code = "API_HTTP_ERROR"
    message = f"Request failed with HTTP {status}"
    details: Dict[str, Any] = {"status": status}
    hint = None

    if body:
        try:
            body_json = json.loads(body)
            details["response"] = body_json
            if isinstance(body_json, dict):
                message = body_json.get("message") or body_json.get("title") or message
                if body_json.get("errorCode"):
                    error_code = str(body_json.get("errorCode"))
        except json.JSONDecodeError:
            details["response"] = body

    if status == 401:
        hint = "Authentication failed. Re-run `bakufu auth setup <account>` and `bakufu auth token --refresh`."
    elif status == 403:
        hint = "Access denied. Verify role permissions for this API operation."
    elif status == 404:
        hint = "Endpoint or object not found. Validate operation/path and object IDs."
    elif "License restrictions apply" in body:
        hint = "Install a valid VBR license first: `bakufu license install-file /path/to/license.lic`."
    elif "SSL certificate problem" in body:
        hint = "Certificate verification failed. Use trusted certs, or explicitly opt in with `--insecure`."

    raise CliError(error_code, message, hint=hint, details=details)


def _print_response(response, args):
    if args.dry_run:
        print(json.dumps({"curl": response["cmd"]}, indent=2))
        return
    if isinstance(response, dict) and "status" in response:
        _raise_for_http_error(response)
        body = response.get("body") or ""
        output = getattr(args, "output", "table")
        status = response["status"]

        # 204 No Content or genuinely empty body
        if not body:
            print(f"HTTP {status} OK", file=sys.stderr)
            return

        if output == "raw":
            print(f"HTTP {status}", file=sys.stderr)
            print(body)
            return

        # Parse body for table/json modes
        parsed = None
        try:
            parsed = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            pass

        # Empty JSON object {} = success confirmation
        if isinstance(parsed, dict) and len(parsed) == 0:
            print(f"HTTP {status} OK", file=sys.stderr)
            return

        print(f"HTTP {status}", file=sys.stderr)

        if output == "table":
            rendered = None
            if parsed is not None:
                rendered = _render_table(parsed)
                if rendered is None and isinstance(parsed, dict):
                    rendered = _render_object(parsed)
            if rendered:
                print(rendered)
            elif parsed is not None:
                print(json.dumps(parsed, indent=2))
            else:
                print(body)
        else:  # json
            if parsed is not None:
                print(json.dumps(parsed, indent=2))
            else:
                print(body)
    else:
        print(response)


def _cell_value(value: Any) -> str:
    """Format a cell value for table display."""
    if value is None:
        return ""
    if isinstance(value, list):
        if not value:
            return ""
        if all(not isinstance(item, (dict, list)) for item in value):
            # Scalar array: comma-separated, clipped at 5 items
            parts = [str(v) for v in value[:5]]
            return ", ".join(parts) + ("\u2026" if len(value) > 5 else "")
        return f"[{len(value)} items]"
    if isinstance(value, dict):
        # Prefer id or name as a compact reference
        for key in ("id", "name", "type"):
            if key in value:
                return str(value[key])
        return "{…}"
    return str(value)


def _render_object(payload: dict) -> Optional[str]:
    """Render a single dict as a two-column key-value table.

    Scalar fields and scalar arrays are rendered inline.
    Nested objects show id/name when available, otherwise {…}.
    """
    if not payload or not isinstance(payload, dict):
        return None
    lines = []
    key_width = min(max((len(k) for k in payload), default=0), 40)
    for k, v in payload.items():
        val = _cell_value(v)
        if len(val) > 100:
            val = val[:99] + "\u2026"
        lines.append(f"{k.ljust(key_width)}  {val}")
    return "\n".join(lines) if lines else None


def _render_table(payload: Any) -> Optional[str]:
    """Render a list/paginated response as a table.

    Handles VBR API response shapes:
      { "data": [...], "pagination": {...} }          (most endpoints)
      { "items": [...], "pagination": {...} }         (FLR, BestPractices)
      { "records": [...], "totalRecords": N }         (SessionLog)
      { "items": [...] }                              (no pagination)
    """
    rows = None
    pagination_footer = None

    if isinstance(payload, dict):
        # 1. Try known VBR list keys in priority order
        for field in ("data", "items", "records", "workloads", "tenantResources"):
            candidate = payload.get(field)
            if isinstance(candidate, list):
                rows = candidate
                break

        # 2. Auto-detect: scan all values for a list of dicts (covers any undocumented key)
        if rows is None:
            for v in payload.values():
                if isinstance(v, list) and v and all(isinstance(item, dict) for item in v):
                    rows = v
                    break

        if rows is not None:
            # Build pagination footer
            pg = payload.get("pagination")
            if isinstance(pg, dict):
                total = pg.get("total")
                count = pg.get("count")
                skip = pg.get("skip", 0)
                if total is not None and count is not None:
                    end = (skip or 0) + count
                    pagination_footer = f"Showing {(skip or 0) + 1}\u2013{end} of {total}"
            elif "totalRecords" in payload:
                pagination_footer = f"{payload['totalRecords']} total records"
    elif isinstance(payload, list):
        rows = payload

    if not rows:
        return None
    if not all(isinstance(r, dict) for r in rows):
        return None

    keys = list(rows[0].keys())[:8]
    if not keys:
        return None

    values = [[_cell_value(row.get(key)) for key in keys] for row in rows]

    widths = [len(k) for k in keys]
    for vals in values:
        for i, v in enumerate(vals):
            widths[i] = min(max(widths[i], len(v)), 80)

    def _clip(s: str, w: int) -> str:
        return s if len(s) <= w else s[: w - 1] + "\u2026"

    header = " | ".join(_clip(k, widths[i]).ljust(widths[i]) for i, k in enumerate(keys))
    sep = "-+-".join("-" * widths[i] for i in range(len(keys)))
    body_lines = [
        " | ".join(_clip(v, widths[i]).ljust(widths[i]) for i, v in enumerate(vals))
        for vals in values
    ]
    lines = [header, sep] + body_lines
    if pagination_footer:
        lines.append(pagination_footer)
    return "\n".join(lines)


def _add_output_flags(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--json", dest="output", action="store_const", const="json",
                       help="Pretty-print JSON output")
    group.add_argument("--raw", dest="output", action="store_const", const="raw",
                       help="Compact JSON output")
    parser.set_defaults(output="table")


def _add_auth_parser(subparsers):
    auth = subparsers.add_parser("auth", help="Authentication commands")
    auth.set_defaults(func=lambda _args: auth.print_help())
    auth_sub = auth.add_subparsers(dest="auth_cmd")

    auth_setup_cmd = auth_sub.add_parser("setup", help="Guided setup and validation")
    auth_setup_cmd.add_argument("account_name")
    auth_setup_cmd.add_argument("--server")
    auth_setup_cmd.add_argument("--username")
    auth_setup_cmd.add_argument("--password", help="Password (omit to use secure interactive prompt — avoids shell history exposure)")
    auth_setup_cmd.add_argument("--default", action="store_true")
    auth_setup_cmd.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    auth_setup_cmd.set_defaults(func=cmd_auth_setup)

    auth_login = auth_sub.add_parser("login", help="Add account without setup checks")
    auth_login.add_argument("account_name")
    auth_login.add_argument("--server")
    auth_login.add_argument("--username")
    auth_login.add_argument("--password", help="Password (omit to use secure interactive prompt — avoids shell history exposure)")
    auth_login.add_argument("--default", action="store_true")
    auth_login.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    auth_login.set_defaults(func=cmd_auth_login)

    auth_list = auth_sub.add_parser("list", help="List configured accounts")
    auth_list.set_defaults(func=cmd_auth_list)

    auth_default = auth_sub.add_parser("default", help="Set default account")
    auth_default.add_argument("account_name")
    auth_default.set_defaults(func=cmd_auth_default)

    auth_token = auth_sub.add_parser("token", help="Show token status or refresh for account")
    auth_token.add_argument("--refresh", action="store_true", help="Force a new token request")
    auth_token.add_argument("--show", action="store_true", help="Print the raw access token value")
    auth_token.add_argument("--account", help="Use a named account")
    auth_token.set_defaults(func=cmd_auth_token)

    auth_test_cmd = auth_sub.add_parser(
        "test",
        help="Test connectivity: token refresh, API reachability, and server version",
        description=(
            "Verify the full authentication and connectivity chain for an account.\n\n"
            "Checks: account config present, token refresh succeeds, API endpoint\n"
            "reachable and returns a valid server version.\n\n"
            "Examples:\n"
            "  bakufu auth test\n"
            "  bakufu auth test --account lab\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    auth_test_cmd.set_defaults(func=cmd_auth_test)

    # Backward-compatible aliases (pre gws-style command layout)
    auth_setup_legacy = subparsers.add_parser("auth-setup", help="Legacy alias for `auth setup`")
    auth_setup_legacy.add_argument("account_name")
    auth_setup_legacy.add_argument("--server")
    auth_setup_legacy.add_argument("--username")
    auth_setup_legacy.add_argument("--password", help="Password (omit to use secure interactive prompt — avoids shell history exposure)")
    auth_setup_legacy.add_argument("--default", action="store_true")
    auth_setup_legacy.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    auth_setup_legacy.set_defaults(func=cmd_auth_setup)

    auth_login_legacy = subparsers.add_parser("auth-login", help="Legacy alias for `auth login`")
    auth_login_legacy.add_argument("account_name")
    auth_login_legacy.add_argument("--server")
    auth_login_legacy.add_argument("--username")
    auth_login_legacy.add_argument("--password", help="Password (omit to use secure interactive prompt — avoids shell history exposure)")
    auth_login_legacy.add_argument("--default", action="store_true")
    auth_login_legacy.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    auth_login_legacy.set_defaults(func=cmd_auth_login)


def build_parser():
    parser = BakufuArgumentParser(prog="bakufu", description="bakufu-cli for Veeam B&R v13")
    parser.add_argument("--account", help="Use a named account from ~/.config/bakufu/accounts.json")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification for this command")

    subparsers = parser.add_subparsers(dest="command")
    _add_auth_parser(subparsers)

    call = subparsers.add_parser(
        "call",
        help="Raw API call to any VBR REST endpoint",
        description=(
            "Make a raw HTTP call to any Veeam Backup & Replication REST API path.\n\n"
            "Use this as an escape hatch when a specific endpoint is not yet covered\n"
            "by a named command. Authentication and base URL are handled automatically.\n\n"
            "Examples:\n"
            "  bakufu call /api/v1/jobs\n"
            "  bakufu call /api/v1/jobs --json\n"
            "  bakufu call /api/v1/jobs/<id> --method DELETE\n"
            "  bakufu call /api/v1/jobs --method POST --body '{\"name\": \"MyJob\"}'\n"
            "  bakufu call /api/v1/jobs --method POST --body @job.json\n"
            "  bakufu call /api/v1/jobs --params 'limit=100&skip=0'\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    call.add_argument("path", help="API path, e.g. /api/v1/jobs or /api/v1/jobs/<id>")
    call.add_argument("--method", default="GET",
                      help="HTTP method: GET, POST, PUT, PATCH, DELETE (default: GET)")
    call.add_argument("--params",
                      help="Query string parameters, e.g. 'limit=100&skip=0'")
    call.add_argument("--body",
                      help="Request body as a JSON string or @file path (e.g. @payload.json)")
    _add_output_flags(call)
    call.add_argument("--refresh", action="store_true",
                      help="Force a token refresh before the call")
    call.add_argument("--dry-run", action="store_true",
                      help="Print the curl command that would be executed without running it")
    call.set_defaults(func=cmd_call)

    services = subparsers.add_parser(
        "services",
        help="List available API service groups (swagger tags)",
        description=(
            "List the top-level service groups exposed by the VBR REST API.\n\n"
            "Each service group (tag) maps to a domain such as Jobs, Repositories,\n"
            "Sessions, Proxies, etc. Use these names with `bakufu operations` and\n"
            "`bakufu run` to discover and call individual operations.\n\n"
            "Examples:\n"
            "  bakufu services list\n"
            "  bakufu operations --tag Jobs\n"
            "  bakufu run Jobs GetAllJobs\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    services.set_defaults(func=lambda _args: services.print_help())
    services_sub = services.add_subparsers(dest="services_cmd")
    services_list = services_sub.add_parser("list", help="List all service groups")
    services_list.set_defaults(func=cmd_services_list)

    ops = subparsers.add_parser(
        "operations",
        help="List API operations, optionally filtered by service group",
        description=(
            "List all available VBR REST API operations from the swagger spec.\n\n"
            "Use --tag to filter to a specific service group. The operation IDs\n"
            "shown here are the values used with `bakufu run` and `bakufu schema`.\n\n"
            "Examples:\n"
            "  bakufu operations\n"
            "  bakufu operations --tag Jobs\n"
            "  bakufu operations --tag Repositories\n"
            "  bakufu run Jobs GetAllJobs\n"
            "  bakufu schema GetAllJobs\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ops.add_argument("--tag", help="Filter operations by service group (tag), e.g. Jobs, Repositories")
    ops.set_defaults(func=cmd_operations_list)

    run = subparsers.add_parser(
        "run",
        help="Run a VBR API operation by service group and operation ID",
        description=(
            "Execute any VBR REST API operation by its tag and operationId.\n\n"
            "Use `bakufu services list` to find tags and `bakufu operations --tag <tag>`\n"
            "to find operation IDs. Shorthand is also supported: bakufu <Tag> <OperationId>.\n\n"
            "Examples:\n"
            "  bakufu run Jobs GetAllJobs\n"
            "  bakufu run Jobs GetAllJobs --json\n"
            "  bakufu run Jobs StartJob --params 'jobId=<uuid>'\n"
            "  bakufu run Repositories GetRepository --params 'id=<uuid>'\n"
            "  bakufu run Jobs CreateJob --body @job.json\n"
            "  bakufu run Jobs GetAllJobs --page-all\n"
            "  bakufu Jobs GetAllJobs                   # shorthand\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run.add_argument("tag", help="Service group (tag), e.g. Jobs, Repositories, Sessions")
    run.add_argument("operation_id", help="Operation ID from `bakufu operations --tag <tag>`")
    run.add_argument("--params", help="Query string parameters, e.g. 'limit=100&skip=0'")
    run.add_argument("--body", help="Request body as JSON string or @file path")
    _add_output_flags(run)
    run.add_argument("--refresh", action="store_true", help="Force token refresh before the call")
    run.add_argument("--dry-run", action="store_true",
                     help="Print the curl command without executing it")
    run.add_argument("--page-all", action="store_true",
                     help="Auto-paginate and return all results (for list operations)")
    run.add_argument("--page-limit", type=int, default=200,
                     help="Items per page when paginating (default 200)")
    run.add_argument("--page-max", type=int, default=10,
                     help="Max number of pages to fetch when --page-all is used (default 10)")
    run.add_argument("--page-delay", type=int, default=100,
                     help="Delay between paginated requests in ms (default 100)")
    run.set_defaults(func=cmd_run)

    schema = subparsers.add_parser(
        "schema",
        help="Show request/response schema for an operation",
        description=(
            "Print the request body and response schema for any VBR API operation.\n\n"
            "Use this to understand what fields to pass in --body when calling an\n"
            "operation that requires a request payload.\n\n"
            "Examples:\n"
            "  bakufu schema CreateJob\n"
            "  bakufu schema GetAllJobs\n"
            "  bakufu schema CreateRepository --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    schema.add_argument("operation_id", help="Operation ID, e.g. CreateJob, GetAllJobs")
    _add_output_flags(schema)
    schema.set_defaults(func=cmd_schema)

    repos = subparsers.add_parser(
        "repos",
        help="List and inspect backup repositories",
        description=(
            "List all backup repositories, show a specific repository, or view capacity states.\n\n"
            "Examples:\n"
            "  bakufu repos list\n"
            "  bakufu repos list --filter 'type=ObjectStorage'\n"
            "  bakufu repos show <repo-uuid>\n"
            "  bakufu repos states\n"
            "  bakufu workflows repositoryHealthReview\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    repos.set_defaults(func=lambda _args: repos.print_help())
    repos_sub = repos.add_subparsers(dest="repos_cmd")
    repos_list = repos_sub.add_parser("list", help="List all repositories")
    _add_output_flags(repos_list)
    repos_list.add_argument("--filter", help="Client-side filter e.g. 'type=ObjectStorage' or 'name~=prod'")
    repos_list.add_argument("--refresh", action="store_true", help="Force token refresh")
    repos_list.add_argument("--dry-run", action="store_true", help="Print curl without executing")
    repos_list.set_defaults(func=cmd_repos_list)
    repos_show = repos_sub.add_parser("show", help="Show a repository by UUID")
    repos_show.add_argument("repo_id", help="Repository UUID")
    _add_output_flags(repos_show)
    repos_show.add_argument("--refresh", action="store_true")
    repos_show.add_argument("--dry-run", action="store_true")
    repos_show.set_defaults(func=cmd_repos_show)
    repos_states = repos_sub.add_parser("states", help="Show capacity and availability states for all repositories")
    _add_output_flags(repos_states)
    repos_states.add_argument("--filter", help="Client-side filter e.g. 'isUnavailable=true'")
    repos_states.add_argument("--refresh", action="store_true")
    repos_states.add_argument("--dry-run", action="store_true")
    repos_states.set_defaults(func=cmd_repos_states)

    proxies = subparsers.add_parser(
        "proxies",
        help="List backup proxies and their task slot states",
        description=(
            "List all backup proxies or view real-time task slot utilisation.\n\n"
            "Examples:\n"
            "  bakufu proxies list\n"
            "  bakufu proxies states\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    proxies.set_defaults(func=lambda _args: proxies.print_help())
    proxies_sub = proxies.add_subparsers(dest="proxies_cmd")
    proxies_list = proxies_sub.add_parser("list", help="List all backup proxies")
    _add_output_flags(proxies_list)
    proxies_list.add_argument("--filter", help="Client-side filter e.g. 'type=Vi'")
    proxies_list.add_argument("--refresh", action="store_true")
    proxies_list.add_argument("--dry-run", action="store_true")
    proxies_list.set_defaults(func=cmd_proxies_list)
    proxies_states = proxies_sub.add_parser("states", help="Show task slot utilisation for all proxies")
    _add_output_flags(proxies_states)
    proxies_states.add_argument("--refresh", action="store_true")
    proxies_states.add_argument("--dry-run", action="store_true")
    proxies_states.set_defaults(func=cmd_proxies_states)

    sobr = subparsers.add_parser(
        "sobr",
        help="List scale-out backup repositories",
        description=(
            "List all scale-out backup repositories (SOBRs) with performance and capacity tier details.\n\n"
            "Examples:\n"
            "  bakufu sobr list\n"
            "  bakufu sobr list --filter 'name~=prod'\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sobr.set_defaults(func=lambda _args: sobr.print_help())
    sobr_sub = sobr.add_subparsers(dest="sobr_cmd")
    sobr_list = sobr_sub.add_parser("list", help="List all scale-out repositories")
    _add_output_flags(sobr_list)
    sobr_list.add_argument("--filter", help="Client-side filter e.g. 'name~=prod'")
    sobr_list.add_argument("--refresh", action="store_true")
    sobr_list.add_argument("--dry-run", action="store_true")
    sobr_list.set_defaults(func=cmd_sobr_list)

    jobs = subparsers.add_parser(
        "jobs",
        help="Full job lifecycle — list, inspect, control, configure, and migrate jobs",
        description=(
            "Complete job management surface covering all VBR job lifecycle operations.\n\n"
            "Subcommands:\n"
            "  list            List all backup jobs (supports --filter)\n"
            "  show            Show full configuration for a specific job\n"
            "  states          List jobs with execution state and last-run details\n"
            "  start           Start a job\n"
            "  stop            Stop a running job\n"
            "  retry           Retry the last failed session for a job\n"
            "  enable          Re-enable a disabled job\n"
            "  disable         Disable a job from scheduled execution\n"
            "  delete          Delete a job (prompts unless --force)\n"
            "  clone           Clone an existing job\n"
            "  update          Full job config update via PUT (--spec JSON or @file)\n"
            "  quick-backup    Start a vSphere quick backup\n"
            "  export          Export jobs to a portable file\n"
            "  import          Import jobs from an export file\n"
            "  apply-policy    Apply agent backup policy configuration\n"
            "  clear-cache     Clear agent backup job cache\n\n"
            "Examples:\n"
            "  bakufu jobs list\n"
            "  bakufu jobs list --filter 'isDisabled=false'\n"
            "  bakufu jobs states --last-result-filter Failed\n"
            "  bakufu jobs show <uuid>\n"
            "  bakufu jobs start <uuid>\n"
            "  bakufu jobs stop <uuid>\n"
            "  bakufu jobs retry <uuid>\n"
            "  bakufu jobs disable <uuid>\n"
            "  bakufu jobs enable <uuid>\n"
            "  bakufu jobs clone <uuid> --name 'My Job Copy'\n"
            "  bakufu jobs update <uuid> --spec @job.json\n"
            "  bakufu jobs delete <uuid>\n"
            "  bakufu jobs export --job-ids <uuid1>,<uuid2>\n"
            "  bakufu jobs import jobs_export.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    jobs.set_defaults(func=lambda _args: jobs.print_help())
    jobs_sub = jobs.add_subparsers(dest="jobs_cmd")

    def _jobs_common(p):
        _add_output_flags(p)
        p.add_argument("--refresh", action="store_true", help="Force token refresh")
        p.add_argument("--dry-run", action="store_true", help="Print curl without executing")

    def _jobs_id_cmd(name, help_text, func, extra=None):
        p = jobs_sub.add_parser(name, help=help_text)
        p.add_argument("job_id", help="Job UUID")
        _jobs_common(p)
        if extra:
            extra(p)
        p.set_defaults(func=func)
        return p

    jobs_list = jobs_sub.add_parser("list", help="List all backup jobs")
    _jobs_common(jobs_list)
    jobs_list.add_argument("--filter", help="Client-side filter e.g. 'isDisabled=false' or 'name~=prod'")
    jobs_list.set_defaults(func=cmd_jobs_list)

    jobs_states = jobs_sub.add_parser("states", help="List jobs with execution state and last-run details")
    _jobs_common(jobs_states)
    jobs_states.add_argument("--limit", type=int, default=200, help="Max results (default 200)")
    jobs_states.add_argument("--name-filter", help="Filter by job name pattern")
    jobs_states.add_argument("--type-filter", help="Filter by job type e.g. VSphereBackup, WindowsAgentBackup")
    jobs_states.add_argument("--last-result-filter", help="Filter by last result: Success, Warning, Failed, None")
    jobs_states.add_argument("--status-filter", help="Filter by current status: Running, Inactive, Disabled")
    jobs_states.add_argument("--repo-id", help="Filter by repository UUID")
    jobs_states.add_argument("--last-run-after", help="Filter to jobs that ran after this ISO8601 timestamp")
    jobs_states.add_argument("--high-priority", action="store_true", help="Return high priority jobs only")
    jobs_states.add_argument("--filter", help="Client-side filter on the result set")
    jobs_states.set_defaults(func=cmd_jobs_states)

    _jobs_id_cmd("show", "Show full configuration for a job", cmd_jobs_show)
    _jobs_id_cmd("start", "Start a backup job", cmd_jobs_start)
    _jobs_id_cmd("stop", "Stop a running backup job", cmd_jobs_stop)
    _jobs_id_cmd("retry", "Retry the last failed session for a job", cmd_jobs_retry)
    _jobs_id_cmd("enable", "Re-enable a disabled job", cmd_jobs_enable)
    _jobs_id_cmd("disable", "Disable a job from scheduled execution", cmd_jobs_disable)

    def _add_delete_flags(p):
        p.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    _jobs_id_cmd("delete", "Delete a job (prompts for confirmation unless --force)", cmd_jobs_delete, _add_delete_flags)

    def _add_clone_flags(p):
        p.add_argument("--name", help="Name for the cloned job (optional — server assigns one if omitted)")
    _jobs_id_cmd("clone", "Clone an existing job", cmd_jobs_clone, _add_clone_flags)

    jobs_update = jobs_sub.add_parser("update", help="Full job config update via PUT (--spec JSON or @file)")
    jobs_update.add_argument("job_id", help="Job UUID")
    jobs_update.add_argument("--spec", required=True, help="Full job spec as JSON string or @file path")
    _jobs_common(jobs_update)
    jobs_update.set_defaults(func=cmd_jobs_update)

    jobs_qb = jobs_sub.add_parser("quick-backup", help="Start a vSphere quick backup")
    jobs_qb.add_argument("--spec", help="Quick backup spec as JSON or @file")
    _jobs_common(jobs_qb)
    jobs_qb.set_defaults(func=cmd_jobs_quick_backup)

    jobs_export = jobs_sub.add_parser("export", help="Export jobs to a portable JSON file")
    jobs_export.add_argument("--job-ids", help="Comma-separated job UUIDs to export (omit for all)")
    jobs_export.add_argument("--spec", help="Full export spec as JSON or @file (overrides --job-ids)")
    jobs_export.add_argument("--output-file", help="Write export to this file instead of stdout")
    _jobs_common(jobs_export)
    jobs_export.set_defaults(func=cmd_jobs_export)

    jobs_import = jobs_sub.add_parser("import", help="Import jobs from an export file")
    jobs_import.add_argument("import_file", help="Path to jobs export JSON file")
    _jobs_common(jobs_import)
    jobs_import.set_defaults(func=cmd_jobs_import)

    _jobs_id_cmd("apply-policy", "Apply agent backup policy configuration", cmd_jobs_apply_policy)
    _jobs_id_cmd("clear-cache", "Clear agent backup job cache", cmd_jobs_clear_cache)

    sessions = subparsers.add_parser(
        "sessions",
        help="List, inspect and view logs for backup sessions",
        description=(
            "List recent sessions, show a specific session's status, or view its log output.\n\n"
            "Examples:\n"
            "  bakufu sessions list\n"
            "  bakufu sessions list --result Failed\n"
            "  bakufu sessions list --job-id <uuid> --limit 20\n"
            "  bakufu sessions show <session-uuid>\n"
            "  bakufu sessions logs <session-uuid>\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sessions.set_defaults(func=lambda _args: sessions.print_help())
    sessions_sub = sessions.add_subparsers(dest="sessions_cmd")
    sessions_list = sessions_sub.add_parser("list", help="List recent sessions")
    _add_output_flags(sessions_list)
    sessions_list.add_argument("--limit", type=int, default=100,
                               help="Max number of sessions to return (default 100)")
    sessions_list.add_argument("--job-id", help="Filter by job UUID")
    sessions_list.add_argument("--state", help="Filter by state: Starting, Working, Stopped, etc.")
    sessions_list.add_argument("--result", help="Filter by result: Success, Warning, Failed, None")
    sessions_list.add_argument("--filter", help="Client-side filter e.g. 'result=Failed' or 'jobName~=prod'")
    sessions_list.add_argument("--refresh", action="store_true")
    sessions_list.add_argument("--dry-run", action="store_true")
    sessions_list.set_defaults(func=cmd_sessions_list)
    sessions_show = sessions_sub.add_parser("show", help="Show session status by UUID")
    sessions_show.add_argument("session_id", help="Session UUID")
    _add_output_flags(sessions_show)
    sessions_show.add_argument("--refresh", action="store_true", help="Force token refresh")
    sessions_show.add_argument("--dry-run", action="store_true", help="Print curl without executing")
    sessions_show.set_defaults(func=cmd_sessions_show)
    sessions_logs = sessions_sub.add_parser("logs", help="Show log entries for a session")
    sessions_logs.add_argument("session_id", help="Session UUID")
    _add_output_flags(sessions_logs)
    sessions_logs.add_argument("--refresh", action="store_true", help="Force token refresh")
    sessions_logs.add_argument("--dry-run", action="store_true", help="Print curl without executing")
    sessions_logs.set_defaults(func=cmd_sessions_logs)

    _workflow_choices = [k.replace("bakufu_workflows_", "") for k in WORKFLOWS]
    workflows = subparsers.add_parser("workflows", help="Curated multi-step workflows")
    workflows.add_argument("workflow_id", nargs="?", choices=_workflow_choices,
                           metavar="WORKFLOW")
    workflows.add_argument("--job-id", help="Job UUID (investigateFailedJob)")
    workflows.add_argument("--job-name", help="Exact job name (investigateFailedJob)")
    workflows.add_argument("--spec", help="JSON spec or @file (createWasabiRepo)")
    workflows.add_argument("--wait", action="store_true",
                           help="Wait for async completion (runSecurityAnalyzer)")
    workflows.add_argument("--interval-ms", type=int, default=2000,
                           help="Poll interval ms when --wait is used (default 2000)")
    workflows.add_argument("--timeout-ms", type=int, default=300000,
                           help="Max wait ms when --wait is used (default 300000)")
    workflows.add_argument("--describe", action="store_true",
                           help="Show full parameter schema for the workflow")
    _add_output_flags(workflows)
    workflows.set_defaults(func=cmd_workflow)

    _helper_choices = [k.replace("bakufu_", "") for k in HELPERS]
    helpers_cmd = subparsers.add_parser("helpers", help="Low-level focused helpers")
    helpers_cmd.add_argument("helper_id", nargs="?", choices=_helper_choices,
                             metavar="HELPER")
    helpers_cmd.add_argument("--name", help="Resource name (jobs_startByName)")
    helpers_cmd.add_argument("--job-id", help="Job UUID")
    helpers_cmd.add_argument("--session-id", help="Session UUID")
    helpers_cmd.add_argument("--server-id", help="Managed server UUID")
    helpers_cmd.add_argument("--spec", help="JSON spec or @file")
    helpers_cmd.add_argument("--schedule", help="Schedule JSON or @file (jobs_updateSchedule)")
    helpers_cmd.add_argument("--storage", help="Storage/retention JSON or @file (jobs_updateSchedule)")
    helpers_cmd.add_argument("--interval-ms", type=int, default=None,
                             help="Poll interval ms (sessions_follow, default 1000)")
    helpers_cmd.add_argument("--timeout-ms", type=int, default=None,
                             help="Max wait ms (sessions_follow, default 600000)")
    helpers_cmd.add_argument("--describe", action="store_true",
                             help="Show full parameter schema for the helper")
    _add_output_flags(helpers_cmd)
    helpers_cmd.set_defaults(func=cmd_helper)

    skills = subparsers.add_parser(
        "skills",
        help="Browse the skills library (helpers, recipes, personas)",
        description=(
            "Browse the full skills library — helpers, recipes, roles, and personas.\n\n"
            "Skills are the reference layer: each skill documents a task, the commands\n"
            "needed to complete it, prerequisites, and tips. They map directly to what\n"
            "an AI agent would execute via the MCP server.\n\n"
            "Examples:\n"
            "  bakufu skills list\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    skills.set_defaults(func=lambda _args: skills.print_help())
    skills_sub = skills.add_subparsers(dest="skills_cmd")
    skills_list = skills_sub.add_parser("list", help="Print the full skills index")
    skills_list.set_defaults(func=cmd_skills_list)

    mcp = subparsers.add_parser(
        "mcp",
        help="Start the MCP server for AI agent integration",
        description=(
            "Start bakufu as an MCP (Model Context Protocol) server over stdio.\n\n"
            "This allows AI agents (Claude, Cursor, etc.) to use bakufu as a tool\n"
            "server, calling VBR API operations, helpers, and workflows on your behalf.\n\n"
            "By default all services, helpers, and workflows are exposed. Use flags\n"
            "to restrict the surface area if needed.\n\n"
            "Examples:\n"
            "  bakufu mcp\n"
            "  bakufu mcp --services Jobs,Repositories\n"
            "  bakufu mcp --no-helpers\n"
            "  bakufu mcp --no-workflows\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mcp.add_argument("-s", "--services", default="all",
                     help="Comma-separated service groups to expose, or 'all' (default: all)")
    mcp.add_argument("-e", "--helpers", action="store_true", default=True,
                     help="Expose helper tools to the agent (default: on)")
    mcp.add_argument("--no-helpers", action="store_false", dest="helpers",
                     help="Disable helper tools")
    mcp.add_argument("-w", "--workflows", action="store_true", default=True,
                     help="Expose workflow tools to the agent (default: on)")
    mcp.add_argument("--no-workflows", action="store_false", dest="workflows",
                     help="Disable workflow tools")
    mcp.set_defaults(func=cmd_mcp)

    mcp_config = subparsers.add_parser(
        "mcp-config",
        help="Print MCP server config JSON for Claude Desktop, Cursor, and other AI tools",
        description=(
            "Generate a ready-to-paste MCP server configuration block.\n\n"
            "Paste the output into your AI tool's config file to connect it to your\n"
            "VBR server via bakufu.\n\n"
            "Examples:\n"
            "  bakufu mcp-config\n"
            "  bakufu mcp-config --account lab\n"
            "  bakufu mcp-config --services Jobs,Repositories\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mcp_config.add_argument("--services", default="all",
                            help="Limit exposed services, e.g. 'Jobs,Repositories' (default: all)")
    mcp_config.set_defaults(func=cmd_mcp_config)

    update_cmd = subparsers.add_parser(
        "update",
        help="Update bakufu to the latest release",
        description=(
            "Check for a newer release on GitHub and install it.\n\n"
            "Examples:\n"
            "  bakufu update           # check and install latest\n"
            "  bakufu update --check   # check only, do not install\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    update_cmd.add_argument("--check", action="store_true",
                            help="Check for update without installing")
    update_cmd.set_defaults(func=cmd_update)

    doctor_cmd = subparsers.add_parser(
        "doctor",
        help="Run connectivity and config diagnostics",
        description=(
            "Check the full bakufu setup: version, auth config, token state,\n"
            "API reachability, swagger spec, and data files.\n\n"
            "Examples:\n"
            "  bakufu doctor\n"
            "  bakufu doctor --account lab\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    doctor_cmd.set_defaults(func=cmd_doctor)

    license_cmd = subparsers.add_parser(
        "license",
        help="View and install the VBR license",
        description=(
            "Show the currently installed VBR license or install a new one from a .lic file.\n\n"
            "Examples:\n"
            "  bakufu license show\n"
            "  bakufu license show --json\n"
            "  bakufu license install-file /path/to/veeam.lic\n"
            "  bakufu license install-file /path/to/veeam.lic --force-standalone-mode\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    license_cmd.set_defaults(func=lambda _args: license_cmd.print_help())
    license_sub = license_cmd.add_subparsers(dest="license_cmd")
    license_show = license_sub.add_parser("show", help="Show installed license details")
    _add_output_flags(license_show)
    license_show.add_argument("--refresh", action="store_true", help="Force token refresh")
    license_show.add_argument("--dry-run", action="store_true", help="Print curl without executing")
    license_show.set_defaults(func=cmd_license_show)
    license_install = license_sub.add_parser("install-file",
                                             help="Install a VBR license from a local .lic file")
    license_install.add_argument("license_file", help="Path to the .lic file")
    license_install.add_argument("--force-standalone-mode", action="store_true",
                                 help="Force standalone (non-Enterprise Manager) mode")
    _add_output_flags(license_install)
    license_install.add_argument("--refresh", action="store_true", help="Force token refresh")
    license_install.add_argument("--dry-run", action="store_true", help="Print curl without executing")
    license_install.set_defaults(func=cmd_license_install_file)

    completion = subparsers.add_parser(
        "completion",
        help="Print shell completion script for bash or zsh",
        description=(
            "Print a shell completion script that enables tab-completion for bakufu.\n\n"
            "Examples:\n"
            "  bakufu completion zsh >> ~/.zshrc && source ~/.zshrc\n"
            "  bakufu completion bash >> ~/.bashrc && source ~/.bashrc\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    completion.add_argument("shell", choices=["bash", "zsh"],
                            help="Shell to generate completion for")
    completion.set_defaults(func=cmd_completion)

    getting_started = subparsers.add_parser(
        "getting-started",
        help="Quick-start guide, persona playbooks, and demo mode",
        description=(
            "Print a quick-start guide or role-specific onboarding playbook.\n\n"
            "Use --demo to run a set of read-only smoke checks against your VBR server.\n"
            "Use --persona to get a tailored command walkthrough for your role.\n\n"
            "Examples:\n"
            "  bakufu getting-started\n"
            "  bakufu getting-started --demo\n"
            "  bakufu getting-started --script\n"
            "  bakufu getting-started --persona backup-admin\n"
            "  bakufu getting-started --persona security-admin\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    getting_started.add_argument("--demo", action="store_true",
                                 help="Run read-only startup smoke checks against your VBR server")
    getting_started.add_argument("--script", action="store_true",
                                 help="Print a copy-paste demo script you can run yourself")
    getting_started.add_argument(
        "--persona",
        choices=["backup-admin", "backup-operator", "security-admin", "dr-operator", "auditor"],
        help="Print a tailored onboarding playbook for a specific role",
    )
    _add_output_flags(getting_started)
    getting_started.set_defaults(func=cmd_getting_started)

    version_cmd = subparsers.add_parser("version", help="Print the installed bakufu version")
    version_cmd.set_defaults(func=cmd_version)

    return parser


def _rewrite_shorthand(argv):
    if not argv:
        return argv
    if argv[0].startswith("-"):
        return argv
    known = {
        "auth", "auth-setup", "auth-login", "call", "services", "operations",
        "run", "schema", "jobs", "sessions", "repos", "proxies", "sobr",
        "workflows", "helpers", "skills", "mcp", "mcp-config",
        "license", "completion", "getting-started", "update", "doctor", "version",
        "-h", "--help",
    }
    first = argv[0]
    if first in known:
        return argv

    try:
        spec = SwaggerSpec.load()
    except Exception:
        return argv

    ops_all = spec.iter_operations()

    # Support: bakufu <Tag> <OperationId> [flags...]
    if len(argv) >= 2:
        maybe_tag = argv[0]
        maybe_operation = argv[1]
        tags = spec.list_tags()
        canonical_tag = next((t for t in tags if t.lower() == maybe_tag.lower()), None)
        if canonical_tag:
            match = next(
                (op for op in spec.operations_by_tag().get(canonical_tag, []) if op.operation_id.lower() == maybe_operation.lower()),
                None,
            )
            if match:
                return ["run", canonical_tag, match.operation_id] + argv[2:]
            tag_ops = [op.operation_id for op in spec.operations_by_tag().get(canonical_tag, [])]
            close = difflib.get_close_matches(maybe_operation, tag_ops, n=5, cutoff=0.5)
            hint = f"Use `bakufu operations --tag \"{canonical_tag}\"` to list valid operations."
            if close:
                hint = f"Did you mean `bakufu run {canonical_tag} {close[0]}`?"
            raise CliError(
                "OPERATION_NOT_FOUND_IN_TAG",
                f"Operation `{maybe_operation}` not found under tag `{canonical_tag}`.",
                hint=hint,
                details={"tag": canonical_tag, "suggestions": close},
            )

    # Support: bakufu <OperationId> [flags...], if unique across all tags
    if len(argv) >= 1:
        maybe_operation = argv[0]
        matches = [op for op in ops_all if op.operation_id.lower() == maybe_operation.lower()]
        if len(matches) == 1:
            op = matches[0]
            tag = op.tags[0] if op.tags else "untagged"
            return ["run", tag, op.operation_id] + argv[1:]
        if len(matches) > 1:
            expanded = []
            for op in matches:
                tag = op.tags[0] if op.tags else "untagged"
                expanded.append(f"{tag}.{op.operation_id}")
            raise CliError(
                "OPERATION_ID_AMBIGUOUS",
                f"OperationId `{maybe_operation}` is ambiguous across multiple tags.",
                hint="Use explicit form: `bakufu run <Tag> <OperationId>`.",
                details={"matches": expanded},
            )

        all_ids = [op.operation_id for op in ops_all]
        close_global = difflib.get_close_matches(maybe_operation, all_ids, n=3, cutoff=0.6)
        if close_global:
            hints = ", ".join(close_global)
            raise CliError(
                "OPERATION_ID_NOT_FOUND",
                f"OperationId `{maybe_operation}` not found.",
                hint=f"Closest matches: {hints}.",
                details={"suggestions": close_global},
            )

    return argv


def _hoist_global_flags(argv):
    if not argv:
        return argv
    account_value = None
    insecure = False
    remaining = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--account":
            if i + 1 < len(argv):
                account_value = argv[i + 1]
                i += 2
                continue
            remaining.append(token)
            i += 1
            continue
        if token.startswith("--account="):
            account_value = token.split("=", 1)[1]
            i += 1
            continue
        if token == "--insecure":
            insecure = True
            i += 1
            continue
        remaining.append(token)
        i += 1

    prefix = []
    if account_value:
        prefix.extend(["--account", account_value])
    if insecure:
        os.environ["BAKUFU_INSECURE"] = "1"
        prefix.append("--insecure")
    return prefix + remaining


def main():
    parser = build_parser()
    try:
        argv = _rewrite_shorthand(sys.argv[1:])
        argv = _hoist_global_flags(argv)
        args = parser.parse_args(argv)
        if getattr(args, "insecure", False):
            os.environ["BAKUFU_INSECURE"] = "1"
        if not hasattr(args, "func"):
            parser.print_help()
            sys.exit(1)
        args.func(args)
    except CliError as exc:
        payload = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "hint": exc.hint,
                "details": exc.details,
            }
        }
        print(json.dumps(payload, indent=2), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        hint = "Run `bakufu auth setup <account>` and verify server reachability."
        if "SSL certificate problem" in str(exc):
            hint = "TLS validation failed. Use a trusted certificate, or retry with `--insecure`."
        payload = {
            "error": {
                "code": "UNHANDLED_EXCEPTION",
                "message": str(exc),
                "hint": hint,
            }
        }
        print(json.dumps(payload, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
