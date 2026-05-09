# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

남은 작업: **C (메시지 포맷 + 발송 빈도 개편) → D (펀더멘탈 일일 표 통합)**.

완료 이력: Phase 1~3 (인프라), A (출처 누수 차단), Phase 4 (월간 누적 + 독립 분석 구조), B (8종목 추가).

---

## C. 메시지 포맷 개편 + detail 매일→주간 (1순위)

### C.0 변경 후 발송 스케줄 (요약)

매일 07:00 KST 발송 순서: **펀더멘탈 표 → Moat Daily**. 일요일은 추가로 종목별 detail.

| 메시지 | 빈도 | 분할 | 내용 |
|--------|------|------|------|
| 펀더멘탈 표 | 매일 07:00 (1번째) | 1메시지 | PER/ROE/D/E/Margin/52W/배당 (D 단계에서 추가) |
| Moat Daily | 매일 07:00 (2번째) | **[!] 5종목씩 청크** → N개 메시지 | 종목별 호재/악재 ≤3 + 종합평가, 개조식 |
| 종목별 detail | **일요일만** (07:00 추가) | 종목당 1메시지 (= 12개) | 전 종목 풀 detail (개조식 + 종합평가, 호재/악재 ≤5) |

### C.1 프롬프트 강화 — `automation/prompts/daily.md`

- **호재/악재 개수 제한**: 각 섹션 "최대 3개. 우선순위 높은 순서로. 4개째는 출력 금지."
- **정량 강제**: 각 bullet에 숫자/%/금액 포함 필수. 예: "Q1 SSSG +3.8%", "EPS $5.11 (+81% YoY)". 정량 데이터 없는 정성적 코멘트는 금지.
- **쉬운 표현**: 전문용어 최소화. 약자 사용 시 한 번은 풀어쓰기. 예: "ROIC(투하자본수익률)".
- **종합평가 섹션 신설**: 기존 `### 한줄평` → `### 종합평가`로 명칭 변경. 형식은 한 줄 유지하되 출처/매체명 금지 규칙 그대로.

### C.2 메시지 빌더 재구성 — `automation/src/daily_moat.py`

#### C.2.a `build_summary` (Moat Daily, 매일) — **[!] 5종목씩 청크**

기존 한 줄 요약 폐기. 종목 단위 개조식 블록을 **[!] 5종목씩 묶어 N개 메시지**로 송출.

```
[메시지 1 — [!] 1~5번째]
Moat Daily — 2026-05-09 (1/N)

━ GOOGL ━
호재
• Q1 매출 +22% YoY ($109.9B)
• Cloud +63% YoY, AI Overviews MAU 20억
• TPU 외부 판매 개시 (Anthropic)
악재
• 2026 capex 가이던스 $185B (↑)
• DOJ behavioral remedy 발효
• 주가 $397 ATH (시총 $4.82T)
종합평가: castle 견고, 단기 멀티플 부담

━ MCD ━
호재
• ...
악재
• ...
종합평가: ...

[... 최대 5종목까지]
```

마지막 메시지(N/N) 끝에 `안정: KO, O, ...` 한 줄 추가.

규칙:
- [!] 종목만 호재/악재 블록 출력. 호재·악재 둘 다 비어/`없음`이면 "안정"으로 분류
- 청크 단위: **[!] 종목 5개씩**. [!] 6개면 메시지 2개, 11개면 3개, 12개 전부 [!]면 3개(5+5+2)
- 페이지네이션 헤더: `Moat Daily — {date} ({i}/{N})` (N=1이면 `(1/1)` 생략 가능, 하지만 일관성 위해 유지)
- 안정 종목 라인은 **마지막 메시지에만** (모든 청크에 반복 X)
- 종목 블록 사이 빈 줄 1개
- 호재/악재 4개째 이후가 프롬프트 위반으로 들어와도 빌더가 강제로 3개 컷 (방어)
- [!] 0개(전 종목 안정)이면 메시지 1개만: 헤더 + `안정: ...`

#### C.2.b `build_detail` (주간 detail, **일요일만**, 종목당 1메시지)

같은 개조식 폼 — `build_summary` 종목 블록과 거의 동일. 차이:
- 헤더 강조: `━━ {TICKER} — {date} ━━`
- Moat 상태 라인 추가: `Moat: {상태}`
- 호재/악재 컷 풀어 **5개까지** 허용 (주간이라 좀 더 두텁게)
- valuation 한 줄 추가 표시
- 종합평가 풀 문장
- **전 12종목 발송** (안정 포함). 종목당 1메시지 → 일요일 detail은 12개 메시지 묶음

#### C.2.c 빌더에 호재/악재 컷 함수 추가

```python
def _top_n(items: list[str], n: int = 3) -> list[str]:
    """LLM이 4개 이상 출력해도 강제 컷. 첫 n개만 보존(우선순위 순서 가정)."""
    return items[:n]
```

`build_summary`/`build_detail`의 bullet 리스트 생성 시 적용.

### C.3 `main()` 발송 분기 — 요일 체크

```python
weekday = datetime.now(ZoneInfo(tz)).weekday()  # 0=월 ... 6=일
is_weekly_detail_day = weekday == DETAIL_WEEKDAY  # config로 분리
...
telegram_bot.send_message(build_summary(...))
if is_weekly_detail_day:
    for ticker in tickers:
        telegram_bot.send_message(build_detail(...))
```

`config.yaml`에 추가:
```yaml
schedule:
  timezone: "Asia/Seoul"
  detail_weekday: 6           # 일요일 (Python weekday: 0=월 ... 6=일)
  summary_chunk_size: 5       # Moat Daily [!] 종목 청크 크기
```

---

## D. 펀더멘탈 일일 표 통합 (2순위)

`investment-strategy`의 주간 펀더멘탈 잡을 moat-journal로 이전 + **주간→일간** 변경.

### D.1 데이터 소스 분석 (사전 확인 완료)

`investment-strategy/main.py:run_fundamentals_weekly`:
- 데이터 소스: **AlphaVantage API** (env `ALPHAVANTAGE_API_KEY`)
- 함수: `modules.<...>.get_stock_fundamentals(ticker, av_api_key)`
- 필드: `per`, `roe`, `debt_equity`, `profit_margin`, `drop_from_high_pct`, `dividend_yield`
- 발송: `tg.send_weekly_fundamentals(fundamentals_list)` — 표 포맷 메시지

AlphaVantage free tier: **25 req/day, 5 req/min**. 12종목 × 1회/일 = 12 req → **무료 한도 내**.

### D.2 코드 이전 vs 신규 — 이전 권장

투자 전략 측 모듈을 그대로 임포트하기보다 **moat-journal 안에 자체 구현**(코드 ~50줄). 이유:
- moat-journal과 investment-strategy 의존성 분리 (각자 독립 venv)
- 펀더멘탈 호출 + 표 빌드 로직만 필요. 단순.

신규 파일 `automation/src/fundamentals.py`:
- `fetch_fundamentals(ticker, api_key) -> dict` — AlphaVantage `OVERVIEW` endpoint 호출
- `build_fundamentals_table(rows: list[dict]) -> str` — 텔레그램용 표 메시지 (monospace)

### D.3 `daily_moat.py` 통합 — **펀더멘탈 → Moat Daily 순서**

`main()` 진입 후 daily 분석/송출 흐름 변경:

1. **(신규)** `fundamentals.fetch_fundamentals` 12종목 순회 (5 req/min 제한 → `time.sleep(15)` 또는 청크 처리)
2. **(신규)** `build_fundamentals_table` → `telegram_bot.send_message` (1번째 메시지)
3. (기존) 종목별 claude --print 분석 → 월간 파일 append
4. (기존, C 적용 후) `build_summary` 청크 메시지 송출
5. (일요일만, C 적용 후) `build_detail` × 12 송출
6. (기존) git commit

펀더멘탈은 daily 분석보다 빠르게 끝나므로 **펀더멘탈 메시지가 먼저 도착** → 사용자가 시장 펀더멘탈 표 → 호재/악재 순서로 자연스럽게 읽음.

표 예시 (monospace, ` ``` `로 감싸 텔레그램에 보냄):
```
티커   PER   ROE   D/E   Margin  52W%   Div
GOOGL  32×   28%   0.05  29%     -3%    0.6%
MCD    25×   ...
```

### D.4 환경 / 의존성

- `.env`에 `ALPHAVANTAGE_API_KEY=...` 추가 (사용자가 investment-strategy 측 키 그대로 복사)
- `requirements.txt`에 `requests`만 있으면 됨 (이미 있음)

### D.5 investment-strategy 측 정리 (이전 후)

- crontab에서 `run_fundamentals_weekly.sh` 줄 제거 (사용자 직접 — `crontab -e`)
- investment-strategy의 `--mode fundamentals_weekly` 코드는 그대로 둬도 무방 (트리거만 제거)

### D.6 실패 처리

AlphaVantage 호출 실패 시 (rate limit / 5xx / 네트워크):
- 종목 단위 부분 실패: 해당 행을 `티커  -  -  -  -  -  -` 형태로 표시 (표 자체는 송출)
- 전 종목 실패 / 키 누락: 펀더멘탈 메시지 자체를 스킵하고 텔레그램에 `⚠️ 펀더멘탈 조회 실패 ({이유 한 줄})` 한 줄 송출 후 daily 분석은 계속 진행 (의존성 없음)
- daily 분석은 펀더멘탈 결과에 의존하지 않음 → 펀더멘탈 실패가 daily 차단으로 이어지면 안 됨

---

## 실행 순서

1. C 명세 확정 → 수정 세션 → 검증 (LaunchAgent 1회 발사) → 커밋
2. D.6 결정 후 D 명세 확정 → 수정 세션 → 검증 → 커밋
3. investment-strategy 측 crontab 제거 (사용자)
