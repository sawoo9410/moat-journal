#!/bin/bash
set -euo pipefail

# OAuth 토큰 갱신 전용 스크립트
# LaunchAgent가 4시간마다 실행 → accessToken이 항상 유효한 상태 유지
# claude --print -p "ping" 실행 시 CLI가 Keychain refreshToken으로 자동 갱신

export HOME="${HOME:-/Users/seosang-u}"
export USER="${USER:-seosang-u}"
export PATH="/Users/seosang-u/.local/bin:$PATH"

LOG="/Users/seosang-u/moat-journal/automation/logs/token-refresh.log"
mkdir -p "$(dirname "$LOG")"

{
  echo "[token-refresh] $(date -Iseconds)"

  # 현재 토큰 만료 시간 확인
  creds="$(security find-generic-password -s 'Claude Code-credentials' -w 2>/dev/null || true)"
  if [ -z "$creds" ]; then
    echo "[token-refresh] Keychain 접근 실패"
    exit 1
  fi

  expires_at="$(/opt/homebrew/bin/python3 -c "
import sys, json
d = json.load(sys.stdin)['claudeAiOauth']
print(d.get('expiresAt', 0))
" <<< "$creds" 2>/dev/null || echo 0)"

  now_ms="$(/opt/homebrew/bin/python3 -c "import time; print(int(time.time()*1000))")"

  if [ "$expires_at" -gt "$now_ms" ] 2>/dev/null; then
    remaining=$(( (expires_at - now_ms) / 60000 ))
    echo "[token-refresh] 토큰 유효 (잔여 ${remaining}분)"
    # 잔여 2시간 이상이면 갱신 불필요
    if [ "$remaining" -gt 120 ]; then
      echo "[token-refresh] 충분한 잔여 시간 — 갱신 스킵"
      exit 0
    fi
    echo "[token-refresh] 잔여 시간 부족 — 선제 갱신"
  else
    echo "[token-refresh] 토큰 만료됨"
  fi

  # claude CLI 실행으로 refreshToken → 새 accessToken 갱신
  if claude --print -p "ping" >/dev/null 2>&1; then
    echo "[token-refresh] 갱신 성공"
  else
    echo "[token-refresh] 갱신 실패 (claude --print rc=$?)"
    exit 1
  fi
} >> "$LOG" 2>&1
