#!/usr/bin/env bash
set -euo pipefail

# Lightweight installer for bakufu release binaries.
# Works with private repos when either:
# - gh CLI is authenticated, or
# - GITHUB_TOKEN is set.

OWNER="${BAKUFU_REPO_OWNER:-anthonyspiteri}"
REPO="${BAKUFU_REPO_NAME:-veeam-cli}"
INSTALL_DIR="${BAKUFU_INSTALL_DIR:-/usr/local/bin}"
BINARY_NAME="bakufu"

OS="$(uname -s)"
ARCH="$(uname -m)"

case "${OS}" in
  Linux) OS_ASSET="linux" ;;
  Darwin) OS_ASSET="macos" ;;
  *)
    echo "Unsupported OS: ${OS}" >&2
    exit 1
    ;;
esac

case "${ARCH}" in
  x86_64|amd64) ARCH_ASSET="x86_64" ;;
  arm64|aarch64)
    if [[ "${OS_ASSET}" == "macos" ]]; then
      ARCH_ASSET="arm64"
    else
      ARCH_ASSET="x86_64"
      echo "Warning: arm64 Linux binary is not published yet; falling back to x86_64." >&2
    fi
    ;;
  *)
    echo "Unsupported architecture: ${ARCH}" >&2
    exit 1
    ;;
esac

ASSET_NAME="${BINARY_NAME}-${OS_ASSET}-${ARCH_ASSET}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "Installing ${ASSET_NAME} from ${OWNER}/${REPO}..."

if command -v gh >/dev/null 2>&1; then
  gh release download \
    --repo "${OWNER}/${REPO}" \
    --pattern "${ASSET_NAME}" \
    --dir "${TMP_DIR}" \
    --clobber
else
  API_URL="https://api.github.com/repos/${OWNER}/${REPO}/releases/latest"
  CURL_ARGS=(-fsSL)
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    CURL_ARGS+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
  fi
  ASSET_URL="$(
    curl "${CURL_ARGS[@]}" "${API_URL}" \
      | python3 -c "import sys, json; d=json.load(sys.stdin); assets=d.get('assets', []); n='${ASSET_NAME}'; print(next((a['browser_download_url'] for a in assets if a.get('name')==n), ''))"
  )"
  if [[ -z "${ASSET_URL}" ]]; then
    echo "Failed to resolve release asset ${ASSET_NAME}. For private repos, set GITHUB_TOKEN or use gh auth login." >&2
    exit 1
  fi
  curl "${CURL_ARGS[@]}" -o "${TMP_DIR}/${ASSET_NAME}" "${ASSET_URL}"
fi

chmod +x "${TMP_DIR}/${ASSET_NAME}"

if [[ -w "${INSTALL_DIR}" ]]; then
  mv "${TMP_DIR}/${ASSET_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
else
  sudo mv "${TMP_DIR}/${ASSET_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
fi

echo "Installed to ${INSTALL_DIR}/${BINARY_NAME}"
"${INSTALL_DIR}/${BINARY_NAME}" version
