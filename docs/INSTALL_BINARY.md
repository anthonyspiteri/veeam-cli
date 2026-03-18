# Binary Install

Install `bakufu` as a standalone executable (no Python/venv required on target host).

## From GitHub Releases

Release assets are published per platform:
- `bakufu-linux-x86_64`
- `bakufu-macos-arm64`
- `bakufu-windows-x86_64.exe`

All downloads are verified against release `SHA256SUMS.txt` before install.

## Linux / macOS

### One-command installer (recommended)

```bash
# Latest release:
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash

# Specific version:
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash -s -- --version v0.2.0

# Check installed vs latest (no install):
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash -s -- --check
```

### From local clone (private repos)

```bash
git clone git@github.com:anthonyspiteri/veeam-cli.git
cd veeam-cli
bash scripts/install.sh
```

### Manual install

Linux:

```bash
chmod +x bakufu-linux-x86_64
sudo mv bakufu-linux-x86_64 /usr/local/bin/bakufu
bakufu version
```

macOS:

```bash
chmod +x bakufu-macos-arm64
sudo mv bakufu-macos-arm64 /usr/local/bin/bakufu
bakufu version
```

## Windows (PowerShell)

### One-command installer (recommended)

```powershell
# Latest release:
irm https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.ps1 | iex

# Specific version:
.\scripts\install.ps1 -Version v0.2.0

# Check installed vs latest (no install):
.\scripts\install.ps1 -Check
```

### From local clone (private repos)

```powershell
git clone git@github.com:anthonyspiteri/veeam-cli.git
cd veeam-cli
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

### Manual install

```powershell
mkdir "$env:USERPROFILE\bin" -Force
Move-Item .\bakufu-windows-x86_64.exe "$env:USERPROFILE\bin\bakufu.exe"
$env:Path += ";$env:USERPROFILE\bin"
bakufu version
```

To make PATH permanent:

```powershell
[Environment]::SetEnvironmentVariable('Path', $env:Path + ";$env:USERPROFILE\bin", 'User')
```

## Updating a Binary Install

Re-run the installer -- it detects the existing version and upgrades if a newer release is available:

```bash
# Linux/macOS:
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash

# Or check first:
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash -s -- --check
```

```powershell
# Windows:
irm https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.ps1 | iex
```

## Shell Completion (Binary Installs)

The installer writes a completion file automatically. To set up manually:

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

Verify:

```bash
bakufu <TAB>
```

## Post-Install

```bash
bakufu version                              # confirm version
bakufu auth setup lab --default             # configure VBR connection
bakufu getting-started                      # guided tour
```

## Notes

- The binary includes a bundled Swagger schema in `schemas/` for dynamic command discovery.
- Override schema path at runtime with `BAKUFU_SWAGGER_PATH=/path/to/swagger.json`.
- For private repos, authenticate first: `gh auth login` (recommended), or set `GITHUB_TOKEN`.
- If no release exists yet, installers will fail until a tagged release publishes assets.
