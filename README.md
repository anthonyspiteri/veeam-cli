# bakufu-cli

One CLI for Veeam Backup & Replication v13 — built for humans and AI agents.  
Swagger-driven operations, structured JSON output, MCP server mode, multi-account auth, and curated backup workflows.

> Note  
> This is a community project and is not an officially supported Veeam product.

> Important  
> This project is under active development. Expect changes as it evolves.

## Contents

- Prerequisites
- Installation
- Quick Start
- Why bakufu?
- Authentication
- AI Agent Skills
- MCP Server
- Advanced Usage
- Environment Variables
- Architecture
- Troubleshooting
- Development

## Prerequisites

- Python `3.9+`
- `curl` available in `PATH`
- Access to a Veeam Backup & Replication v13 REST API endpoint
- Local Swagger schema JSON in `schemas/` (or `swagger_v1.3.json`)

## Installation

For OS-specific copy-paste commands, see `docs/INSTALL.md`.

```bash
git clone <your-repo-url>
cd veeam-api-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Quick Start

```bash
bakufu auth setup lab --default
bakufu auth token --refresh
bakufu jobs list --pretty
bakufu license show --pretty
```

Run any Swagger operation dynamically:

```bash
bakufu services list
bakufu operations --tag Jobs
bakufu run Jobs GetAllJobs --pretty
```

## Why bakufu?

For humans:
- Avoid hand-written `curl` calls for common operations.
- Discover available services and operations from Swagger.
- Use `--dry-run` for request preview and `--page-all` for auto-pagination.

For AI agents:
- Consistent JSON output for command and MCP tool calls.
- Helper tools and workflows reduce orchestration boilerplate.
- Persona/recipe skill library for backup-specific tasks.

## Authentication

The CLI supports account-based auth, env-based auth, and file-based auth.

Interactive setup and validation:

```bash
bakufu auth setup lab --default
```

Direct account add:

```bash
bakufu auth login lab \
  --server "https://your-vbr:9419" \
  --username "veeamadmin" \
  --password 'your-password' \
  --default
```

Account management:

```bash
bakufu auth list
bakufu auth default lab
bakufu auth token --refresh
bakufu --account lab jobs list --pretty
```

Credential storage:
- Account metadata: `~/.config/bakufu/accounts.json` (or `BAKUFU_HOME` override)
- Passwords: OS keyring (`keyring` Python package)
- Legacy fallback: `.bakufu/accounts.json` and `.bakufu/token*.json` are still read

## AI Agent Skills

The repo ships a generated skills library:
- Service skills (from Swagger tags)
- Helper skills
- Persona skills
- Recipe skills

Skills index:
- `docs/skills.md`
- `docs/SKILL_CONVENTIONS.md`

Regenerate skills from latest local schema:

```bash
python scripts/sync_skills_from_swagger.py
```

List skills in CLI:

```bash
bakufu skills list
```

## MCP Server

`bakufu mcp` runs a stdio MCP server (Content-Length framed JSON-RPC), compatible with clients like Claude Desktop.

```bash
bakufu mcp --services Jobs,Sessions --helpers --workflows
```

Claude Desktop config example:

```json
{
  "mcpServers": {
    "bakufu": {
      "command": "bakufu",
      "args": ["mcp", "--services", "Jobs,Sessions", "--helpers", "--workflows"]
    }
  }
}
```

Flags:
- `--services <list|all>`: Comma-separated Swagger tags, or `all`
- `--helpers`: Expose helper tools
- `--workflows`: Expose workflow tools

## Advanced Usage

Direct API path call:

```bash
bakufu call /api/v1/serverInfo --pretty
```

Dry-run request preview:

```bash
bakufu run Jobs GetAllJobs --params '{"limit": 5}' --dry-run
```

Pagination (NDJSON one page per line):

```bash
bakufu run Sessions GetAllSessions \
  --params '{"limit": 100}' \
  --page-all --page-limit 100 --page-max 10 --page-delay 100
```

Schema introspection by operationId:

```bash
bakufu schema GetAllJobs
```

Built-in workflows:

```bash
bakufu workflows investigateFailedJob --job-name "Daily Backup"
bakufu workflows createWasabiRepo --spec @wasabi_repo.json
bakufu workflows capacityReport
bakufu workflows runSecurityAnalyzer
bakufu workflows validateImmutability
```

One-line license install from local `.lic` file:

```bash
bakufu license install-file /absolute/path/to/license.lic --pretty
```

Shell completion:

```bash
# bash
bakufu completion bash > ~/.bakufu-completion.bash
echo 'source ~/.bakufu-completion.bash' >> ~/.bashrc

# zsh
bakufu completion zsh > ~/.bakufu-completion.zsh
echo 'source ~/.bakufu-completion.zsh' >> ~/.zshrc
```

## Environment Variables

All variables are optional.

- `BAKUFU_TOKEN`: Pre-obtained bearer token (highest priority)
- `BAKUFU_SERVER`: Server URL (used with `BAKUFU_USER` + `BAKUFU_PASS`)
- `BAKUFU_USER`: Username for direct credential mode
- `BAKUFU_PASS`: Password for direct credential mode
- `BAKUFU_CREDENTIALS_FILE`: Path to JSON credentials file (`server`, `username`, `password`)
- `BAKUFU_ACCOUNT`: Default account name (overridden by `--account`)
- `BAKUFU_HOME`: Config/token directory (default `~/.config/bakufu`)
- `BAKUFU_SWAGGER_PATH`: Override Swagger JSON path

Credential resolution precedence:
1. `BAKUFU_TOKEN` (token only)
2. `BAKUFU_SERVER` + `BAKUFU_USER` + `BAKUFU_PASS`
3. Account credentials (`--account` or `BAKUFU_ACCOUNT` or default account)
4. `BAKUFU_CREDENTIALS_FILE` (or `credentials.json`)

## Architecture

High level:
1. Load Swagger from newest `schemas/swagger*.json` (or `BAKUFU_SWAGGER_PATH`, fallback `swagger_v1.3.json`)
2. Build service and operation model from tags/paths
3. Resolve auth context and access token
4. Execute via `curl`
5. Return structured JSON

Command model:
- High-level stable commands: `auth`, `jobs`, `sessions`, `workflows`, `skills`, `mcp`
- Dynamic operation execution: `services`, `operations`, `run`, `schema`

## Troubleshooting

`zsh: event not found` when password contains `!`:
- Use single quotes around passwords or use interactive prompt mode.

```bash
bakufu auth setup lab --default
```

`Failed to obtain token`:
- Verify server URL, DNS, port (`9419`), and credentials.
- Check if REST API is reachable: `bakufu call /api/v1/serverInfo --dry-run`

No account found / wrong account used:
- Run `bakufu auth list`
- Set default: `bakufu auth default <name>`
- Or override per command: `bakufu --account <name> ...`

Invalid command/subcommand:
- bakufu now returns structured JSON usage errors with nearest-command suggestions.
- Example: typing `auth-setp` will include a hint like `Did you mean auth-setup?`

Missing keyring backend:
- Install/repair keyring dependencies in your environment.
- Reinstall package: `python -m pip install -e .`

Schema looks outdated:
- Put latest schema JSON in `schemas/` and rerun:
- `python scripts/sync_skills_from_swagger.py`

## Development

Install editable package:

```bash
python -m pip install -e .
```

Regenerate skill catalog:

```bash
python scripts/sync_skills_from_swagger.py
```

Sanity check CLI:

```bash
bakufu --help
bakufu auth --help
bakufu mcp --help
```
