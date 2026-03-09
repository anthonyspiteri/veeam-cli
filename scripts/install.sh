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
CHECKSUM_NAME="SHA256SUMS.txt"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "Installing ${ASSET_NAME} from ${OWNER}/${REPO}..."

if command -v gh >/dev/null 2>&1; then
  gh release download \
    --repo "${OWNER}/${REPO}" \
    --pattern "${ASSET_NAME}" \
    --dir "${TMP_DIR}" \
    --clobber
  gh release download \
    --repo "${OWNER}/${REPO}" \
    --pattern "${CHECKSUM_NAME}" \
    --dir "${TMP_DIR}" \
    --clobber
else
  API_URL="https://api.github.com/repos/${OWNER}/${REPO}/releases/latest"
  CURL_ARGS=(-fsSL)
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    CURL_ARGS+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
  fi
  RELEASE_JSON="${TMP_DIR}/release.json"
  if ! curl "${CURL_ARGS[@]}" -o "${RELEASE_JSON}" "${API_URL}"; then
    echo "Failed to query latest release for ${OWNER}/${REPO}." >&2
    echo "For private repos, authenticate first: gh auth login or export GITHUB_TOKEN=<token>." >&2
    exit 1
  fi
  ASSET_URL="$(
    python3 -c "import json,sys
try:
    d=json.load(open('${RELEASE_JSON}','r',encoding='utf-8'))
except Exception:
    print('', end='')
    raise SystemExit(0)
assets=d.get('assets',[])
n='${ASSET_NAME}'
print(next((a.get('browser_download_url','') for a in assets if a.get('name')==n),''), end='')"
  )"
  CHECKSUM_URL="$(
    python3 -c "import json,sys
try:
    d=json.load(open('${RELEASE_JSON}','r',encoding='utf-8'))
except Exception:
    print('', end='')
    raise SystemExit(0)
assets=d.get('assets',[])
n='${CHECKSUM_NAME}'
print(next((a.get('browser_download_url','') for a in assets if a.get('name')==n),''), end='')"
  )"
  if [[ -z "${ASSET_URL}" ]]; then
    echo "Failed to resolve release asset ${ASSET_NAME} in latest release." >&2
    echo "Check that a release exists and includes this asset. For private repos, use gh auth login or GITHUB_TOKEN." >&2
    exit 1
  fi
  if [[ -z "${CHECKSUM_URL}" ]]; then
    echo "Missing ${CHECKSUM_NAME} in latest release. Refusing unsigned install." >&2
    exit 1
  fi
  if ! curl "${CURL_ARGS[@]}" -o "${TMP_DIR}/${ASSET_NAME}" "${ASSET_URL}"; then
    echo "Failed downloading ${ASSET_NAME} from release assets." >&2
    echo "Confirm token/auth can access private release assets." >&2
    exit 1
  fi
  if ! curl "${CURL_ARGS[@]}" -o "${TMP_DIR}/${CHECKSUM_NAME}" "${CHECKSUM_URL}"; then
    echo "Failed downloading ${CHECKSUM_NAME}." >&2
    exit 1
  fi
fi

CHECKSUM_FILE="${TMP_DIR}/${CHECKSUM_NAME}"
if [[ ! -f "${CHECKSUM_FILE}" ]]; then
  echo "Missing ${CHECKSUM_NAME}; cannot verify binary integrity." >&2
  exit 1
fi

EXPECTED_HASH="$(
  awk -v n="${ASSET_NAME}" '
    $2 == n || $2 == ("*" n) { print $1; exit }
  ' "${CHECKSUM_FILE}"
)"
if [[ -z "${EXPECTED_HASH}" ]]; then
  echo "No checksum entry for ${ASSET_NAME} in ${CHECKSUM_NAME}." >&2
  exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL_HASH="$(sha256sum "${TMP_DIR}/${ASSET_NAME}" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
  ACTUAL_HASH="$(shasum -a 256 "${TMP_DIR}/${ASSET_NAME}" | awk '{print $1}')"
else
  echo "No SHA256 tool found (expected sha256sum or shasum)." >&2
  exit 1
fi

if [[ "${EXPECTED_HASH}" != "${ACTUAL_HASH}" ]]; then
  echo "Checksum verification failed for ${ASSET_NAME}." >&2
  exit 1
fi

chmod +x "${TMP_DIR}/${ASSET_NAME}"

if [[ -w "${INSTALL_DIR}" ]]; then
  mv "${TMP_DIR}/${ASSET_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
else
  sudo mv "${TMP_DIR}/${ASSET_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
fi

echo "Installed to ${INSTALL_DIR}/${BINARY_NAME}"
"${INSTALL_DIR}/${BINARY_NAME}" version
