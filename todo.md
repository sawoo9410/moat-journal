# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

---

# Task K — 지수/ETF 트랙 (`index` 레인)

주식 moat 트랙과 **분리된** 지수/ETF 분석 트랙 신설. moat 프레임(ROE·D/E·마진·해자 서사)은
지수·ETF에 안 맞으므로, 유형 태그 + 프로필 기반의 별도 파이프라인을 만든다.
**주식 moat 코드(daily_moat.py의 종목 로직)는 건드리지 않는다** — 재사용 함수만 import.

## K.1 대상 유니버스 (확정)

유형: `tracker`(지수추종) · `dividend`(배당) · `covered_call`(커버드콜) · `leveraged`(레버리지).

### 미국 (yfinance PER 나옴)
| ID | yf_symbol | 유형 | tracks | valuation_source |
|----|-----------|------|--------|------------------|
| SPYM | SPYM | tracker | SP500 | (self) |
| QQQM | QQQM | tracker | NDX100 | (self) |
| SCHD | SCHD | dividend | US_DIV_DJ100 | (self) |
| JEPQ | JEPQ | covered_call | NDX100 | QQQM |
| SPYI | SPYI | covered_call | SP500 | SPYM |
| QQQI | QQQI | covered_call | NDX100 | QQQM |
| GPIX | GPIX | covered_call | SP500 | SPYM |
| GPIQ | GPIQ | covered_call | NDX100 | QQQM |
| QLD | QLD | leveraged | NDX100 x2 | QQQM |

### 한국 (.KS — yfinance 가격만, PER·yield=None → valuation_source에서 밸류 상속)
| ID | yf_symbol | 유형 | tracks | hedged | valuation_source |
|----|-----------|------|--------|--------|------------------|
| 360750 | 360750.KS | tracker | SP500 | false | SPYM |
| 448290 | 448290.KS | tracker | SP500 | true | SPYM |
| 449180 | 449180.KS | tracker | SP500 | true | SPYM |
| 449190 | 449190.KS | tracker | NDX100 | true | QQQM |
| 458730 | 458730.KS | dividend | US_DIV_DJ100 | false | SCHD |
| 458760 | 458760.KS | covered_call | US_DIV_DJ100 | false | SCHD |
| 0008S0 | 0008S0.KS | covered_call | US_DIV_DJ100 | false | SCHD |

(원지수 ^GSPC/^IXIC/^DJI는 이번 범위 제외 — ETF와 낙폭 중복, 데이터 빈약. 필요 시 후속 추가.)

## K.2 밸류 상속 규칙 (핵심 설계)

- **밸류(PER)만 valuation_source에서 상속** — 같은 바스켓은 래퍼가 달라도 근본 PE가 같다.
  한국 ETF는 yfinance가 PER를 안 주므로, 매 수집 시 valuation_source(미국 티커)의 **같은 날짜 행 PER**를 읽어 밸류 축에 사용.
- **가격·낙폭·MA·52주 위치·타이밍은 절대 상속 금지 — 반드시 그 종목 자기 시계열(원화 포함)로 계산.**
  이유: 환(비헤지)·헤지비용 드래그·NAV 프리미엄/디스카운트 때문에 원화 투자자의 낙폭은 언더라잉과 다르다.
  예) S&P500 -15%(USD) → 360750(비헤지)는 달러 강세 시 원화 -8%, 448290(H)는 ~-15%.
- `hedged` 필드는 낙폭 해석 주석용(헤지=지수+비용, 비헤지=지수±환).

## K.3 데이터 모델 / 디렉토리

```
automation/instruments.yaml          ← index 유니버스 목록(위 표) + 유형/tracks/valuation_source/currency/hedged
indices/{ID}/
  profile.yaml                       ← yf_symbol, name, structure, tracks, valuation_source, currency, hedged, notes
  fundamentals.csv                   ← 일별 수집 (아래 컬럼)
  {YYYY}/{YYYY-MM}.md                ← 월간 분석 append (moat.md 없음 — 컨텍스트는 profile + 프롬프트)
```

`indices/{ID}/fundamentals.csv` 컬럼:
`date, price, per, dist_yield_ttm, dist_yield_ann, drop_from_high_pct, ma50_gap_pct, ma200_gap_pct, currency, source`
- `per`: self 또는 valuation_source 상속(상속 시 source에 `per<-{SRC}` 표기)
- **분배율(확정)**: `yf.Ticker().info["yield"]` **금지**(부정확 — 실측상 QQQI 1.3%↔실제 14.8%, SPYI 2.4%↔12.5%, GPIQ 0.65%↔9.8%). 대신 **`yf.Ticker().dividends`(실제 지급 분배금)로 직접 계산** — US·KR 모두 정확.
  - `dist_yield_ttm` = 최근 12개월 분배금 합 ÷ 현재가 (주지표, 안정적)
  - `dist_yield_ann` = 최근 분배 × 연간 지급횟수 ÷ 현재가 (현재 런레이트)
  - source 라벨 `dividends`. (KR 458760·0008S0·458730도 `.dividends` 정상.)
- `ma50_gap_pct`/`ma200_gap_pct`: `(price/MA - 1)*100`, 자기 가격 히스토리 기반
- 날짜 멱등 append (기존 CSV 로직 재사용)

## K.4 수집 (fundamentals.py 확장)

- 신규 함수 `fetch_index_instrument(profile)`:
  - `yf.Ticker(yf_symbol).history(period="1y")` 로 price/52주고점/MA50/MA200/낙폭/MA gap 계산 (모든 유형 공통, KR 포함).
  - `.info`에서 per/yield (US ETF). KR(.KS)이면 per=None → valuation_source의 당일 CSV 행에서 상속.
  - distribution_yield: US는 `.info` yield best-effort; KR 커버드콜은 K.8 소스 숙제.
- `fetch_all_indices(profiles)` — valuation_source 종목을 **먼저** 수집해야 상속 가능(위상 정렬: self 먼저, 상속 나중).

## K.5 유형별 분석 프레임 + 등급

주식의 `Moat질 × 밸류` 대신 **`추세 × 밸류`** 매트릭스 사용(지수엔 moat 없음).
- **밸류 축**: PER를 자기 history 분위수와 비교 → 저평가/적정/고평가 (recalibrate 방식 재사용). KR은 상속 PER 사용.
- **추세 축**: MA200 기준 상승/중립/하락 (+ MA50 보조, 모멘텀) → 상승/횡보/하락.
- `GRADE_MATRIX_INDEX`(추세 × 밸류) → 신규매수 적기 / 매수 고려 / 관망 / 회피.
- **낙폭 수치 게이트 재사용**: Task I의 `apply_numeric_gates`(dd_typical/dd_shallow) 그대로. ETF PER은 집계라 대부분 `per_reliable: true`.
- 유형별 조정:
  - `tracker`: 위 프레임 그대로.
  - `dividend`: 밸류에 배당수익률 vs 자기 history 보조축. 프레임 동일.
  - `covered_call`: **지금은 tracker와 동일 프레임으로 매수 타이밍만.** 단 분배율·NAV는 첫날부터 수집(K.3). upside cap은 프롬프트 코멘트로만 경고, 등급식은 tracker와 동일. (충분히 검증 후 인컴 서브프레임으로 승격 — 후속 Task.)
  - `leveraged`(QLD): 등급 매트릭스 미적용 → K.6 라운드트립 신호로 대체.

## K.6 QLD 라운드트립 (유일한 매도 신호)

QLD는 적립·무매도가 아니라 **극단 낙폭 진입 → 회복 청산 → 손절**. 별도 로직 `qld_signal(row, state)`:
- **진입**: ATH 대비 낙폭 **-35% 알림 시작, -40~-45%에서 분할**(코어 지수 QQQM 동반 극단낙폭이면 가점) → `진입(극단낙폭)`. 소액만.
- **보유**: 진입선~회복선 사이 → `보유`.
- **청산**: 진입시점 고점 회복(또는 price가 MA50 상향 돌파) → `청산(회복)`.
- **손절**: 진입가 대비 **-18%**(존 -15~-20%) 추가 하락 → `손절`.
- 진입가/손절가/ATH 상태는 `indices/QLD/state.yaml`에 보존(라운드트립 추적). 출력 라벨이 적립 종목과 다름 — 텔레그램/월간 md 별도 표기.

**백테스트 근거(QLD 2006~2026, 5069일)**: 손절 -8~-12%는 휩쏘로 승률 0% → 반드시 -15% 이상. 엔트리 -25%는 얕아 노이즈, -55%는 20년 2회뿐. -35%/-15%가 표본 최다(5거래·60%승·평균+35%). 손절의 핵심 가치는 2008 방어(진입 후 QLD -85%까지 갔으나 손절이 -24%에서 차단). **표본 극소(깊은 낙폭 2~5회)라 확정값 아님 — 라이브 데이터로 재보정할 시작 규칙. `automation/src/tools/qld_backtest.py`로 재실행 가능하게 이관.**

## K.7 프롬프트 (`automation/prompts/index.md`)

- moat.md 미참조. 입력: profile.yaml + fundamentals 실값(PER·낙폭·MA gap·배당/분배율) + tracks/유형.
- 초점(사용자 확정): **밸류(자기 history 대비 PER) + 추세(낙폭·MA50/200) + 매크로(Fed·금리·달러/원화)**.
- 출력 섹션: `밸류`, `추세`, `매크로`, `호재`, `악재`, `매수 매력도`(추세/밸류/유형/근거), `종합평가`.
- covered_call은 분배율 지속성·NAV 침식 코멘트 포함, upside cap 경고. leveraged는 라운드트립·감쇠 경고.
- KR 종목은 환(헤지 여부)·프리미엄/디스카운트 코멘트 요구.

## K.8 캘리브레이션 재사용 + 숙제

- `automation/calibration.yaml`에 index ID 항목 추가(dd_typical/dd_shallow/per_reliable/per_cheap/per_rich).
  - `recalibrate.py`를 indices/*/fundamentals.csv도 스캔하도록 확장(경로 일반화).
  - 최초 임계값은 history 최소 ~30일 쌓인 뒤 하네스+recalibrate로 fit. 그 전엔 cal 비어있어 게이트 미적용(하위호환).
- **숙제 정리**:
  - (a) 분배율 소스 — **확정: yfinance `.dividends` 직접 계산**(K.3). `.info["yield"]` 폐기. Toss API는 공식 없음(비공식 엔드포인트 = fragile+ToS) → 제외.
  - (b) KR NAV/괴리율 — **지금은 불필요**(분배율은 위로 해결). 필요해지면 **네이버 금융/KRX**(Toss 아님). 침식은 자체 가격추세 프록시로 대체.
  - (c) QLD 손절% — **확정: -18%(존 -15~-20%), 엔트리 -35~-45%**(K.6 백테스트). 표본 극소라 라이브 재보정.

## K.9 텔레그램 분리

- `telegram_bot.send_message(text, parse_mode=None, target="moat")` 로 시그니처 확장(하위호환 기본값 "moat").
- `load_config(target)`:
  - `moat`: `MOAT_TELEGRAM_BOT_TOKEN` / `MOAT_TELEGRAM_CHAT_ID` (기존).
  - `index`: `MOAT_INDEX_TELEGRAM_BOT_TOKEN` / `MOAT_INDEX_TELEGRAM_CHAT_ID`.
    - 토큰 미설정 시 moat 봇 토큰으로 폴백 + chat_id만 분리 허용.
- index 런의 모든 전송은 `target="index"`. `.env.example`에 신규 2개 키 추가.

## K.10 오케스트레이터 / 스케줄

- 신규 `automation/src/index_daily.py`(daily_moat.py와 병렬). daily_moat에서 재사용 함수 import:
  `apply_numeric_gates`, `_downgrade`, `compute_grade`(또는 공용 모듈로 추출), `append_monthly`(경로 파라미터화), `load_calibration`, `ticker_calibration`, `run_claude`, `parse_output` 계열.
  - 재사용 위해 필요하면 등급/게이트/파싱을 `automation/src/grading.py` 공용 모듈로 추출(주식 로직 동작 불변 유지).
- 흐름: instruments.yaml 로드 → fetch_all_indices(valuation_source 위상정렬) → CSV append → 유형별 프롬프트/등급(QLD는 라운드트립) → 월간 md append → 텔레그램(target=index) → git commit.
- 신규 wrapper `automation/cron/index_daily.sh`(Keychain 토큰 주입 + index telegram env). 
- 신규 LaunchAgent `com.moat-journal.index.plist` — 매일 07:10 KST(주식 데일리 뒤).

## K.11 구현 순서 (수정 세션)

1. `grading.py` 공용 추출(주식 회귀 없는지 확인) + `append_monthly` 경로 파라미터화.
2. `instruments.yaml` + `indices/{ID}/profile.yaml` 생성(K.1 표).
3. fundamentals.py: `fetch_index_instrument` / `fetch_all_indices`(MA·상속·KR).
4. `GRADE_MATRIX_INDEX` + 추세축 산출 + `qld_signal` + `index.md` 프롬프트.
5. telegram_bot target 분기 + `.env.example`.
6. `index_daily.py` 오케스트레이터.
7. cron wrapper + plist. (등록은 사용자.)
8. 스모크: 1회 수동 실행 → indices/*/CSV·월간 md·텔레그램(index) 확인.
9. history 쌓인 뒤(후속) 하네스+recalibrate로 index 캘리브레이션 fit.

## K.12 범위 밖(후속 Task 후보)

- 커버드콜 인컴 서브프레임(분배율 커버리지·NAV 침식·수익률 지속성) 승격.
- 원지수(^GSPC 등) 편입, CAPE 등 외부 밸류 지표, 브레드스/집중도.
- QLD 손절% 및 진입 분위 백테스트 튜닝.
