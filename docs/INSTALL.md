# bakufu-cli Install Guide

Quick install paths for macOS, Linux, and Windows.

## Prerequisites

- Python `3.9+`
- `curl` in `PATH`
- Access to a Veeam Backup & Replication v13 REST endpoint

Security defaults:
- TLS verification is on by default.
- Use `--insecure` only for trusted lab/self-signed environments.

## macOS / Linux (bash/zsh)

```bash
git clone <your-repo-url>
cd veeam-api-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Validate:

```bash
bakufu --help
bakufu auth --help
```

## Windows (PowerShell)

```powershell
git clone <your-repo-url>
cd veeam-api-agent
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Validate:

```powershell
bakufu --help
bakufu auth --help
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Windows (cmd.exe)

```bat
git clone <your-repo-url>
cd veeam-api-agent
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .
```

## First Auth

Interactive setup (recommended):

```bash
bakufu auth setup lab --default
```

Self-signed lab certificates:

```bash
bakufu --insecure auth setup lab --default
```

Then:

```bash
bakufu auth token --refresh
bakufu jobs list --pretty
```

## Shell Notes

- Passwords with `!` in `zsh`: avoid inline passwords or wrap with single quotes.
- Prefer interactive auth prompts for complex passwords.
- One-step completion setup (macOS/Linux):

```bash
scripts/setup-completion.sh
```

## Optional Environment Variables

- `BAKUFU_HOME` default config/token dir (default `~/.config/bakufu`)
- `BAKUFU_ACCOUNT` default account name
- `BAKUFU_SWAGGER_PATH` explicit schema file path
- `BAKUFU_INSECURE` set to `1|true|yes|on` to disable TLS verification for the current shell
