import argparse
import base64
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .api import call_api, call_api_paginated
from .token import ensure_token
from .swagger import SwaggerSpec
from .accounts import add_account, list_accounts, set_default
from .mcp_server import serve
from .mcp_helpers import run_workflow, WORKFLOWS
from .auth_setup import setup as auth_setup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_SKILLS_PATH = PROJECT_ROOT / "docs" / "skills.md"


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
    try:
        ensure_token(force_refresh=args.refresh, account=args.account)
    except Exception as exc:
        raise CliError(
            "AUTH_TOKEN_FAILED",
            str(exc),
            hint="Run `bakufu auth setup <account>` and verify network/DNS.",
        )
    print("OK")


def cmd_auth_login(args):
    server = args.server
    username = args.username
    password = args.password
    if not server:
        server = input("Server URL: ").strip()
    if not username:
        username = input("Username: ").strip()
    if not password:
        import getpass

        password = getpass.getpass("Password: ")
    if not server or not username or not password:
        raise CliError("AUTH_INPUT_INVALID", "Missing server/username/password")
    add_account(args.account_name, server, username, password, make_default=args.default)
    print("OK")


def cmd_auth_setup(args):
    server = args.server
    username = args.username
    password = args.password
    if not server:
        server = input("Server URL: ").strip()
    if not username:
        username = input("Username: ").strip()
    if not password:
        import getpass

        password = getpass.getpass("Password: ")
    if not server or not username or not password:
        raise CliError("AUTH_INPUT_INVALID", "Missing server/username/password")
    result = auth_setup(server, username, password, args.account_name, make_default=args.default)
    print(json.dumps(result, indent=2))


def cmd_auth_list(_args):
    data = list_accounts()
    print(json.dumps(data, indent=2))


def cmd_auth_default(args):
    set_default(args.account_name)
    print("OK")


def cmd_call(args):
    params = _parse_json_arg(args.params) or {}
    data = _parse_json_arg(args.json)
    response = call_api(
        args.path,
        method=args.method,
        params=params,
        data=data,
        pretty=args.pretty,
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
    data = _parse_json_arg(args.json)

    if args.page_all:
        pages = call_api_paginated(
            op.path,
            params=params,
            limit=args.page_limit,
            max_pages=args.page_max,
            page_delay_ms=args.page_delay,
            method=op.method,
            data=data,
            pretty=args.pretty,
            refresh=args.refresh,
            dry_run=args.dry_run,
            account=args.account,
        )
        if args.dry_run:
            print(json.dumps(pages, indent=2))
            return
        for page in pages:
            print(json.dumps(page))
        return

    response = call_api(
        op.path,
        method=op.method,
        params=params,
        data=data,
        pretty=args.pretty,
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
    print(json.dumps(result, indent=2))


def cmd_jobs_list(args):
    response = call_api("/api/v1/jobs", pretty=args.pretty, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_jobs_start(args):
    path = f"/api/v1/jobs/{args.job_id}/start"
    response = call_api(path, method="POST", data={}, pretty=args.pretty, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_sessions_show(args):
    path = f"/api/v1/sessions/{args.session_id}"
    response = call_api(path, pretty=args.pretty, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_sessions_logs(args):
    path = f"/api/v1/sessions/{args.session_id}/logs"
    response = call_api(path, pretty=args.pretty, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
    _print_response(response, args)


def cmd_license_show(args):
    response = call_api("/api/v1/license", pretty=args.pretty, refresh=args.refresh, dry_run=args.dry_run, account=args.account)
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
        pretty=args.pretty,
        refresh=args.refresh,
        dry_run=args.dry_run,
        account=args.account,
    )
    _print_response(response, args)


def cmd_skills_list(_args):
    print(DOCS_SKILLS_PATH.read_text())


def cmd_workflow(args):
    workflow_name = f"bakufu.workflows.{args.workflow_id}"
    if workflow_name not in WORKFLOWS:
        raise CliError("WORKFLOW_NOT_FOUND", f"Workflow not found: {args.workflow_id}")
    payload: Dict[str, Any] = {"account": args.account}
    if args.job_id:
        payload["jobId"] = args.job_id
    if args.job_name:
        payload["jobName"] = args.job_name
    if args.spec:
        payload["repoSpec"] = _parse_json_arg(args.spec)
    result = run_workflow(workflow_name, payload)
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
  local top="auth auth-setup auth-login call services operations run schema jobs sessions workflows skills mcp license completion"

  if [[ $COMP_CWORD -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "$top --account -h --help" -- "$cur") )
    return 0
  fi

  case "$cmd" in
    auth)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "setup login list default token" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--server --username --password --default --refresh --account -h --help" -- "$cur") )
      fi
      ;;
    jobs)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "list start" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--pretty --refresh --dry-run -h --help" -- "$cur") )
      fi
      ;;
    sessions)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "show logs" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--pretty --refresh --dry-run -h --help" -- "$cur") )
      fi
      ;;
    services) COMPREPLY=( $(compgen -W "list -h --help" -- "$cur") ) ;;
    skills) COMPREPLY=( $(compgen -W "list -h --help" -- "$cur") ) ;;
    workflows)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "investigateFailedJob createWasabiRepo capacityReport runSecurityAnalyzer validateImmutability" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--job-id --job-name --spec -h --help" -- "$cur") )
      fi
      ;;
    run) COMPREPLY=( $(compgen -W "--params --json --pretty --refresh --dry-run --page-all --page-limit --page-max --page-delay -h --help" -- "$cur") ) ;;
    call) COMPREPLY=( $(compgen -W "--method --params --json --pretty --refresh --dry-run -h --help" -- "$cur") ) ;;
    operations) COMPREPLY=( $(compgen -W "--tag -h --help" -- "$cur") ) ;;
    mcp) COMPREPLY=( $(compgen -W "--services --helpers --workflows -h --help" -- "$cur") ) ;;
    license)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "show install-file" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--pretty --refresh --dry-run --force-standalone-mode -h --help" -- "$cur") )
      fi
      ;;
    completion) COMPREPLY=( $(compgen -W "bash zsh -h --help" -- "$cur") ) ;;
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
    '1:command:->cmds' \
    '*::arg:->args'

  case $state in
    cmds)
      _values 'command' \
        auth auth-setup auth-login call services operations run schema \
        jobs sessions workflows skills mcp license completion
      ;;
    args)
      case $words[2] in
        auth) _values 'auth command' setup login list default token ;;
        jobs) _values 'jobs command' list start ;;
        sessions) _values 'sessions command' show logs ;;
        services) _values 'services command' list ;;
        skills) _values 'skills command' list ;;
        workflows) _values 'workflow' investigateFailedJob createWasabiRepo capacityReport runSecurityAnalyzer validateImmutability ;;
        license) _values 'license command' show install-file ;;
        completion) _values 'shell' bash zsh ;;
      esac
      ;;
  esac
}
_bakufu "$@"
"""


def cmd_completion(args):
    if args.shell == "bash":
        print(_completion_script_bash())
        return
    if args.shell == "zsh":
        print(_completion_script_zsh())
        return
    raise CliError("COMPLETION_SHELL_UNSUPPORTED", f"Unsupported shell: {args.shell}")


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
        hint = "Install a valid VBR license first: `bakufu license install-file /path/to/license.lic --pretty`."

    raise CliError(error_code, message, hint=hint, details=details)


def _print_response(response, args):
    if args.dry_run:
        print(json.dumps({"curl": response["cmd"]}, indent=2))
        return
    if isinstance(response, dict) and "status" in response:
        _raise_for_http_error(response)
        print(f"HTTP {response['status']}", file=sys.stderr)
        if response.get("body"):
            print(response["body"])
    else:
        print(response)


def _add_auth_parser(subparsers):
    auth = subparsers.add_parser("auth", help="Authentication commands")
    auth.set_defaults(func=cmd_auth_token, refresh=False, account=None)
    auth_sub = auth.add_subparsers(dest="auth_cmd")

    auth_setup_cmd = auth_sub.add_parser("setup", help="Guided setup and validation")
    auth_setup_cmd.add_argument("account_name")
    auth_setup_cmd.add_argument("--server")
    auth_setup_cmd.add_argument("--username")
    auth_setup_cmd.add_argument("--password")
    auth_setup_cmd.add_argument("--default", action="store_true")
    auth_setup_cmd.set_defaults(func=cmd_auth_setup)

    auth_login = auth_sub.add_parser("login", help="Add account without setup checks")
    auth_login.add_argument("account_name")
    auth_login.add_argument("--server")
    auth_login.add_argument("--username")
    auth_login.add_argument("--password")
    auth_login.add_argument("--default", action="store_true")
    auth_login.set_defaults(func=cmd_auth_login)

    auth_list = auth_sub.add_parser("list", help="List configured accounts")
    auth_list.set_defaults(func=cmd_auth_list)

    auth_default = auth_sub.add_parser("default", help="Set default account")
    auth_default.add_argument("account_name")
    auth_default.set_defaults(func=cmd_auth_default)

    auth_token = auth_sub.add_parser("token", help="Refresh/validate token for account")
    auth_token.add_argument("--refresh", action="store_true", help="Force token refresh")
    auth_token.add_argument("--account", help="Use a named account")
    auth_token.set_defaults(func=cmd_auth_token)

    # Backward-compatible aliases (pre gws-style command layout)
    auth_setup_legacy = subparsers.add_parser("auth-setup", help="Legacy alias for `auth setup`")
    auth_setup_legacy.add_argument("account_name")
    auth_setup_legacy.add_argument("--server")
    auth_setup_legacy.add_argument("--username")
    auth_setup_legacy.add_argument("--password")
    auth_setup_legacy.add_argument("--default", action="store_true")
    auth_setup_legacy.set_defaults(func=cmd_auth_setup)

    auth_login_legacy = subparsers.add_parser("auth-login", help="Legacy alias for `auth login`")
    auth_login_legacy.add_argument("account_name")
    auth_login_legacy.add_argument("--server")
    auth_login_legacy.add_argument("--username")
    auth_login_legacy.add_argument("--password")
    auth_login_legacy.add_argument("--default", action="store_true")
    auth_login_legacy.set_defaults(func=cmd_auth_login)


def build_parser():
    parser = BakufuArgumentParser(prog="bakufu", description="bakufu-cli for Veeam B&R v13")
    parser.add_argument("--account", help="Use a named account from ~/.config/bakufu/accounts.json")

    subparsers = parser.add_subparsers(dest="command")
    _add_auth_parser(subparsers)

    call = subparsers.add_parser("call", help="Call an API path directly")
    call.add_argument("path")
    call.add_argument("--method", default="GET")
    call.add_argument("--params")
    call.add_argument("--json")
    call.add_argument("--pretty", action="store_true")
    call.add_argument("--refresh", action="store_true")
    call.add_argument("--dry-run", action="store_true")
    call.set_defaults(func=cmd_call)

    services = subparsers.add_parser("services", help="Swagger services (tags)")
    services_sub = services.add_subparsers(dest="services_cmd")
    services_list = services_sub.add_parser("list", help="List services")
    services_list.set_defaults(func=cmd_services_list)

    ops = subparsers.add_parser("operations", help="Swagger operations")
    ops.add_argument("--tag", help="Filter by tag")
    ops.set_defaults(func=cmd_operations_list)

    run = subparsers.add_parser("run", help="Run a Swagger operation by tag and id")
    run.add_argument("tag")
    run.add_argument("operation_id")
    run.add_argument("--params")
    run.add_argument("--json")
    run.add_argument("--pretty", action="store_true")
    run.add_argument("--refresh", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--page-all", action="store_true")
    run.add_argument("--page-limit", type=int, default=200)
    run.add_argument("--page-max", type=int, default=10)
    run.add_argument("--page-delay", type=int, default=100)
    run.set_defaults(func=cmd_run)

    schema = subparsers.add_parser("schema", help="Show request/response schema for operationId")
    schema.add_argument("operation_id")
    schema.set_defaults(func=cmd_schema)

    jobs = subparsers.add_parser("jobs", help="Job operations")
    jobs_sub = jobs.add_subparsers(dest="jobs_cmd")
    jobs_list = jobs_sub.add_parser("list", help="List jobs")
    jobs_list.add_argument("--pretty", action="store_true")
    jobs_list.add_argument("--refresh", action="store_true")
    jobs_list.add_argument("--dry-run", action="store_true")
    jobs_list.set_defaults(func=cmd_jobs_list)
    jobs_start = jobs_sub.add_parser("start", help="Start a job by id")
    jobs_start.add_argument("job_id")
    jobs_start.add_argument("--pretty", action="store_true")
    jobs_start.add_argument("--refresh", action="store_true")
    jobs_start.add_argument("--dry-run", action="store_true")
    jobs_start.set_defaults(func=cmd_jobs_start)

    sessions = subparsers.add_parser("sessions", help="Session operations")
    sessions_sub = sessions.add_subparsers(dest="sessions_cmd")
    sessions_show = sessions_sub.add_parser("show", help="Show a session")
    sessions_show.add_argument("session_id")
    sessions_show.add_argument("--pretty", action="store_true")
    sessions_show.add_argument("--refresh", action="store_true")
    sessions_show.add_argument("--dry-run", action="store_true")
    sessions_show.set_defaults(func=cmd_sessions_show)
    sessions_logs = sessions_sub.add_parser("logs", help="Show session logs")
    sessions_logs.add_argument("session_id")
    sessions_logs.add_argument("--pretty", action="store_true")
    sessions_logs.add_argument("--refresh", action="store_true")
    sessions_logs.add_argument("--dry-run", action="store_true")
    sessions_logs.set_defaults(func=cmd_sessions_logs)

    workflows = subparsers.add_parser("workflows", help="Curated recipes")
    workflows.add_argument("workflow_id", choices=[
        "investigateFailedJob",
        "createWasabiRepo",
        "capacityReport",
        "runSecurityAnalyzer",
        "validateImmutability",
    ])
    workflows.add_argument("--job-id")
    workflows.add_argument("--job-name")
    workflows.add_argument("--spec", help="JSON spec or @file")
    workflows.set_defaults(func=cmd_workflow)

    skills = subparsers.add_parser("skills", help="Skills library")
    skills_sub = skills.add_subparsers(dest="skills_cmd")
    skills_list = skills_sub.add_parser("list", help="List skills")
    skills_list.set_defaults(func=cmd_skills_list)

    mcp = subparsers.add_parser("mcp", help="Start MCP server over stdio")
    mcp.add_argument("--services", help="Comma-separated services to expose, or 'all'", default="all")
    mcp.add_argument("--helpers", action="store_true")
    mcp.add_argument("--workflows", action="store_true")
    mcp.set_defaults(func=cmd_mcp)

    license_cmd = subparsers.add_parser("license", help="License operations")
    license_sub = license_cmd.add_subparsers(dest="license_cmd")
    license_show = license_sub.add_parser("show", help="Show installed license details")
    license_show.add_argument("--pretty", action="store_true")
    license_show.add_argument("--refresh", action="store_true")
    license_show.add_argument("--dry-run", action="store_true")
    license_show.set_defaults(func=cmd_license_show)
    license_install = license_sub.add_parser("install-file", help="Install license from local .lic file")
    license_install.add_argument("license_file", help="Path to .lic file")
    license_install.add_argument("--force-standalone-mode", action="store_true")
    license_install.add_argument("--pretty", action="store_true")
    license_install.add_argument("--refresh", action="store_true")
    license_install.add_argument("--dry-run", action="store_true")
    license_install.set_defaults(func=cmd_license_install_file)

    completion = subparsers.add_parser("completion", help="Print shell completion script")
    completion.add_argument("shell", choices=["bash", "zsh"])
    completion.set_defaults(func=cmd_completion)

    return parser


def _rewrite_shorthand(argv):
    if not argv:
        return argv
    known = {
        "auth", "auth-setup", "auth-login", "call", "services", "operations",
        "run", "schema", "jobs", "sessions", "workflows", "skills", "mcp",
        "license", "completion", "-h", "--help",
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


def main():
    parser = build_parser()
    try:
        argv = _rewrite_shorthand(sys.argv[1:])
        args = parser.parse_args(argv)
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
        payload = {
            "error": {
                "code": "UNHANDLED_EXCEPTION",
                "message": str(exc),
                "hint": "Run `bakufu auth setup <account>` and verify server reachability.",
            }
        }
        print(json.dumps(payload, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
