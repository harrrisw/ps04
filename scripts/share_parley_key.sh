#!/usr/bin/env bash
# Explicitly share a key with agent-run processes through a Git-ignored file.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -z "${PARLEY_API_KEY:-}" ]]; then
  read -r -s -p 'Paste your MIT Parley API key (input hidden): ' PARLEY_API_KEY
  printf '\n'
fi
[[ -n "$PARLEY_API_KEY" ]] || { echo 'No key supplied.' >&2; exit 1; }
umask 077
mkdir -p .secrets
printf '%s' "$PARLEY_API_KEY" > .secrets/parley_api_key.txt
echo 'Key saved locally in .secrets/parley_api_key.txt (ignored by Git). No API request made.'
