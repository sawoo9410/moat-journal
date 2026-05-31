# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

남은 작업:
- **E. Moat Daily 단축 — 종합평가만 송출** (워킹트리에 구현된 듯, 커밋/검증 미완)
- **F. 펀더멘털 데이터 소스 yfinance 교체** — 빈 카드 → 전 필드 무료 채움
- **G. 로그 월별 분리** — `daily-2026-05.log` 식으로 누적

---

## E. Moat Daily 메시지 단축

### 배경

현재 Moat Daily 요약 메시지는 종목당 호재(≤3) + 악재(≤3) + Valuation + 종합평가까지 모두 포함 → 종목당 ~24줄, 5종목 청크면 한 메시지 ~7KB로 Telegram 4096자 한도 초과 → `_split_message`가 다시 쪼개 가독성 저하.

월간 .md 파일에는 풀 기록(호재/악재/Valuation/종합평가) 보존이 가치 있음. **텔레그램 매일 요약에만 단축 적용**, 깊이는 일요일 detail로.

### E.1 변경 명세

| 항목 | 변경 |
|------|------|
| `companies/{TICKER}/{YYYY}/{YYYY-MM}.md` (월간 기록) | **변경 없음** — 호재/악재/Valuation/종합평가 풀 기록 유지 |
| Moat Daily 메시지 (매일) | **종합평가만** per ticker |
| 일요일 detail 메시지 | **변경 없음** — 호재 ≤5 + 악재 ≤5 + valuation + 종합평가 풀 유지 |
| 청크 크기 | **유지** (`summary_chunk_size: 5`, [!] 5종목씩) |

### E.2 메시지 포맷 (예상)

```
Moat Daily — 2026-05-15 (1/N)

━ GOOGL ━
호재는 Waymo 트립 +92%·검색 점유율 유지·AI 인프라 수요 확장이고, 악재는 FY26 capex $180~190B로 ROIC 분모 팽창·DOJ 항소 장기화·주가 +16.7% 선반영이며, 결과적으로 Castle 외벽은 견고하지만 ROIC 품질 erosion이 thesis 가정보다 빨라 추가매수보다 매출 기여도 확인이 우선인 악재 우위.

━ MCD ━
{종합평가}

[... 최대 5종목]
```

마지막 메시지 끝에 `안정: {티커 쉼표 나열}` 한 줄 추가.

### E.3 코드 수정 범위 — `automation/src/daily_moat.py`

#### `build_summary` 재작성

현재 호재/악재/Valuation/종합평가 블록을 모두 출력 → **종합평가만** 출력하도록 단순화.

```python
def build_summary_chunk(date: str, results: list[dict], chunk_idx: int, chunk_total: int, append_stable: list[str] | None = None) -> str:
    header = f"Moat Daily — {date} ({chunk_idx}/{chunk_total})"
    lines = [header, ""]
    for r in results:
        ticker = r["ticker"]
        comment = r["parsed"]["comment"].strip()
        if not comment:
            continue
        lines.append(f"━ {ticker} ━")
        lines.append(comment)
        lines.append("")
    if append_stable:
        lines.append(f"안정: {', '.join(append_stable)}")
    return "\n".join(lines).rstrip() + "\n"
```

호재/악재 컷 함수(`_top_n`), Valuation 압축 로직 등은 build_summary 경로에서 제거 (build_detail에는 유지).

#### `main()` 청크 송출 로직

[!] 종목(comment 있는 종목)을 `summary_chunk_size`(=5)로 분할 → 각 청크 `build_summary_chunk` 호출 → telegram_bot.send_message.

```python
flagged = [r for r in results if r.get("flag")]
stable = [r["ticker"] for r in results if not r.get("flag") and not r.get("error")]
chunk_size = cfg["schedule"].get("summary_chunk_size", 5)
chunks = [flagged[i:i+chunk_size] for i in range(0, len(flagged), chunk_size)] or [[]]
total = len(chunks)
for idx, chunk in enumerate(chunks, start=1):
    append_stable = stable if idx == total else None
    msg = build_summary_chunk(date, chunk, idx, total, append_stable=append_stable)
    telegram_bot.send_message(msg)
```

[!] 종목 0개 (전 종목 안정)이면 청크 1개 빈 chunk + 안정 라인만 송출.

### E.4 프롬프트 — 변경 없음

`automation/prompts/daily.md`는 현재대로 유지. 호재/악재/Valuation/종합평가 4개 섹션 모두 생성. 단지 텔레그램 송출 시점에 종합평가만 골라 보낼 뿐, **월간 .md 파일에는 풀 기록 그대로 저장**.

### E.5 검증 절차 (수정 세션 후)

1. `launchctl start com.moat-journal.daily` 1회 발사
2. 텔레그램 확인:
   - Moat Daily 메시지가 종목별 `━ TICKER ━ {종합평가}` 블록만 (호재/악재 bullet, Valuation 없음)
   - [!] 종목 5개 이상이면 청크 헤더 `(i/N)` 표시
   - 마지막 청크에만 `안정: ...` 라인
   - 한 메시지가 4096자 미만 (청크가 다시 분할되지 않음)
3. 월간 .md 파일은 그대로 풀 기록 보존 확인
4. 일요일이 아니면 detail 메시지 송출 없음 확인

문제 없으면 E 종결, todo 비우기.

---

## F. 펀더멘털 데이터 소스 yfinance 교체

### 배경 (진단 결과)

현재 펀더멘털 카드는 **매일 비어서 안 나감 + 절반은 N/A**. 3겹 원인:

1. **API 키 부재** — `.env` 없음, plist `EnvironmentVariables` 없음, `launchctl setenv` 없음. `daily_moat.py`의 `av_key=""` → 펀더멘털 단계 silent skip. 22일(05-10~05-31) 연속 로그에 펀더멘털 라인 0건으로 확정.
2. **D/E 항상 N/A** — AlphaVantage `OVERVIEW`에 부채비율 필드 자체가 없음(55개 필드 중 0개). 게다가 `fundamentals.py:48` 로직 반전 버그로 어차피 항상 None.
3. **"52주 고점 대비" 가짜값** — `fundamentals.py:62`이 현재가 대신 `AnalystTargetPrice`(애널리스트 목표가)를 사용. OVERVIEW에 실시간 가격 없음.

### 결정: AlphaVantage → **yfinance (Yahoo Finance)**

실측 검증 완료(yfinance 1.2.0, /opt/homebrew/bin/python3 3.9.13): **API 키 불필요, 12종목 전부**(소형주 AMBQ 포함) 6개 필드 모두 반환. D/E·52주 고점대비 실값 확보 → ②③ 동시 해결. 무료·무한도 → ① 해결.

### F.1 의존성

- `requirements.txt`에 `yfinance>=0.2` 추가. (이미 `--user`로 설치돼 production python에서 import 가능 — 검증 시 설치됨.)
- production python = `/opt/homebrew/bin/python3`. 설치 위치 `~/Library/Python/3.9/site-packages` 가 해당 python sys.path에 포함됨(검증됨).

### F.2 `fundamentals.py` 재작성

기존 AlphaVantage OVERVIEW 호출부 제거, `yfinance.Ticker(sym).info` 사용. **반환 dict 키는 그대로 유지**(`ticker, name, per, roe, debt_equity, profit_margin, drop_from_high_pct, dividend_yield`) → `build_fundamentals_table`은 거의 그대로.

필드 매핑 (yfinance `.info` → 카드값):

| 카드 필드 | info 키 | 변환 | 주의 |
|-----------|---------|------|------|
| name | `shortName` (없으면 `longName`) | 그대로 | |
| per | `trailingPE` | round 1 | None 허용 (AMBQ 등 적자) |
| roe | `returnOnEquity` | ×100, round 1 (%) | 소수 |
| debt_equity | `debtToEquity` | **÷100**, round 2 (비율) | **Yahoo는 퍼센트(예 KO 124.9 → 1.25)** |
| profit_margin | `profitMargins` | ×100, round 1 (%) | 소수, 음수 가능 |
| drop_from_high_pct | `currentPrice`(없으면 `regularMarketPrice`) & `fiftyTwoWeekHigh` | `(price/high-1)*100`, round 1 | **현재가 사용 — 실값** |
| dividend_yield | `dividendYield` | **그대로**, round 1 (%) | **yfinance 1.2.0은 이미 퍼센트 — ×100 금지** (AV와 반대) |

- 값이 None/누락이면 해당 필드 None → 카드에서 N/A 표시(기존 `build_fundamentals_table` 로직 유지). MCD처럼 자기자본 음수면 ROE/D/E None 정상.
- `fetch_fundamentals(ticker)` — `api_key` 인자 제거.
- `fetch_all(tickers)` — `api_key` 인자 제거. AlphaVantage rate-limit 대응 `time.sleep(15)` 제거. 대신 Yahoo 보호용 종목당 `time.sleep(0.3~0.5)` + **빈 info/예외 시 1회 재시도**(2s 후). 예외는 종목별로 잡아 `{"ticker", "error":...}` 반환(기존처럼 표 빌더가 처리).
- `OVERVIEW_URL`, `requests` import, `safe_float`의 AV 전용 분기 등 사용 안 하면 정리.

### F.3 `daily_moat.py` 변경

- `ALPHAVANTAGE_API_KEY` 게이트 **제거** — 키 불필요하므로 펀더멘털 항상 실행.
- 호출부: `fund_rows = fundamentals.fetch_all(tickers)` (api_key 인자 삭제).
- 전체 실패(네트워크 등) 대비 try/except 유지 → 실패 시 `⚠️ 펀더멘탈 조회 실패 (...)` 텔레그램 + stderr.
- step 1 주석/메시지에서 AlphaVantage 잔재 정리.

### F.4 카드 포맷 — 변경 없음

`build_fundamentals_table` 레이아웃(PER/ROE/D/E/Margin/52주/배당) 유지. 이제 D/E·52주가 실값으로 채워짐. 배당 표시 `f"{div}%"` 그대로(이미 퍼센트 저장).

### F.5 검증 (수정 세션 후)

1. `/opt/homebrew/bin/python3 -c "import automation.src.fundamentals as f; print(f.build_fundamentals_table(f.fetch_all(['GOOGL','MCD','KO','AMBQ'])))"` — 4종목 카드에 PER/ROE/D/E/Margin/52주/배당 채워짐(MCD ROE/D/E만 N/A 허용), 빈 카드 없음.
2. `launchctl start com.moat-journal.daily` 1회 발사 → 텔레그램에 펀더멘털 카드 도착(전 종목, D/E·52주 실값).
3. 로그에 `⚠️ 펀더멘탈 조회 실패` 없음 확인.

---

## G. 로그 월별 분리

### 배경

현재 wrapper들이 단일 파일에 무한 append (`daily.log`, `daily-launchd.log`, `rollup.log`, `token-refresh.log`). 회전 없음. 월 경계로 파일을 갈라 누적하고 싶음: `daily-2026-05.log`, `daily-2026-06.log` …

### G.1 방식 — plist 수정 없이 wrapper에서 처리

각 wrapper 상단(`cd` 직후, 토큰 주입/echo 이전)에 월별 파일로 **전체 출력 리다이렉트**:

```bash
mkdir -p automation/logs
MONTH="$(date +%Y-%m)"
exec >> "automation/logs/daily-$MONTH.log" 2>&1
```

- `exec >> ... 2>&1` 이후 모든 wrapper echo + python 출력이 월별 파일 하나로 감 → 기존 `daily.log` + `daily-launchd.log` 이원화가 **단일 월별 파일로 통합**.
- 따라서 `daily_moat.sh` 끝의 `... | tee -a automation/logs/daily.log` 파이프 **제거**, `"$PYTHON" automation/src/daily_moat.py` 만 실행 (pipefail 우려도 사라짐).
- plist `StandardOutPath`/`StandardErrorPath`는 그대로 둠 — `exec` 이후엔 거의 빈 채로 남고, exec 이전 치명적 실패(bash 기동 실패 등)만 잡는 안전망. plist 편집 불필요.

### G.2 적용 대상 wrapper

| wrapper | 월별 파일명 |
|---------|-------------|
| `automation/cron/daily_moat.sh` | `daily-$MONTH.log` |
| `automation/cron/rollup.sh` | `rollup-$MONTH.log` (기존 `tee -a rollup.log` 제거) |
| `automation/cron/refresh_token.sh` | `token-refresh-$MONTH.log` (기존 `LOG=` 고정경로를 월별로) |

각 wrapper 동일 패턴 적용. `refresh_token.sh`는 `LOG` 변수를 `automation/logs/token-refresh-$(date +%Y-%m).log`로 바꾸거나 동일 `exec` 패턴으로 통일.

### G.3 기존 로그 / gitignore

- 기존 `daily.log`/`daily-launchd.log`/`rollup.log`/`token-refresh.log`는 그대로 둠(건드리지 않음). 새 쓰기만 월별로.
- `.gitignore`의 `automation/logs/`가 `*-YYYY-MM.log` 전부 커버 → 추가 설정 불필요.

### G.4 검증 (수정 세션 후)

1. `bash automation/cron/daily_moat.sh` 수동 1회 → `automation/logs/daily-2026-05.log` 생성·기록 확인(wrapper 헤더 + python 출력 한 파일에).
2. plist 발사(`launchctl start com.moat-journal.daily`) 후에도 월별 파일에 정상 적재 확인.
3. 월 경계 자동 분리는 `date +%Y-%m`이 보장(다음 달 첫 실행 시 새 파일).

F·G 모두 검증되면 종결, todo 비우기.
