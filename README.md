# bakufu-cli

A multi-layer admin CLI for Veeam Backup & Replication — structured commands, operational runbooks, and role-based workflows for backup admins and infrastructure engineers. Includes MCP server mode for AI agent integration.

> Note
> This is a community project and is not an officially supported Veeam product.

> Important
> This project is under active development. Expect changes as it evolves.

## Contents

- Prerequisites
- Installation
- Updates
- Quick Start
- What is bakufu?
- Command Layers
- Authentication
- Workflows
- Skills and Personas
- MCP Server
- Advanced Usage
- Environment Variables
- Architecture
- Troubleshooting
- Development

## Prerequisites

- Python `3.9+` (or use binary install — no Python required on target)
- `curl` available in `PATH`
- Access to a Veeam Backup & Replication v13 REST API endpoint

## Installation

For OS-specific copy-paste commands, see `docs/INSTALL.md`.
For standalone executable installs, see `docs/INSTALL_BINARY.md`.
For update/upgrade flows, see `docs/UPDATES.md`.

```bash
git clone https://github.com/anthonyspiteri/veeam-cli.git
cd veeam-cli
uv venv && source .venv/bin/activate && uv pip install -e .
# or without uv:
# python3 -m venv .venv && source .venv/bin/activate && python -m pip install -e .
```

Binary install (no Python on target):

```bash
# Linux/macOS one-command installer:
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash

# Windows:
irm https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.ps1 | iex
```

Installers verify SHA256 checksums before install, detect existing versions, and set up shell completions automatically.

Security defaults:
- TLS certificate validation is enabled by default.
- Use `--insecure` only for lab/self-signed certificate scenarios.

## Updates

```bash
# Binary installs — re-run installer (detects and skips if already latest):
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash

# Development clone:
git pull && uv pip install -e .

# Check installed vs latest:
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash -s -- --check
bakufu version
```

Versioning is tag-driven (`setuptools-scm`):
- release tags: `vX.Y.Z`
- non-tagged commits: dev versions (for example `0.1.2.devN+g<sha>`)

## Quick Start

```bash
bakufu getting-started
bakufu getting-started --persona backup-admin
bakufu auth setup lab --default
bakufu jobs list --pretty
bakufu license show --pretty
```

For self-signed lab certs only:

```bash
bakufu --insecure auth setup lab --default
```

## What is bakufu?

Most API-wrapper CLIs give you a 1:1 mapping of REST endpoints to commands. That means you get the API, but none of the operational knowledge of how to use it safely or effectively.

bakufu is modelled on the same approach as the [Google Workspace CLI](https://github.com/googleworkspace/cli) — a purpose-built admin tool with domain-specific commands, structured output, and composable operations. The REST API is the foundation, not the product.

**For backup administrators:**
- Role-specific commands and runbooks without hand-crafted API calls
- Multi-step operations with safety built in (e.g. GET-merge-PUT prevents config overwrites)
- Sequenced workflows for common tasks: investigate a failed job, review repository health, run security analysis, validate restore readiness

**For infrastructure engineers:**
- Proxy, managed server, WAN accelerator, and repository management
- Platform inventory browsing (vSphere, Hyper-V, Cloud Director)
- Component version tracking and rescan orchestration

**For AI agents:**
- Consistent structured JSON output across all commands
- MCP server mode for Claude Desktop, Claude Code, and other MCP-compatible environments
- Skill library with role-based context, recipes, and safe helper tools

## Command Layers

bakufu is built in four composable layers:

| Layer | Count | Description |
|---|---|---|
| Services | 67 | Direct Swagger-driven API operations — every VBR domain exposed as commands |
| Helpers | 18 | Multi-call operations with safety patterns (name resolution, atomic updates, aggregations) |
| Recipes | 42 | Sequenced runbooks with prerequisites, ordered steps, and domain notes |
| Personas | 7 | Role-based skill bundles — backup-admin, storage-admin, infrastructure-engineer, and more |

**Total: 109 skills**

Run any Swagger operation dynamically:

```bash
bakufu services list
bakufu operations --tag Jobs
bakufu run Jobs GetAllJobs --pretty
bakufu schema CreateBackupJob
```

## Authentication

The CLI supports account-based auth, env-based auth, and file-based auth.

Interactive setup (recommended):

```bash
bakufu auth setup lab --default
```

For self-signed cert labs only:

```bash
bakufu auth setup lab --default --insecure
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
- Legacy plaintext account passwords are auto-migrated into keyring when encountered

## Workflows

Built-in multi-step workflows for common operational tasks:

```bash
bakufu workflows investigateFailedJob --job-name "Daily Backup"
bakufu workflows createWasabiRepo --spec @wasabi_repo.json
bakufu workflows capacityReport
bakufu workflows runSecurityAnalyzer --wait --timeout-ms 600000
bakufu workflows validateImmutability
```

## Skills and Personas

bakufu ships a generated skills library for role-based operations and AI agent context.

Load a persona to get role-specific guidance:

```bash
bakufu getting-started --persona backup-admin
bakufu getting-started --persona storage-admin
bakufu getting-started --persona infrastructure-engineer
```

List all available skills:

```bash
bakufu skills list
```

Skills index: `docs/skills.md`

Regenerate from latest local schema:

```bash
uv run python scripts/sync_skills_from_swagger.py
```

## MCP Server

`bakufu mcp` exposes the CLI as a stdio MCP server (Content-Length framed JSON-RPC), compatible with Claude Desktop, Claude Code, and other MCP clients. Helpers and workflows are included by default.

```bash
# All services, helpers, and workflows:
bakufu mcp

# Specific services only:
bakufu mcp -s Jobs,Sessions

# Disable helpers:
bakufu mcp --no-helpers
```

Claude Desktop config example:

```json
{
  "mcpServers": {
    "bakufu": {
      "command": "bakufu",
      "args": ["mcp", "-s", "all"]
    }
  }
}
```

Flags:
- `-s, --services <list|all>`: Comma-separated Swagger tags, or `all` (default: `all`)
- `-e, --helpers`: Expose helper tools (default: on)
- `--no-helpers`: Disable helper tools
- `-w, --workflows`: Expose workflow tools (default: on)
- `--no-workflows`: Disable workflow tools

## Advanced Usage

Output modes:

```bash
bakufu jobs list                               # structured table (default)
bakufu jobs list --json                        # pretty JSON
bakufu jobs list --raw                         # compact JSON
```

Direct API path call:

```bash
bakufu call /api/v1/serverInfo
```

Dry-run request preview:

```bash
bakufu run Jobs GetAllJobs --params '{"limit": 5}' --dry-run
```

Pass a request body:

```bash
bakufu run Jobs CreateBackupJob --body '{"name": "Nightly"}'
bakufu run Jobs CreateBackupJob --body @job-spec.json
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

Security Analyzer:

```bash
bakufu run Security GetSecurityAnalyzerSession
bakufu run Security GetBestPracticesComplianceResult
```

License install from local `.lic` file:

```bash
bakufu license install-file /absolute/path/to/license.lic
```

Shell completion:

```bash
# one-step setup (auto-detects shell, writes file, updates rc):
scripts/setup-completion.sh

# or manually:
bakufu completion bash > ~/.bakufu-completion.bash && echo 'source ~/.bakufu-completion.bash' >> ~/.bashrc
bakufu completion zsh  > ~/.bakufu-completion.zsh  && echo 'source ~/.bakufu-completion.zsh'  >> ~/.zshrc
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
- `BAKUFU_INSECURE`: Disable TLS verification (`1|true|yes|on`) for current process

Credential resolution precedence:
1. `BAKUFU_TOKEN` (token only)
2. `BAKUFU_SERVER` + `BAKUFU_USER` + `BAKUFU_PASS`
3. Account credentials (`--account` or `BAKUFU_ACCOUNT` or default account)
4. `BAKUFU_CREDENTIALS_FILE` (or `credentials.json`)

## Architecture

Four-layer command model:

1. **Services** — Swagger-driven, auto-generated from API tags. Every VBR REST domain is a service.
2. **Helpers** — Python-implemented multi-call tools with safe write patterns and aggregations.
3. **Recipes** — Sequenced runbooks: what to run, in what order, what to look for.
4. **Personas** — Role bundles that load the right recipes and helpers for a given operator.

Execution path:
1. Load Swagger from newest `schemas/swagger*.json` (or `BAKUFU_SWAGGER_PATH`)
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

`SSL certificate problem`:
- Preferred: trust the VBR certificate chain on your host.
- Temporary lab workaround: add `--insecure` to the command.

`--dry-run` output and secrets:
- `Authorization` header is redacted in request preview output.

No account found / wrong account used:
- Run `bakufu auth list`
- Set default: `bakufu auth default <name>`
- Or override per command: `bakufu --account <name> ...`

Invalid command/subcommand:
- bakufu returns structured JSON usage errors with nearest-command suggestions.

Missing keyring backend:
- Reinstall package: `uv pip install -e .`

Schema looks outdated:
- Drop latest schema JSON into `schemas/` and run:
- `uv run python scripts/sync_skills_from_swagger.py`

## Development

Install editable package:

```bash
uv pip install -e .    # or: python -m pip install -e .
```

Regenerate skill catalog:

```bash
uv run python scripts/sync_skills_from_swagger.py
```

Sanity check CLI:

```bash
bakufu --help
bakufu auth --help
bakufu mcp --help
```
