# Updates and Releases

This project supports two update paths:

## 1) Development Clone (git pull)

Use this if you cloned the repo and run editable installs.

```bash
cd /path/to/veeam-cli
git pull
source .venv/bin/activate
python -m pip install -e .
python scripts/sync_skills_from_swagger.py
```

Optional completion refresh:

```bash
bakufu completion zsh > ~/.bakufu-completion.zsh
source ~/.bakufu-completion.zsh
```

## 2) Versioned Release Tags (recommended)

Install/update from a pinned release tag:

```bash
python -m pip install -U "git+https://github.com/anthonyspiteri/veeam-cli.git@v0.1.0"
```

This gives predictable upgrades and rollbacks.

Binary-first update (no Python on target):

```bash
curl -fsSL https://raw.githubusercontent.com/anthonyspiteri/veeam-cli/main/scripts/install.sh | bash
```

Installer behavior:
- Verifies binary integrity against release `SHA256SUMS.txt`.
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
python -m pip install -U "git+https://github.com/anthonyspiteri/veeam-cli.git@v0.1.0"
```
