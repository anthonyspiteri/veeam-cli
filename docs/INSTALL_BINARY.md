# Binary Install

Install `bakufu` as a standalone executable (no Python/venv required on target host).

## From GitHub Releases

1. Open the latest release for `anthonyspiteri/veeam-cli`.
2. Download the binary for your OS:
- `bakufu-linux-x86_64`
- `bakufu-macos-arm64`
- `bakufu-windows-x86_64.exe`

## Linux / macOS

```bash
# Option A: one-command installer from this repo
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash

# Option B: manual
chmod +x bakufu-linux-x86_64
sudo mv bakufu-linux-x86_64 /usr/local/bin/bakufu
bakufu version
bakufu getting-started
```

For macOS:

```bash
chmod +x bakufu-macos-arm64
sudo mv bakufu-macos-arm64 /usr/local/bin/bakufu
bakufu version
bakufu getting-started
```

## Windows (PowerShell)

```powershell
# Option A: one-command installer from this repo
irm https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.ps1 | iex

# Option B: manual
mkdir "$env:USERPROFILE\bin" -Force
Move-Item .\bakufu-windows-x86_64.exe "$env:USERPROFILE\bin\bakufu.exe"
$env:Path += ";$env:USERPROFILE\bin"
bakufu version
bakufu getting-started
```

## Notes

- The binary includes a bundled Swagger schema in `schemas/` for dynamic command discovery.
- Override schema path at runtime with:
  - `BAKUFU_SWAGGER_PATH=/path/to/swagger.json`
- For private repos, authenticate first:
  - `gh auth login` (recommended), or
  - set `GITHUB_TOKEN` before running installers.
