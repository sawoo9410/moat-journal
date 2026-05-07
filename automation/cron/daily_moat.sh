#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

mkdir -p automation/logs
PYTHON="${PYTHON:-/opt/homebrew/bin/python3}"
"$PYTHON" automation/src/daily_moat.py 2>&1 | tee -a automation/logs/daily.log
