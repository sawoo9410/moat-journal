# moat-journal — 운영 규칙

매일 cron으로 종목별 moat(경쟁우위) 분석을 자동 실행하고, 기록을 저장하고, 텔레그램으로 전송하는 시스템.

## 세션 규칙

| 세션 | 수정 가능 범위 | 목적 |
|------|---------------|------|
| **계획** | `.md` 문서만 | 요구사항 정리, 룰 확정, 구현 계획을 `todo.md`에 작성 |
| **수정** | 코드만 (`.py`, `.yaml`, `.sh`) | `todo.md` 보고 구현. **todo.md 수정 금지** |
| **평가** | 읽기 전용 | `todo.md` 기준으로 코드 구현 여부 판정 |

### todo 중심 워크플로우

- **계획 세션**: 세운 계획을 모두 `todo.md`에 구현 명세로 작성. 계획 완료 시 커밋.
- **수정 세션**: `todo.md`를 읽고 구현. todo.md는 읽기 전용 — 비우기 포함 일체 수정 금지. 완료 후 커밋.
- **평가 세션**: `todo.md`에 남아있는 항목 vs 코드 상태를 비교하여 정합성 판정.

### 세션 트리거

사용자가 명시:
- "계획 세션이야" → 계획
- "수정 세션이야" → 수정
- "평가해줘" / "평가 세션이야" → 평가

## 디렉토리 구조

```
automation/
  config.yaml            ← 추적 종목, 텔레그램 설정
  .env.example           ← 환경변수 템플릿
  src/
    daily_moat.py         ← 매일 cron 실행 오케스트레이터
    telegram_bot.py       ← 텔레그램 전송
    rollup.py             ← 분기/연간 요약 생성
  prompts/
    daily.md              ← claude --print용 분석 프롬프트 템플릿
  cron/
    daily_moat.sh         ← cron wrapper
    rollup.sh             ← 분기/연간 rollup wrapper
  logs/                   ← 실행 로그 (gitignore)

companies/{TICKER}/
  moat.md                ← moat thesis (누적)
  daily/
    {YYYY-MM-DD}.md      ← 일일 분석 기록
  quarterly/
    {YYYY}-Q{N}.md       ← 분기 요약
  annual/
    {YYYY}.md            ← 연간 요약
```

## 텔레그램 메시지 형식

### 메시지 1 — 일일 요약 (항상 전송)

```
Moat Daily — {날짜}

[!] GOOGL — AI capex ROI 우려, EU DMA 벌금 리스크
[!] MCD — 동일점포 매출 +3.2% (예상 상회)

안정: KO, QCOM, OXY
```

### 메시지 2~N — [!] 종목만 별도 메시지로 전송

```
━━━━━━━━━━━━━━━━
  {TICKER} — {날짜}
  Moat: {상태} ({변동})
━━━━━━━━━━━━━━━━

💰 {현재가} / {핵심 지표}

💬 호재는 {~}이고, 악재는 {~}이고, 결과적으로 {~}이지만 {호재|악재}다.
```

- [!] 종목마다 **별도 텔레그램 메시지**로 전송 (하나로 합치지 않음)
- **텔레그램에 출처/소스/뉴스 상세 일체 포함 금지** — 한줄평이 호악재를 종합
- 출처·뉴스 bullet 포함한 전체 분석은 `companies/{TICKER}/daily/{날짜}.md`에만 기록

## 자동화 흐름

```
매일 07:00 KST (cron)
  → daily_moat.py
  → config.yaml에서 추적 종목 읽기
  → 종목별 claude --print (버핏식 moat 분석 + 웹 검색)
  → companies/{TICKER}/daily/{날짜}.md에 저장
  → 신호 분류 (호재/악재/안정) → 텔레그램 전송
  → git auto-commit

분기 말 (cron, 분기 1회)
  → rollup.py quarterly
  → 해당 분기 daily 기록 종합 → quarterly/{YYYY}-Q{N}.md
  → 텔레그램 분기 요약 전송

연말 (cron, 연 1회)
  → rollup.py annual
  → 4개 분기 요약 종합 → annual/{YYYY}.md
```

## commit 정책

- 수정 세션: 구현 완료 후 자동 commit
- 계획 세션: 계획 완료 후 커밋
- `git push`: 사용자만
- `.env` / 시크릿 파일 commit 금지

## 참조

| 항목 | 위치 |
|------|------|
| 구현 명세 | `todo.md` |
| 추적 종목 설정 | `automation/config.yaml` |
| 분석 프롬프트 템플릿 | `automation/prompts/daily.md` |
| 사용자 프로필 | `memory/user_profile.md` |
