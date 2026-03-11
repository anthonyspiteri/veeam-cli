#!/usr/bin/env bash
set -euo pipefail

# Configure bakufu shell completion on Linux/macOS.
# Usage:
#   scripts/setup-completion.sh
#   scripts/setup-completion.sh --shell zsh
#   scripts/setup-completion.sh --shell bash --no-rc

SHELL_NAME=""
UPDATE_RC="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --shell)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --shell (expected: zsh|bash)" >&2
        exit 1
      fi
      SHELL_NAME="$2"
      shift 2
      ;;
    --no-rc)
      UPDATE_RC="false"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: scripts/setup-completion.sh [--shell zsh|bash] [--no-rc]

Options:
  --shell   Target shell (zsh or bash). Default: detect from $SHELL.
  --no-rc   Do not modify shell rc file; only write completion file.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${SHELL_NAME}" ]]; then
  SHELL_NAME="$(basename "${SHELL:-}")"
fi

if [[ "${SHELL_NAME}" != "zsh" && "${SHELL_NAME}" != "bash" ]]; then
  echo "Unsupported shell '${SHELL_NAME}'. Use --shell zsh or --shell bash." >&2
  exit 1
fi

if ! command -v bakufu >/dev/null 2>&1; then
  echo "bakufu not found in PATH. Install bakufu first." >&2
  exit 1
fi

if [[ "${SHELL_NAME}" == "zsh" ]]; then
  OUT_FILE="${HOME}/.bakufu-completion.zsh"
  RC_FILE="${HOME}/.zshrc"
  SOURCE_LINE='source ~/.bakufu-completion.zsh'
  COMPMGR_LINE='autoload -Uz compinit && compinit'
else
  OUT_FILE="${HOME}/.bakufu-completion.bash"
  RC_FILE="${HOME}/.bashrc"
  SOURCE_LINE='source ~/.bakufu-completion.bash'
  COMPMGR_LINE=""
fi

bakufu completion "${SHELL_NAME}" > "${OUT_FILE}"
echo "Wrote completion file: ${OUT_FILE}"

if [[ "${UPDATE_RC}" == "true" ]]; then
  touch "${RC_FILE}"
  if [[ -n "${COMPMGR_LINE}" ]] && ! grep -Fqx "${COMPMGR_LINE}" "${RC_FILE}"; then
    echo "${COMPMGR_LINE}" >> "${RC_FILE}"
    echo "Updated ${RC_FILE}: added compinit line"
  fi
  if ! grep -Fqx "${SOURCE_LINE}" "${RC_FILE}"; then
    echo "${SOURCE_LINE}" >> "${RC_FILE}"
    echo "Updated ${RC_FILE}: added completion source line"
  fi
fi

echo "Done. Reload your shell:"
if [[ "${SHELL_NAME}" == "zsh" ]]; then
  echo "  exec zsh"
else
  echo "  exec bash"
fi
