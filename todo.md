# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

남은 작업:
- **J. 펀더멘털 시계열 적재** — 종목별 CSV 하루 1행 (작업 I의 전제)
- **I. 매수 매력도 등급** — 포지션 무관 4단계 · 하이브리드 판단 · 레인별 기준

> E·F·G·H는 정합 완료(커밋 4cae983까지)되어 제거됨.
> 구현 순서: **J → I** (I의 밸류 판단이 J의 과거 데이터를 소비).

---

## J. 펀더멘털 시계열 적재

### 목표

현재 펀더멘털은 매일 조회 → 텔레그램 카드 전송 → **버려짐**(어디에도 저장 안 됨). 종목별 시계열로 적재해 과거평균·밴드 계산을 가능케 함. **작업 I의 밸류 판단(배당 yield vs 과거평균, PER vs 자기 밴드)의 전제.**

### J.1 저장 형식 — 종목별 CSV

```
companies/{TICKER}/fundamentals.csv
date,per,roe,debt_equity,profit_margin,drop_from_high_pct,dividend_yield,source
2026-06-01,23.0,35.8,1.25,31.6,-18.3,2.66,yfinance
```

- 하루 1행 append (1년 ≈ 365행, 가벼움). 컬럼 = F.2 정규화 단위 그대로(ROE/Margin/배당=%, D/E=비율).
- None 필드는 빈 칸. `source` = 그 행을 채운 소스(F.6 폴백에 따라 `yfinance` 또는 `yfinance+stooq` 등).
- **git 커밋 대상** — `companies/` 는 gitignore 아님. 버전관리할 데이터.

### J.2 코드 변경 — `automation/src/daily_moat.py` step 1

`fetch_all` 직후, 텔레그램 전송과 **독립적으로** CSV append (append 실패가 카드 전송을 막지 않도록 try/except 분리):

```python
fund_rows = fundamentals.fetch_all(tickers)
for row in fund_rows:
    try:
        append_fundamentals_csv(row["ticker"], date, row)  # error 행은 skip
    except Exception as e:
        print(f"[daily_moat] fundamentals csv append 실패 {row['ticker']}: {e}", file=sys.stderr)
fund_table = fundamentals.build_fundamentals_table(fund_rows)
telegram_bot.send_message(fund_table)
```

신규 함수 `append_fundamentals_csv(ticker, date, row)`:
- 파일 없으면 헤더 먼저 기록.
- **멱등성**: 같은 `date` 행이 이미 있으면 중복 append 금지 — 그 날짜 행을 덮어쓰거나 skip(수동 재실행 대비).
- `row.get("error")` 있으면 **skip**(빈 행으로 오염시키지 않음).
- 저장한 CSV 경로를 `git_commit` 대상(`saved_paths`)에 포함.

### J.3 검증 (수정 세션 후)

1. 수동 1회 실행 → `companies/GOOGL/fundamentals.csv` 생성, 헤더 + 당일 1행.
2. 같은 날 재실행 → 행 중복 안 됨(멱등).
3. error 종목은 행 미기록.
4. `git status`에 `companies/*/fundamentals.csv` 추적됨(커밋 포함).

J 검증 완료되면 I 착수.

---

## I. 매수 매력도 등급

### 목표

매일 종목별로 "**지금 이 가격에 신규 진입할 만한가**"를 4단계로 판정해 텔레그램 + 월간 .md에 표시. 보유 현황은 추적하지 않음(포지션 무관 매력도, 길 A). moat-journal의 역할은 장기보유 관점의 매력 평가 — 타이밍 트레이딩은 별도 프로젝트 담당.

### I.1 등급 체계 (포지션 무관 4단계)

| 등급 | 의미 |
|------|------|
| **신규매수 적기** | 지금 들어갈 만함 |
| **매수 고려** | 들어가도 되나 서두를 것 없음 |
| **관망** | 진입 근거 부족, 대기 |
| **회피** | 신규 진입 부적절 (보유 중이면 비중축소로 읽음) |

"분할매수/보유" 같은 포지션 전제 단어 금지(현재 0포지션).

### I.2 판단 = 2축 + 하이브리드 결합

**축 1 — Moat질 (LLM 정성)**: 견고 / 좁음 / 약화 / 훼손 (기존 `Moat 상태`와 연동)
**축 2 — 밸류 (LLM이 주입된 실값에 ground)**: 저평가 / 적정 / 고평가

- **절대 PER로 자르지 않음** — 종목 자신/섹터 기준 상대평가. 룰은 실값(52주 고점대비·PER·배당)을 LLM에 주입해 ground시키고, 극단값만 가드.
- **하이브리드 분담**:
  - LLM: 두 축(Moat질 + 밸류) 판정 + 1줄 근거. 주입된 펀더멘털 실값 + 웹검색으로 맥락 부여.
  - Python: 아래 **매트릭스로 최종 등급을 결정론적으로 산정**(LLM이 제안한 등급이 아니라 매트릭스가 authoritative) + 자본보존 가드 적용.

### I.3 결합 매트릭스 (Python, authoritative)

| Moat질 ＼ 밸류 | 저평가 | 적정 | 고평가 |
|---|---|---|---|
| **견고** | 신규매수 적기 | 매수 고려 | 관망 |
| **좁음** | 매수 고려 | 관망 | 관망 |
| **약화** | 관망 | 회피 | 회피 |
| **훼손** | 회피 | 회피 | 회피 |

**자본보존 가드 (결정론적)**: Moat질이 `약화`/`훼손`이면 어떤 밸류에서도 `신규매수 적기`·`매수 고려`가 나오지 않도록 clamp(매트릭스가 이미 보장하나, LLM이 다른 등급을 우겨도 Python이 재강제). 싼 게 함정일 수 있음.

### I.4 레인별 기준 (compounder vs dividend)

레인은 `profile.yaml`에서 결정:
- 명시적 `lane: compounder|dividend` 있으면 그대로.
- 없으면: `tracking_purpose`에 `dividend` 포함 또는 `dividend:` 블록 존재 → dividend, 아니면 compounder.
- 수정 세션은 `profile.yaml`에 `lane` 필드 추가 권장(예: O=dividend, GOOGL=compounder). `dividend.md`는 대부분 종목에 스캐폴드돼 있어 레인 판별 근거로 쓰지 말 것.

레인별로 두 축의 잣대가 다름(프롬프트에서 분기):

| | compounder | dividend |
|---|---|---|
| Moat질 | 재투자 해자 폭(ROIC·재투자 활주로) | 현금흐름 안정 해자 |
| 밸류(저평가 판단) | 성장 대비 PER + 52주 위치 | 배당수익률 vs 과거평균/국채 + payout 안전성(FCF 커버) |
| 회피 트리거 | moat 약화/훼손 · 성장정체+고PER | 배당컷 리스크 · payout 위험 · moat 훼손 |

"과거평균/밴드"(yield 과거평균, PER 자기 밴드)는 **J의 `fundamentals.csv`에서 계산**해 프롬프트에 함께 주입. 데이터가 부족한 초기엔 LLM 웹검색/현재값으로 graceful fallback.

### I.5 코드/프롬프트 변경 범위

**`automation/prompts/daily.md`**
- `{FUNDAMENTALS}`, `{LANE}` placeholder 추가.
- 새 섹션 `### 매수 매력도` 출력 지시 — 형식:
  ```
  - Moat질: 견고|좁음|약화|훼손
  - 밸류: 저평가|적정|고평가
  - 레인: compounder|dividend
  - 근거: {한 줄, 레인 기준 반영}
  ```
- 기존 섹션(Moat 상태/호재/악재/Valuation/종합평가)은 유지. 레인별 잣대 설명을 프롬프트에 명시.

**`automation/src/daily_moat.py`**
- `render_prompt(template, ticker, moat_content, fundamentals_str, lane)`로 확장 — 시그니처에 펀더멘털 실값 문자열 + 레인 주입.
  - 펀더멘털 문자열: step 1에서 받은 `fund_rows`를 `{ticker: row}` dict로 만들어 조회. 포맷 예 `PER 23 / ROE 35.8% / D/E 1.25 / Margin 31.6% / 52주 고점대비 -18.3% / 배당 2.66%`. error 행이면 `펀더멘털 N/A`.
  - 레인: `profile.yaml` 읽어 I.4 규칙으로 결정. 헬퍼 `load_lane(ticker) -> "compounder"|"dividend"`.
- `parse_output`: `### 매수 매력도`에서 `moat_q`(Moat질), `valuation_bucket`(밸류), `rec_lane`, `rec_rationale` 추출.
- 신규 `compute_grade(moat_q: str, valuation_bucket: str) -> str` — I.3 매트릭스 + 가드. 알 수 없는 값이면 안전하게 `관망`.
- `results[i]`에 `grade`, `rec_rationale` 추가.

**`companies/{T}/profile.yaml`**: `lane` 필드 추가(선택, 추론 폴백 있음).

### I.6 표시 위치

**텔레그램 — Moat Daily 요약** (build_summary_chunks):
- [!] 종목 헤더에 등급 인라인: `━ GOOGL · 매수 고려 ━` 후 종합평가.
- 안정 종목 라인에도 등급: `안정: KO·관망, QCOM·매수 고려` (전 종목 등급 가시화).

**월간 .md**: claude raw 출력에 `### 매수 매력도` 섹션이 포함되므로 `append_monthly`가 자동 보존(추가 작업 없음). Python이 매트릭스로 보정한 최종 등급과 LLM 섹션이 다를 수 있으니, 월간 .md에는 **보정 후 최종 등급 한 줄을 헤더에 덧붙임**(예: `## 2026-06-01 · 매수 고려`)— append 시 date 헤더에 등급 부가.

**펀더멘털 카드(step 1)**: 등급은 분석(step 2) 이후 산정되므로 카드에는 넣지 않음(카드는 실값 먼저 도착 유지).

### I.7 검증 (수정 세션 후)

1. 4종목 수동 실행 → 각 출력에 `### 매수 매력도`(Moat질/밸류/레인/근거) 존재, 최종 등급이 4단계 중 하나.
2. **가드 검증**: Moat질이 약화/훼손인 종목은 신규매수 적기·매수 고려가 절대 안 나옴.
3. **레인 검증**: O는 dividend 잣대(배당 안전성·payout 언급), GOOGL은 compounder 잣대(재투자/성장 대비 PER).
4. 텔레그램 요약에 `━ TICKER · 등급 ━` + 안정 라인 등급 표시. 월간 .md date 헤더에 최종 등급 부가.

I 검증 완료되면 종결, todo 비우기.
