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

# alert 텔레그램 env — 경보 전용 채널. 토큰 미설정 시 telegram_bot에서 moat 봇 토큰 폴백
export MOAT_ALERT_TELEGRAM_BOT_TOKEN="${MOAT_ALERT_TELEGRAM_BOT_TOKEN:-}"
export MOAT_ALERT_TELEGRAM_CHAT_ID="${MOAT_ALERT_TELEGRAM_CHAT_ID:-}"

export HOME="${HOME:-/Users/seosang-u}"
export USER="${USER:-seosang-u}"
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"
export PATH="/Users/seosang-u/.local/bin:$PATH"

PYTHON="${PYTHON:-/opt/homebrew/bin/python3}"

# LaunchAgent에서 Keychain OAuth 토큰 주입 (만료 체크 포함)
# 돌파가 있을 때만 하락 사유 생성에 claude를 쓴다 — 평소(무돌파)에는 호출 자체가 없다.
_inject_oauth_token() {
  local creds token expires_at now_ms
  creds="$(security find-generic-password -s 'Claude Code-credentials' -w 2>/dev/null || true)"
  if [ -z "$creds" ]; then
    echo "[trigger-wrapper] Keychain 접근 실패" >&2
    return
  fi

  read -r token expires_at <<< "$(/opt/homebrew/bin/python3 -c "
import sys, json
d = json.load(sys.stdin)['claudeAiOauth']
print(d['accessToken'], d.get('expiresAt', 0))
" <<< "$creds" 2>/dev/null)"

  now_ms="$(/opt/homebrew/bin/python3 -c "import time; print(int(time.time()*1000))")"

  # "지금 안 만료됐나"가 아니라 "이 작업이 끝날 때까지 버티나"를 본다. (daily_moat.sh 주석 참조)
  # 트리거는 돌파가 있을 때만 사유 생성(tracks당 1회)이라 짧지만, 같은 규칙을 적용한다.
  local margin_ms=$(( ${TOKEN_MARGIN_MIN:-30} * 60 * 1000 ))

  if [ "$expires_at" -gt "$(( now_ms + margin_ms ))" ] 2>/dev/null; then
    echo "[trigger-wrapper] OAuth 토큰 유효 (expires in $(( (expires_at - now_ms) / 60000 ))분)" >&2
    export CLAUDE_CODE_OAUTH_TOKEN="$token"
  else
    echo "[trigger-wrapper] OAuth 토큰 잔여 부족(<${TOKEN_MARGIN_MIN:-30}분) — claude CLI로 갱신 시도" >&2
    claude --print -p "ping" >/dev/null 2>&1 || true
    creds="$(security find-generic-password -s 'Claude Code-credentials' -w 2>/dev/null || true)"
    token="$(/opt/homebrew/bin/python3 -c "import sys,json; print(json.load(sys.stdin)['claudeAiOauth']['accessToken'])" <<< "$creds" 2>/dev/null || true)"
    if [ -n "$token" ]; then
      echo "[trigger-wrapper] 토큰 갱신 성공" >&2
      export CLAUDE_CODE_OAUTH_TOKEN="$token"
    else
      echo "[trigger-wrapper] 토큰 갱신 실패 — 사유 없이 가격만 전송됨" >&2
    fi
  fi
}
_inject_oauth_token

echo "[trigger-wrapper] $(date -Iseconds) python=$PYTHON"

"$PYTHON" automation/src/index_trigger.py
