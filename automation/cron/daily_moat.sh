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

# LaunchAgent에서 Keychain OAuth 토큰 주입 (만료 체크 포함)
# accessToken은 수시간짜리이므로 만료 여부를 확인하고,
# 만료됐으면 claude CLI에게 직접 갱신시킨 뒤 새 토큰을 가져옴
_inject_oauth_token() {
  local creds token expires_at now_ms
  creds="$(security find-generic-password -s 'Claude Code-credentials' -w 2>/dev/null || true)"
  if [ -z "$creds" ]; then
    echo "[wrapper] Keychain 접근 실패" >&2
    return
  fi

  read -r token expires_at <<< "$(/opt/homebrew/bin/python3 -c "
import sys, json
d = json.load(sys.stdin)['claudeAiOauth']
print(d['accessToken'], d.get('expiresAt', 0))
" <<< "$creds" 2>/dev/null)"

  now_ms="$(/opt/homebrew/bin/python3 -c "import time; print(int(time.time()*1000))")"

  if [ "$expires_at" -gt "$now_ms" ] 2>/dev/null; then
    echo "[wrapper] OAuth 토큰 유효 (expires in $(( (expires_at - now_ms) / 60000 ))분)" >&2
    export CLAUDE_CODE_OAUTH_TOKEN="$token"
  else
    echo "[wrapper] OAuth 토큰 만료 — claude CLI로 갱신 시도" >&2
    # 토큰 없이 claude 한 번 실행 → CLI가 Keychain에서 refreshToken으로 자동 갱신
    claude --print -p "ping" >/dev/null 2>&1 || true
    # 갱신된 토큰 재추출
    creds="$(security find-generic-password -s 'Claude Code-credentials' -w 2>/dev/null || true)"
    token="$(/opt/homebrew/bin/python3 -c "import sys,json; print(json.load(sys.stdin)['claudeAiOauth']['accessToken'])" <<< "$creds" 2>/dev/null || true)"
    if [ -n "$token" ]; then
      echo "[wrapper] 토큰 갱신 성공" >&2
      export CLAUDE_CODE_OAUTH_TOKEN="$token"
    else
      echo "[wrapper] 토큰 갱신 실패 — CLAUDE_CODE_OAUTH_TOKEN 미설정" >&2
    fi
  fi
}
_inject_oauth_token

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
