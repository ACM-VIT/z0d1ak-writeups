#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE="${SCRIPT_DIR}/scripts/add_comp.bundle.mjs"
SOURCE="${SCRIPT_DIR}/scripts/add_comp.mjs"

if ! command -v node >/dev/null 2>&1; then
    printf 'Node.js 18+ is required to run add_comp.sh\n' >&2
    exit 1
fi

if [[ -f "$BUNDLE" ]]; then
    exec node "$BUNDLE" "$@"
fi

exec node "$SOURCE" "$@"
