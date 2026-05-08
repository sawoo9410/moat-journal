#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# cron 환경에서는 PATH가 최소이므로 claude CLI 경로 추가
export PATH="/Users/seosang-u/.local/bin:$PATH"

mkdir -p automation/logs
PYTHON="${PYTHON:-/opt/homebrew/bin/python3}"
"$PYTHON" automation/src/daily_moat.py 2>&1 | tee -a automation/logs/daily.log
