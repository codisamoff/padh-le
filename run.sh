#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$project_dir/.venv/bin/python" ]]; then
    echo "Padh Le is not installed yet."
    echo
    echo "Run:"
    echo "    ./setup.sh"
    exit 1
fi

exec "$project_dir/.venv/bin/python" "$project_dir/main.py"
