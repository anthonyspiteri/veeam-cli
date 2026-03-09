#!/usr/bin/env bash
set -euo pipefail

# Cut and push a release tag for GitHub Actions to publish artifacts.
# Usage:
#   scripts/release.sh v0.1.1
#   scripts/release.sh v0.1.1 --dry-run

usage() {
  cat <<'EOF'
Usage: scripts/release.sh <tag> [--dry-run]

Examples:
  scripts/release.sh v0.1.1
  scripts/release.sh v0.1.1 --dry-run

Notes:
  - Must be run from a git checkout with origin configured.
  - Tag format must be vX.Y.Z (SemVer).
  - Pushes main and the tag to origin unless --dry-run is set.
EOF
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

TAG="$1"
DRY_RUN="false"
if [[ "${2:-}" == "--dry-run" ]]; then
  DRY_RUN="true"
elif [[ $# -eq 2 ]]; then
  usage
  exit 1
fi

if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid tag: $TAG (expected vX.Y.Z)" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not in a git repository." >&2
  exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "main" ]]; then
  echo "Current branch is '$BRANCH'. Switch to 'main' before releasing." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is dirty. Commit or stash changes before releasing." >&2
  exit 1
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag already exists locally: $TAG" >&2
  exit 1
fi

if git ls-remote --exit-code --tags origin "refs/tags/${TAG}" >/dev/null 2>&1; then
  echo "Tag already exists on origin: $TAG" >&2
  exit 1
fi

echo "Release summary"
echo "  branch: $BRANCH"
echo "  tag:    $TAG"
echo "  commit: $(git rev-parse --short HEAD)"
echo "  dryrun: $DRY_RUN"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "Dry run complete. No changes made."
  exit 0
fi

git push origin main
git tag "$TAG"
git push origin "$TAG"

echo
echo "Release tag pushed: $TAG"
echo "GitHub Actions release workflow should now build and publish assets."
echo "Check status:"
echo "  gh run list --workflow release.yml --limit 5"
echo "View release:"
echo "  gh release view $TAG --repo \$(git config --get remote.origin.url | sed -E 's#(git@github.com:|https://github.com/)##; s#\\.git\$##')"
