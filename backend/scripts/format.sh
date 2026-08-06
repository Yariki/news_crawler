#!/usr/bin/env bash
# Format the source code: sort imports with isort, then apply PEP 8 fixes
# with autopep8. Pass --check to report issues without modifying files.
#
# Usage:
#   scripts/format.sh [--check] [path ...]   (default path: app)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_BIN="$ROOT/.venv/bin"
MAX_LINE_LENGTH=100

CHECK=0
if [[ "${1:-}" == "--check" ]]; then
    CHECK=1
    shift
fi

TARGETS=("$@")
if [[ ${#TARGETS[@]} -eq 0 ]]; then
    TARGETS=("app")
fi

for tool in isort autopep8; do
    if [[ ! -x "$VENV_BIN/$tool" ]]; then
        echo "error: $tool not found in $VENV_BIN — run: pip install -r requirements-dev.txt" >&2
        exit 1
    fi
done

cd "$ROOT"

if [[ $CHECK -eq 1 ]]; then
    "$VENV_BIN/isort" --check-only --diff "${TARGETS[@]}"
    "$VENV_BIN/autopep8" --recursive --diff --aggressive \
        --max-line-length "$MAX_LINE_LENGTH" --exit-code "${TARGETS[@]}"
    echo "OK: no formatting changes needed."
else
    "$VENV_BIN/isort" "${TARGETS[@]}"
    "$VENV_BIN/autopep8" --recursive --in-place --aggressive \
        --max-line-length "$MAX_LINE_LENGTH" "${TARGETS[@]}"cls
    echo "Done: formatted ${TARGETS[*]}."
fi
