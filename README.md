# moat-journal

매일 종목별 moat(경쟁우위)을 자동 분석하고, 텔레그램으로 전달하고, git에 기록하는 시스템.

## 구조

```
companies/{TICKER}/
  moat.md                 ← moat thesis (4축 + Castle + ROIC)
  moat-changelog.md       ← thesis 버전 변경 이력
  dividend.md             ← 배당 thesis (전 종목, 무배당은 자본정책 짧게)
  profile.yaml            ← 종목 메타 (이름·섹터·키워드·dividend 블록)
  pre-2025.md             ← 2025 이전 누적 컨텍스트 (해당 종목만)
  {YYYY}/
    {YYYY-MM}.md          ← 일일 분석 월간 누적 (하루 entry append)
    quarterly-Q{N}.md     ← 분기 독립 분석 (WebSearch 기반)
    annual.md             ← 연간 독립 회고

automation/
  config.yaml             ← tickers + paths + schedule (timezone / detail_weekday / chunk_size)
  src/
    daily_moat.py         ← 매일 LaunchAgent 실행 오케스트레이터
    rollup.py             ← 분기/연간 독립 분석
    fundamentals.py       ← AlphaVantage 펀더멘탈 호출 + 카드형 메시지
    telegram_bot.py       ← 텔레그램 전송 (4096자 분할)
  prompts/
    daily.md              ← 일일 분석 프롬프트
    quarterly.md          ← 분기 독립 분석 프롬프트
    annual.md             ← 연간 독립 회고 프롬프트
  cron/                   ← (이름은 cron이지만 실체는 launchd LaunchAgent wrapper)
    daily_moat.sh         ← LaunchAgent wrapper (Keychain OAuth 토큰 주입 + 만료 체크)
    rollup.sh             ← 분기/연간 wrapper
    refresh_token.sh      ← OAuth 토큰 선제 갱신 전용 (4시간 주기)
  logs/                   ← 실행 로그 (gitignore)
```

## 자동화 흐름

트리거: `~/Library/LaunchAgents/com.moat-journal.{daily,quarterly,annual,token-refresh}.plist` (launchd).

macOS cron은 Keychain 접근 불가 → LaunchAgent + wrapper에서 `security find-generic-password`로 Keychain의 `Claude Code-credentials` accessToken 추출 → `CLAUDE_CODE_OAUTH_TOKEN`으로 주입. accessToken 만료 시 `claude --print "ping"`이 refreshToken으로 자동 갱신.

```
매일 07:00 KST
  → daily_moat.py
  → 1. AlphaVantage 펀더멘탈 표 (카드형) → 텔레그램
  → 2. 종목별 claude --print (버핏식 moat 분석 + WebSearch)
  → 3. 월간 파일 {YYYY}/{YYYY-MM}.md에 append
  → 4. Moat Daily 요약 ([!] 5종목씩 청크 → N개 메시지)
  → 5. (일요일만) 종목별 detail (종목당 1메시지)
  → 6. git auto-commit

분기 첫날 07:00 KST (1/1·4/1·7/1·10/1)
  → rollup.py quarterly
  → moat.md/profile.yaml + 월간 파일 컨텍스트 + WebSearch로 분기 독립 분석
  → {YYYY}/quarterly-Q{N}.md 생성 + 텔레그램

연초 1/1 07:00 KST
  → rollup.py annual
  → moat.md/profile.yaml + 4개 분기 파일 컨텍스트 + WebSearch로 연간 회고
  → {YYYY}/annual.md 생성 + 텔레그램

4시간 주기
  → refresh_token.sh
  → accessToken 잔여 시간 체크 → 2시간 미만이면 선제 갱신
```

## 텔레그램 메시지

### 매일 07:00

1. **펀더멘탈 카드** (1메시지) — 종목당 카드 블록, PER/ROE/D/E/Margin/52주 최저 비교/배당
2. **Moat Daily 요약** ([!] 5종목씩 청크 → N메시지) — 종목별 호재/악재 ≤3 + 종합평가, 정량 표현
3. **(일요일만) 종목별 detail** — 12종목 × 1메시지, 풀 호재/악재 ≤5 + valuation + 종합평가

### 작성 규칙

- 출처/매체명/URL 일체 금지 (프롬프트 + 파서 트림 2중 방어)
- 호재/악재 우선순위 순서로 컷 (요약 ≤3, detail ≤5)
- 안정 종목(호재·악재 없음)은 마지막 메시지 끝에 티커만 나열

## 세팅

```bash
pip install -r requirements.txt

# .env (gitignore)
cat > .env <<EOF
MOAT_TELEGRAM_BOT_TOKEN=...
MOAT_TELEGRAM_CHAT_ID=...
ALPHAVANTAGE_API_KEY=...    # 무료 키 25 req/day, 12종목 일일 호출에 충분
EOF

# Claude CLI 인증 (한 번만)
claude /login

# LaunchAgent 등록 (~/Library/LaunchAgents/com.moat-journal.*.plist)
# crontab은 사용 안 함. macOS Keychain 접근 때문에 launchd 필수.
```

## 추적 종목

`automation/config.yaml`의 `tickers`에서 관리. 종목 추가 시 `companies/{TICKER}/moat.md` + `profile.yaml` 스캐폴드 필요 (없으면 daily 분석에서 skip).

## 운영 규칙 / 세션 패턴

`CLAUDE.md` 참고. 계획·수정·평가 3종 세션 구분, todo.md 중심 워크플로우.
