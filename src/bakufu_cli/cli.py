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
    add_account(
        args.account_name,
        server,
        username,
        password,
        make_default=args.default,
        insecure=bool(args.insecure),
    )
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
    result = auth_setup(
        server,
        username,
        password,
        args.account_name,
        make_default=args.default,
        insecure=bool(args.insecure),
    )
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
    if not args.workflow_id:
        args._workflows_parser.print_help()
        return
    workflow_name = f"bakufu_workflows_{args.workflow_id}"
    if workflow_name not in WORKFLOWS:
        raise CliError("WORKFLOW_NOT_FOUND", f"Workflow not found: {args.workflow_id}")
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
    if getattr(args, "formatted", None) == "table":
        rendered = _render_table(result)
        if rendered:
            print(rendered)
            return
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, separators=(",", ":")))


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
  local top="auth auth-setup auth-login call services operations run schema jobs sessions workflows skills mcp license completion getting-started version"

  if [[ $COMP_CWORD -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "$top --account --insecure -h --help" -- "$cur") )
    return 0
  fi

  case "$cmd" in
    auth)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "setup login list default token" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--server --username --password --default --refresh --account --insecure -h --help" -- "$cur") )
      fi
      ;;
    jobs)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "list start" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--pretty --raw --formatted --refresh --dry-run -h --help" -- "$cur") )
      fi
      ;;
    sessions)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "show logs" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--pretty --raw --formatted --refresh --dry-run -h --help" -- "$cur") )
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
        COMPREPLY=( $(compgen -W "--params --json --pretty --raw --formatted --refresh --dry-run --page-all --page-limit --page-max --page-delay -h --help" -- "$cur") )
      fi
      ;;
    call) COMPREPLY=( $(compgen -W "--method --params --json --pretty --raw --formatted --refresh --dry-run --insecure -h --help" -- "$cur") ) ;;
    operations) COMPREPLY=( $(compgen -W "--tag -h --help" -- "$cur") ) ;;
    mcp) COMPREPLY=( $(compgen -W "-s --services -e --helpers -w --workflows --insecure -h --help" -- "$cur") ) ;;
    license)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "show install-file" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--pretty --raw --formatted --refresh --dry-run --force-standalone-mode -h --help" -- "$cur") )
      fi
      ;;
    completion) COMPREPLY=( $(compgen -W "bash zsh -h --help" -- "$cur") ) ;;
    getting-started) COMPREPLY=( $(compgen -W "--demo --script --persona --pretty --raw -h --help backup-admin backup-operator security-admin dr-operator auditor" -- "$cur") ) ;;
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
        jobs sessions workflows skills mcp license completion getting-started version
      ;;
    args)
      case $words[2] in
        auth) _values 'auth command' setup login list default token ;;
        jobs) _values 'jobs command' list start ;;
        sessions) _values 'sessions command' show logs ;;
        services) _values 'services command' list ;;
        skills) _values 'skills command' list ;;
        workflows) _values 'workflow' investigateFailedJob createWasabiRepo capacityReport runSecurityAnalyzer validateImmutability ;;
        mcp) _values 'options' -s --services -e --helpers -w --workflows --insecure ;;
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
            _values 'run options' --params --json --pretty --raw --formatted --refresh --dry-run --page-all --page-limit --page-max --page-delay --insecure
          fi
          ;;
        license) _values 'license command' show install-file ;;
        completion) _values 'shell' bash zsh ;;
        getting-started) _values 'options' --demo --script --persona --pretty --raw backup-admin backup-operator security-admin dr-operator auditor ;;
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
                "bakufu run Repositories GetAllRepositories --account demo-lab --formatted table",
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
                "bakufu run Jobs GetAllJobs --account demo-lab --formatted table",
                "bakufu workflows investigateFailedJob --job-name \"Demo Nightly Backup\" --account demo-lab",
                "bakufu run Sessions GetAllSessions --params '{\"limit\":20}' --account demo-lab --pretty",
                "bakufu sessions logs <session-id> --account demo-lab --pretty",
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
                "bakufu run Security GetBestPracticesComplianceResult --account demo-lab --pretty",
                "bakufu run Malware\\ Detection GetAllMalwareEvents --account demo-lab --pretty",
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
                "bakufu run Restore\\ Points GetAllRestorePoints --account demo-lab --pretty",
                "bakufu run Replicas GetAllReplicas --account demo-lab --pretty",
                "bakufu run Failover GetAllFailoverPlans --account demo-lab --pretty",
                "bakufu run Failback GetAllFailbackPlans --account demo-lab --pretty",
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
                "bakufu run Sessions GetAllSessions --params '{\"limit\":50}' --account demo-lab --pretty",
                "bakufu run Security GetAllAuthorizationEvents --account demo-lab --pretty",
                "bakufu license show --account demo-lab --pretty",
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
bakufu run Services GetAllServices --formatted table --account demo-lab

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
   bakufu run Services GetAllServices --formatted table --account demo-lab

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
            lambda: call_api("/api/v1/serverTime", pretty=True, account=args.account),
        ),
        (
            "service.info",
            "bakufu call /api/v1/serverInfo",
            "Read-only authenticated server information check.",
            lambda: call_api("/api/v1/serverInfo", pretty=True, account=args.account),
        ),
        (
            "license.show",
            "bakufu license show",
            "Read current license status and edition.",
            lambda: call_api("/api/v1/license", pretty=True, account=args.account),
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
    if not args.pretty:
        print(json.dumps(report, separators=(",", ":")))
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
        hint = "Install a valid VBR license first: `bakufu license install-file /path/to/license.lic --pretty`."
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
        if getattr(args, "formatted", None) == "table":
            try:
                parsed = json.loads(body) if body else None
            except json.JSONDecodeError:
                parsed = None
            rendered = _render_table(parsed)
            if rendered:
                print(f"HTTP {response['status']}", file=sys.stderr)
                print(rendered)
                return
        print(f"HTTP {response['status']}", file=sys.stderr)
        if body:
            print(body)
    else:
        print(response)


def _render_table(payload: Any) -> Optional[str]:
    rows = None
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        rows = payload.get("data")
    elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
        rows = payload.get("items")
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        rows = payload.get("results")
    elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        rows = payload.get("rows")
    elif isinstance(payload, list):
        rows = payload
    if not rows:
        return None
    if not all(isinstance(r, dict) for r in rows):
        return None

    keys = list(rows[0].keys())[:8]
    if not keys:
        return None
    values = []
    for row in rows:
        vals = []
        for key in keys:
            value = row.get(key)
            if isinstance(value, (dict, list)):
                vals.append(json.dumps(value, separators=(",", ":")))
            else:
                vals.append("" if value is None else str(value))
        values.append(vals)

    widths = [len(k) for k in keys]
    for vals in values:
        for i, v in enumerate(vals):
            widths[i] = min(max(widths[i], len(v)), 80)

    def _clip(s: str, w: int) -> str:
        return s if len(s) <= w else s[: w - 1] + "…"

    header = " | ".join(_clip(k, widths[i]).ljust(widths[i]) for i, k in enumerate(keys))
    sep = "-+-".join("-" * widths[i] for i in range(len(keys)))
    body = []
    for vals in values:
        body.append(" | ".join(_clip(v, widths[i]).ljust(widths[i]) for i, v in enumerate(vals)))
    return "\n".join([header, sep] + body)


def _add_output_flags(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pretty", dest="pretty", action="store_true", help="Pretty-print JSON output (default)")
    group.add_argument("--raw", dest="pretty", action="store_false", help="Emit compact/raw JSON output")
    parser.set_defaults(pretty=True)
    parser.add_argument("--formatted", choices=["table"], help="Render response in friendly table format when possible")


def _add_auth_parser(subparsers):
    auth = subparsers.add_parser("auth", help="Authentication commands")
    auth.set_defaults(func=lambda _args: auth.print_help())
    auth_sub = auth.add_subparsers(dest="auth_cmd")

    auth_setup_cmd = auth_sub.add_parser("setup", help="Guided setup and validation")
    auth_setup_cmd.add_argument("account_name")
    auth_setup_cmd.add_argument("--server")
    auth_setup_cmd.add_argument("--username")
    auth_setup_cmd.add_argument("--password")
    auth_setup_cmd.add_argument("--default", action="store_true")
    auth_setup_cmd.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    auth_setup_cmd.set_defaults(func=cmd_auth_setup)

    auth_login = auth_sub.add_parser("login", help="Add account without setup checks")
    auth_login.add_argument("account_name")
    auth_login.add_argument("--server")
    auth_login.add_argument("--username")
    auth_login.add_argument("--password")
    auth_login.add_argument("--default", action="store_true")
    auth_login.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
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
    auth_setup_legacy.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    auth_setup_legacy.set_defaults(func=cmd_auth_setup)

    auth_login_legacy = subparsers.add_parser("auth-login", help="Legacy alias for `auth login`")
    auth_login_legacy.add_argument("account_name")
    auth_login_legacy.add_argument("--server")
    auth_login_legacy.add_argument("--username")
    auth_login_legacy.add_argument("--password")
    auth_login_legacy.add_argument("--default", action="store_true")
    auth_login_legacy.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    auth_login_legacy.set_defaults(func=cmd_auth_login)


def build_parser():
    parser = BakufuArgumentParser(prog="bakufu", description="bakufu-cli for Veeam B&R v13")
    parser.add_argument("--account", help="Use a named account from ~/.config/bakufu/accounts.json")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification for this command")

    subparsers = parser.add_subparsers(dest="command")
    _add_auth_parser(subparsers)

    call = subparsers.add_parser("call", help="Call an API path directly")
    call.add_argument("path")
    call.add_argument("--method", default="GET")
    call.add_argument("--params")
    call.add_argument("--json")
    _add_output_flags(call)
    call.add_argument("--refresh", action="store_true")
    call.add_argument("--dry-run", action="store_true")
    call.set_defaults(func=cmd_call)

    services = subparsers.add_parser("services", help="Swagger services (tags)")
    services.set_defaults(func=lambda _args: services.print_help())
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
    _add_output_flags(run)
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
    jobs.set_defaults(func=lambda _args: jobs.print_help())
    jobs_sub = jobs.add_subparsers(dest="jobs_cmd")
    jobs_list = jobs_sub.add_parser("list", help="List jobs")
    _add_output_flags(jobs_list)
    jobs_list.add_argument("--refresh", action="store_true")
    jobs_list.add_argument("--dry-run", action="store_true")
    jobs_list.set_defaults(func=cmd_jobs_list)
    jobs_start = jobs_sub.add_parser("start", help="Start a job by id")
    jobs_start.add_argument("job_id")
    _add_output_flags(jobs_start)
    jobs_start.add_argument("--refresh", action="store_true")
    jobs_start.add_argument("--dry-run", action="store_true")
    jobs_start.set_defaults(func=cmd_jobs_start)

    sessions = subparsers.add_parser("sessions", help="Session operations")
    sessions.set_defaults(func=lambda _args: sessions.print_help())
    sessions_sub = sessions.add_subparsers(dest="sessions_cmd")
    sessions_show = sessions_sub.add_parser("show", help="Show a session")
    sessions_show.add_argument("session_id")
    _add_output_flags(sessions_show)
    sessions_show.add_argument("--refresh", action="store_true")
    sessions_show.add_argument("--dry-run", action="store_true")
    sessions_show.set_defaults(func=cmd_sessions_show)
    sessions_logs = sessions_sub.add_parser("logs", help="Show session logs")
    sessions_logs.add_argument("session_id")
    _add_output_flags(sessions_logs)
    sessions_logs.add_argument("--refresh", action="store_true")
    sessions_logs.add_argument("--dry-run", action="store_true")
    sessions_logs.set_defaults(func=cmd_sessions_logs)

    workflows = subparsers.add_parser("workflows", help="Curated recipes")
    workflows.add_argument(
        "workflow_id",
        nargs="?",
        choices=[
            "investigateFailedJob",
            "createWasabiRepo",
            "capacityReport",
            "runSecurityAnalyzer",
            "validateImmutability",
        ],
    )
    workflows.add_argument("--job-id")
    workflows.add_argument("--job-name")
    workflows.add_argument("--spec", help="JSON spec or @file")
    workflows.add_argument("--wait", action="store_true", help="Wait for workflow completion (where supported)")
    workflows.add_argument("--interval-ms", type=int, default=2000, help="Poll interval when --wait is used")
    workflows.add_argument("--timeout-ms", type=int, default=300000, help="Max wait time when --wait is used")
    _add_output_flags(workflows)
    workflows.set_defaults(func=cmd_workflow, _workflows_parser=workflows)

    skills = subparsers.add_parser("skills", help="Skills library")
    skills.set_defaults(func=lambda _args: skills.print_help())
    skills_sub = skills.add_subparsers(dest="skills_cmd")
    skills_list = skills_sub.add_parser("list", help="List skills")
    skills_list.set_defaults(func=cmd_skills_list)

    mcp = subparsers.add_parser("mcp", help="Start MCP server over stdio")
    mcp.add_argument("-s", "--services", help="Comma-separated services to expose, or 'all'", default="all")
    mcp.add_argument("-e", "--helpers", action="store_true", help="Expose helper tools")
    mcp.add_argument("-w", "--workflows", action="store_true", help="Expose workflow tools")
    mcp.set_defaults(func=cmd_mcp)

    license_cmd = subparsers.add_parser("license", help="License operations")
    license_cmd.set_defaults(func=lambda _args: license_cmd.print_help())
    license_sub = license_cmd.add_subparsers(dest="license_cmd")
    license_show = license_sub.add_parser("show", help="Show installed license details")
    _add_output_flags(license_show)
    license_show.add_argument("--refresh", action="store_true")
    license_show.add_argument("--dry-run", action="store_true")
    license_show.set_defaults(func=cmd_license_show)
    license_install = license_sub.add_parser("install-file", help="Install license from local .lic file")
    license_install.add_argument("license_file", help="Path to .lic file")
    license_install.add_argument("--force-standalone-mode", action="store_true")
    _add_output_flags(license_install)
    license_install.add_argument("--refresh", action="store_true")
    license_install.add_argument("--dry-run", action="store_true")
    license_install.set_defaults(func=cmd_license_install_file)

    completion = subparsers.add_parser("completion", help="Print shell completion script")
    completion.add_argument("shell", choices=["bash", "zsh"])
    completion.set_defaults(func=cmd_completion)

    getting_started = subparsers.add_parser("getting-started", help="Show quick-start guide and optional read-only demo")
    getting_started.add_argument("--demo", action="store_true", help="Run read-only startup smoke checks")
    getting_started.add_argument("--script", action="store_true", help="Print a copy-paste demo script")
    getting_started.add_argument(
        "--persona",
        choices=["backup-admin", "backup-operator", "security-admin", "dr-operator", "auditor"],
        help="Print detailed onboarding for a specific backup persona",
    )
    group = getting_started.add_mutually_exclusive_group()
    group.add_argument("--pretty", dest="pretty", action="store_true", help="Pretty JSON output (default)")
    group.add_argument("--raw", dest="pretty", action="store_false", help="Compact JSON output")
    getting_started.set_defaults(pretty=True, func=cmd_getting_started)

    version_cmd = subparsers.add_parser("version", help="Print CLI version")
    version_cmd.set_defaults(func=cmd_version)

    return parser


def _rewrite_shorthand(argv):
    if not argv:
        return argv
    if argv[0].startswith("-"):
        return argv
    known = {
        "auth", "auth-setup", "auth-login", "call", "services", "operations",
        "run", "schema", "jobs", "sessions", "workflows", "skills", "mcp",
        "license", "completion", "getting-started", "version", "-h", "--help",
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
