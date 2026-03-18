# Updates and Releases

This project supports three update paths depending on how you installed.

## 1) Development Clone (git pull)

Use this if you cloned the repo and run editable installs.

```bash
cd /path/to/veeam-cli
git pull
source .venv/bin/activate
uv pip install -e .    # or: python -m pip install -e .
uv run python scripts/sync_skills_from_swagger.py
```

Refresh shell completions after update:

```bash
bakufu completion "$(basename $SHELL)" > ~/.bakufu-completion."$(basename $SHELL)"
source ~/.bakufu-completion."$(basename $SHELL)"
```

## 2) Versioned Release Tags

Install/update from a pinned release tag:

```bash
# using uv:
uv pip install -U "git+https://github.com/anthonyspiteri/veeam-cli.git@v0.1.0"

# using pip:
python -m pip install -U "git+https://github.com/anthonyspiteri/veeam-cli.git@v0.1.0"
```

This gives predictable upgrades and rollbacks.

## 3) Binary Install (no Python on target)

The install scripts detect existing versions and upgrade automatically:

```bash
# Linux/macOS -- check then upgrade:
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash -s -- --check
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash

# Pin a specific version:
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash -s -- --version v0.2.0
```

```powershell
# Windows -- check then upgrade:
.\scripts\install.ps1 -Check
.\scripts\install.ps1

# Pin a specific version:
.\scripts\install.ps1 -Version v0.2.0
```

Installer behavior:
- Detects existing installation and shows current version.
- Skips download if already at latest (unless `--version` is specified).
- Verifies binary integrity against release `SHA256SUMS.txt`.
- Writes shell completion file and shows next-step instructions.
- For private repos, authenticate with `gh auth login` or set `GITHUB_TOKEN`.

## Version Check

```bash
bakufu version
```

Versioning model:
- Versions are derived automatically from Git tags via `setuptools-scm`.
- Release tags must use `vX.Y.Z` format (example: `v0.1.1`).
- Untagged commits install as dev builds (example: `0.1.2.dev3+g<sha>`).

## Publishing a New Release

1. Ensure `main` is clean and pushed.
2. Create and push a SemVer tag:

```bash
git tag v0.1.1
git push origin v0.1.1
```

Or use the one-shot helper:

```bash
scripts/release.sh v0.1.1
```

3. GitHub Actions (`.github/workflows/release.yml`) will:
- Build `sdist` + `wheel`
- Build standalone binaries for Linux/macOS/Windows
- Generate checksums
- Publish a GitHub Release with artifacts

## Rollback

Pin an older tag:

```bash
# pip:
python -m pip install -U "git+https://github.com/anthonyspiteri/veeam-cli.git@v0.1.0"

# binary:
curl -fsSL .../install.sh | bash -s -- --version v0.1.0
```
