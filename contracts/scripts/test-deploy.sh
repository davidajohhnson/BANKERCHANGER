#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_SCRIPT="${SCRIPT_DIR}/deploy.sh"

bash -n "$DEPLOY_SCRIPT"
bash -n "${SCRIPT_DIR}/verify-wasm-upload.sh"

help_output="$(bash "$DEPLOY_SCRIPT" --help)"
for option in --network --rpc-url --secret-key; do
    if [[ "$help_output" != *"$option"* ]]; then
        echo "ERROR: deploy help does not document $option" >&2
        exit 1
    fi
done

if ! rg -q 'command -v soroban' "$DEPLOY_SCRIPT" || \
   ! rg -q '\$STELLAR_CLI" contract deploy' "$DEPLOY_SCRIPT" || \
   ! rg -q '\$STELLAR_CLI" contract invoke' "$DEPLOY_SCRIPT"; then
    echo "ERROR: deploy script is missing CLI fallback or current CLI commands" >&2
    exit 1
fi

echo "Deploy script syntax and CLI checks passed"
