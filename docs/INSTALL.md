# bakufu-cli Install Guide

Quick install paths for macOS, Linux, and Windows.

## Prerequisites

- Python `3.9+` (or use binary install for no-Python targets)
- `curl` in `PATH`
- Access to a Veeam Backup & Replication v13 REST endpoint

Security defaults:
- TLS verification is on by default.
- Use `--insecure` only for trusted lab/self-signed environments.

## macOS / Linux (uv -- recommended)

```bash
git clone https://github.com/anthonyspiteri/veeam-cli.git
cd veeam-cli
uv venv
source .venv/bin/activate
uv pip install -e .
```

Validate:

```bash
bakufu version
bakufu --help
```

## macOS / Linux (pip)

```bash
git clone https://github.com/anthonyspiteri/veeam-cli.git
cd veeam-cli
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Validate:

```bash
bakufu version
bakufu --help
```

## Windows (PowerShell)

```powershell
git clone https://github.com/anthonyspiteri/veeam-cli.git
cd veeam-cli
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Validate:

```powershell
bakufu version
bakufu --help
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Windows (cmd.exe)

```bat
git clone https://github.com/anthonyspiteri/veeam-cli.git
cd veeam-cli
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .
```

## Shell Completion

One-step setup (auto-detects shell, writes completion file, updates rc):

```bash
scripts/setup-completion.sh
```

Manual setup:

```bash
# bash
bakufu completion bash > ~/.bakufu-completion.bash
echo 'source ~/.bakufu-completion.bash' >> ~/.bashrc
source ~/.bashrc

# zsh
bakufu completion zsh > ~/.bakufu-completion.zsh
echo 'autoload -Uz compinit && compinit' >> ~/.zshrc
echo 'source ~/.bakufu-completion.zsh' >> ~/.zshrc
source ~/.zshrc
```

Verify completions are working:

```bash
bakufu <TAB>
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

## Check for Updates

```bash
bakufu version
```

Development clone update:

```bash
cd /path/to/veeam-cli
git pull
source .venv/bin/activate
uv pip install -e .    # or: python -m pip install -e .

# refresh completions after update
bakufu completion "$(basename $SHELL)" > ~/.bakufu-completion."$(basename $SHELL)"
```

## Shell Notes

- Passwords with `!` in `zsh`: avoid inline passwords or wrap with single quotes.
- Prefer interactive auth prompts for complex passwords.

## Optional Environment Variables

- `BAKUFU_HOME` default config/token dir (default `~/.config/bakufu`)
- `BAKUFU_ACCOUNT` default account name
- `BAKUFU_SWAGGER_PATH` explicit schema file path
- `BAKUFU_INSECURE` set to `1|true|yes|on` to disable TLS verification for the current shell
