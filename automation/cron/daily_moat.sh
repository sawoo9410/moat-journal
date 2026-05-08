#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# cron 환경에서는 PATH가 최소이므로 환경 변수 명시
export HOME="${HOME:-/Users/seosang-u}"
export USER="${USER:-seosang-u}"
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"
export PATH="/Users/seosang-u/.local/bin:$PATH"

# LaunchAgent에서 Keychain OAuth 토큰 주입
CLAUDE_CODE_OAUTH_TOKEN="$(security find-generic-password -s 'Claude Code-credentials' -w 2>/dev/null | /opt/homebrew/bin/python3 -c "import sys,json; print(json.load(sys.stdin)['claudeAiOauth']['accessToken'])" 2>/dev/null || true)"
export CLAUDE_CODE_OAUTH_TOKEN

mkdir -p automation/logs
PYTHON="${PYTHON:-/opt/homebrew/bin/python3}"

{
  echo "[wrapper] $(date -Iseconds)"
  echo "[wrapper] HOME=$HOME USER=$USER"
  echo "[wrapper] PATH=$PATH"
  echo "[wrapper] which claude: $(command -v claude || echo NOT_FOUND)"
  echo "[wrapper] claude --version: $(claude --version 2>&1 || echo VERSION_FAILED)"
  echo "[wrapper] claude config dir: $(ls -la "$HOME/.config/claude" 2>&1 | head -3 || echo NO_CONFIG_DIR)"
  echo "[wrapper] python: $PYTHON ($($PYTHON --version 2>&1))"
} >&2

"$PYTHON" automation/src/daily_moat.py 2>&1 | tee -a automation/logs/daily.log
