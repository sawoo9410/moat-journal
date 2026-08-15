#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/../.."

# 월별 로그 분리
mkdir -p automation/logs
MONTH="$(date +%Y-%m)"
exec >> "automation/logs/index-trigger-$MONTH.log" 2>&1

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# index 텔레그램 env — 미설정 시 telegram_bot에서 moat 봇 토큰 폴백
export MOAT_INDEX_TELEGRAM_BOT_TOKEN="${MOAT_INDEX_TELEGRAM_BOT_TOKEN:-}"
export MOAT_INDEX_TELEGRAM_CHAT_ID="${MOAT_INDEX_TELEGRAM_CHAT_ID:-}"

export HOME="${HOME:-/Users/seosang-u}"
export USER="${USER:-seosang-u}"
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"
export PATH="/Users/seosang-u/.local/bin:$PATH"

PYTHON="${PYTHON:-/opt/homebrew/bin/python3}"

# 낙폭 트리거는 LLM 미사용 — Keychain OAuth 주입 불필요(가격 조회 + 텔레그램만)
echo "[trigger-wrapper] $(date -Iseconds) python=$PYTHON"

"$PYTHON" automation/src/index_trigger.py
