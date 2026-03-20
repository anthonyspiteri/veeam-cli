#!/usr/bin/env bash
set -euo pipefail

# Installer for bakufu release binaries.
# Works with private repos when either:
# - gh CLI is authenticated, or
# - GITHUB_TOKEN is set.
#
# Usage:
#   scripts/install.sh                  # install latest release
#   scripts/install.sh --version v0.2.0 # install specific version
#   scripts/install.sh --check          # check installed vs latest version
#   curl -fsSL .../install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --version v0.2.0

OWNER="${BAKUFU_REPO_OWNER:-anthonyspiteri}"
REPO="${BAKUFU_REPO_NAME:-veeam-cli}"
INSTALL_DIR="${BAKUFU_INSTALL_DIR:-/usr/local/bin}"
BINARY_NAME="bakufu"
REQUESTED_TAG=""
CHECK_ONLY="false"

# ── Parse arguments ──────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --version (expected vX.Y.Z)" >&2
        exit 1
      fi
      REQUESTED_TAG="$2"
      shift 2
      ;;
    --check)
      CHECK_ONLY="true"
      shift
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: install.sh [--version vX.Y.Z] [--check]

Options:
  --version TAG   Install a specific release tag (default: latest)
  --check         Compare installed version against latest release and exit
  -h, --help      Show this help

Environment:
  BAKUFU_REPO_OWNER   GitHub owner (default: anthonyspiteri)
  BAKUFU_REPO_NAME    GitHub repo  (default: veeam-cli)
  BAKUFU_INSTALL_DIR  Install path (default: /usr/local/bin)
  GITHUB_TOKEN        Auth token for private repos
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $1. Use --help for usage." >&2
      exit 1
      ;;
  esac
done

# ── Detect platform ──────────────────────────────────────────────────
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

# ── Check existing installation ──────────────────────────────────────
EXISTING_VERSION=""
if command -v "${BINARY_NAME}" >/dev/null 2>&1; then
  EXISTING_VERSION="$("${BINARY_NAME}" version 2>/dev/null || echo "unknown")"
  EXISTING_PATH="$(command -v "${BINARY_NAME}")"
  echo "Existing installation found: ${EXISTING_VERSION} (${EXISTING_PATH})"
fi

# ── Resolve latest release tag ───────────────────────────────────────
LATEST_TAG=""
if command -v gh >/dev/null 2>&1; then
  LATEST_TAG="$(gh release view --repo "${OWNER}/${REPO}" --json tagName -q .tagName 2>/dev/null || true)"
fi

if [[ "${CHECK_ONLY}" == "true" ]]; then
  if [[ -z "${EXISTING_VERSION}" ]]; then
    echo "bakufu is not installed."
  else
    echo "Installed: ${EXISTING_VERSION}"
  fi
  if [[ -n "${LATEST_TAG}" ]]; then
    echo "Latest release: ${LATEST_TAG}"
    if [[ -n "${EXISTING_VERSION}" && "${EXISTING_VERSION}" == "${LATEST_TAG#v}" ]]; then
      echo "Already up to date."
    else
      echo "Update available: run install.sh to upgrade."
    fi
  else
    echo "Could not determine latest release (gh CLI may not be authenticated)."
  fi
  exit 0
fi

# Skip download if already at latest and no specific version requested
# Use exact match: installed version must equal the tag (e.g. "0.1.9" == "0.1.9")
# Dev/dirty suffixes (e.g. "0.1.9.dev0+...") are treated as different from the release.
if [[ -n "${EXISTING_VERSION}" && -n "${LATEST_TAG}" && -z "${REQUESTED_TAG}" ]]; then
  if [[ "${EXISTING_VERSION}" == "${LATEST_TAG#v}" ]]; then
    echo "Already at latest version (${EXISTING_VERSION}). Use --version TAG to force a specific version."
    exit 0
  fi
fi

if [[ -n "${EXISTING_VERSION}" ]]; then
  echo "Upgrading bakufu from ${EXISTING_VERSION}..."
fi

# ── Download release assets ──────────────────────────────────────────
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

if [[ -n "${REQUESTED_TAG}" ]]; then
  echo "Installing ${ASSET_NAME} (${REQUESTED_TAG}) from ${OWNER}/${REPO}..."
else
  echo "Installing ${ASSET_NAME} (latest) from ${OWNER}/${REPO}..."
fi

if command -v gh >/dev/null 2>&1; then
  gh release download ${REQUESTED_TAG:+"${REQUESTED_TAG}"} \
    --repo "${OWNER}/${REPO}" \
    --pattern "${ASSET_NAME}" \
    --dir "${TMP_DIR}" \
    --clobber
  gh release download ${REQUESTED_TAG:+"${REQUESTED_TAG}"} \
    --repo "${OWNER}/${REPO}" \
    --pattern "${CHECKSUM_NAME}" \
    --dir "${TMP_DIR}" \
    --clobber
else
  if [[ -n "${REQUESTED_TAG}" ]]; then
    API_URL="https://api.github.com/repos/${OWNER}/${REPO}/releases/tags/${REQUESTED_TAG}"
  else
    API_URL="https://api.github.com/repos/${OWNER}/${REPO}/releases/latest"
  fi
  CURL_ARGS=(-fsSL)
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    CURL_ARGS+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
  fi
  RELEASE_JSON="${TMP_DIR}/release.json"
  if ! curl "${CURL_ARGS[@]}" -o "${RELEASE_JSON}" "${API_URL}"; then
    echo "Failed to query release for ${OWNER}/${REPO}." >&2
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
    echo "Failed to resolve release asset ${ASSET_NAME} in release." >&2
    echo "Check that a release exists and includes this asset. For private repos, use gh auth login or GITHUB_TOKEN." >&2
    exit 1
  fi
  if [[ -z "${CHECKSUM_URL}" ]]; then
    echo "Missing ${CHECKSUM_NAME} in release. Refusing unsigned install." >&2
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

# ── Verify checksum ──────────────────────────────────────────────────
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
echo "Checksum verified."

# ── Install binary ───────────────────────────────────────────────────
chmod +x "${TMP_DIR}/${ASSET_NAME}"

if [[ -w "${INSTALL_DIR}" ]]; then
  mv "${TMP_DIR}/${ASSET_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
else
  sudo mv "${TMP_DIR}/${ASSET_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
fi

echo "Installed to ${INSTALL_DIR}/${BINARY_NAME}"

# ── Verify installation ──────────────────────────────────────────────
NEW_VERSION=""
if "${INSTALL_DIR}/${BINARY_NAME}" version >/dev/null 2>&1; then
  NEW_VERSION="$("${INSTALL_DIR}/${BINARY_NAME}" version 2>/dev/null)"
  echo "Version: ${NEW_VERSION}"
else
  echo "Warning: installed binary failed self-check. Reinstall from a newer release or build locally." >&2
fi

# ── PATH check ───────────────────────────────────────────────────────
if ! echo "${PATH}" | tr ':' '\n' | grep -qx "${INSTALL_DIR}"; then
  echo ""
  echo "Warning: ${INSTALL_DIR} is not in your PATH."
  echo "Add it to your shell profile:"
  DETECTED_SHELL="$(basename "${SHELL:-bash}")"
  if [[ "${DETECTED_SHELL}" == "zsh" ]]; then
    echo "  echo 'export PATH=\"${INSTALL_DIR}:\$PATH\"' >> ~/.zshrc && exec zsh"
  else
    echo "  echo 'export PATH=\"${INSTALL_DIR}:\$PATH\"' >> ~/.bashrc && exec bash"
  fi
fi

# ── Shell completion setup ───────────────────────────────────────────
echo ""
echo "Shell completion:"
if command -v "${BINARY_NAME}" >/dev/null 2>&1; then
  DETECTED_SHELL="$(basename "${SHELL:-bash}")"
  if [[ "${DETECTED_SHELL}" == "zsh" ]]; then
    COMP_FILE="${HOME}/.bakufu-completion.zsh"
    RC_FILE="${HOME}/.zshrc"
    SOURCE_LINE="source ~/.bakufu-completion.zsh"
    if "${BINARY_NAME}" completion zsh > "${COMP_FILE}" 2>/dev/null; then
      echo "  Wrote ${COMP_FILE}"
    fi
    if [[ -f "${RC_FILE}" ]] && grep -Fqx "${SOURCE_LINE}" "${RC_FILE}" 2>/dev/null; then
      echo "  Already sourced in ${RC_FILE}"
    else
      echo "  To enable, add to ${RC_FILE}:"
      echo "    autoload -Uz compinit && compinit"
      echo "    ${SOURCE_LINE}"
    fi
  elif [[ "${DETECTED_SHELL}" == "bash" ]]; then
    COMP_FILE="${HOME}/.bakufu-completion.bash"
    RC_FILE="${HOME}/.bashrc"
    SOURCE_LINE="source ~/.bakufu-completion.bash"
    if "${BINARY_NAME}" completion bash > "${COMP_FILE}" 2>/dev/null; then
      echo "  Wrote ${COMP_FILE}"
    fi
    if [[ -f "${RC_FILE}" ]] && grep -Fqx "${SOURCE_LINE}" "${RC_FILE}" 2>/dev/null; then
      echo "  Already sourced in ${RC_FILE}"
    else
      echo "  To enable, add to ${RC_FILE}:"
      echo "    ${SOURCE_LINE}"
    fi
  else
    echo "  Run: bakufu completion --help"
  fi
else
  echo "  Binary not in PATH yet; run completion setup after fixing PATH."
fi

echo ""
echo "Next steps:"
echo "  bakufu auth setup <name> --default    # configure VBR connection"
echo "  bakufu getting-started                # guided tour"
