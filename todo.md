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

---

# Task M — 구조별 낙폭 임계 + QLD 라운드트립 경보 승격

낙폭 트리거(`index_trigger.py`, 15:15 KST, `target="alert"`)의 대상을 전 구조로 확장하고,
임계를 구조별로 분리한다. 임계는 실증 근거로 정했다 — `automation/src/tools/dd_calibration.py`.

## M.1 배경 — 왜 구조별로 나누나

기존엔 `tracker|dividend`만 대상이고 커버드콜·레버리지는 "규칙 별도"로 빠져 있었다.
구조마다 **하방 캡처율**이 달라서, 같은 임계를 써도 알림 빈도와 "언더라잉이 얼마나
빠졌을 때 울리는지"가 전혀 달라진다. 트래커의 알림 부담(연 5~11회)을 기준선으로 맞춘다.

## M.2 커버드콜 — 트래커와 동일 임계 `[-3, -5, -7, -10]%`

근거(같은 기간으로만 잘라 비교):

| | 하락캡처 | 상승캡처 | 비대칭 | 알림 빈도비 | -3% 후 1년내 NAV 복귀 |
|---|---|---|---|---|---|
| JEPQ | 0.68x | 0.72x | 1.05 유리 | 0.69x | 95% |
| QQQI | 0.73x | 0.79x | 1.09 유리 | 0.74x | 92% |
| GPIQ | 0.77x | 0.85x | 1.10 유리 | 0.83x | 92% |
| SPYI | 0.72x | 0.75x | 1.04 유리 | 0.81x | 100% |
| GPIX | 0.81x | 0.87x | 1.08 유리 | 0.90x | 100% |
| 458760 | 0.25x | 0.58x | 2.33 유리 | 0.75x | 80% |
| 0008S0 | 0.25x | 0.52x | 2.09 유리 | 1.00x | 86% |
| (QQQ 참고) | 1.00x | 1.00x | 1.00 | 1.00x | 89% |

- **낙폭이 진짜 매수 기회였다**: 원가격(NAV) 기준 1년내 복귀율이 92~100%로 언더라잉(89%)보다 높다.
  조정가만 회복하고 NAV는 못 오는 "분배금이 가린 침식" 패턴이 아니다.
- **상승캡처 > 하락캡처**가 전 종목에서 성립 — 교과서적 "상승 캡" 우려와 반대 방향.
- **동일 임계가 곧 중복 제거 필터**: 하락캡처 0.68~0.81x라 같은 임계면 트래커의 69~90%
  빈도로만 울리고, 울릴 때는 언더라잉이 1.3배 더 깊이 빠진 상황이다.
  한국 커버드콜은 환 상쇄로 캡처 0.25x → -3%가 SCHD -12%급 희소·고신호 사건.
- 임의 상수를 새로 만들 근거가 없으므로 트래커와 통일한다.

## M.3 레버리지(QLD) — `[-7, -12, -16, -21]%`

- 하락캡처 **2.12x**. 트래커 임계를 쓰면 최근 3년 **47회(연 15.7회)**로 거의 매달 울린다.
- 캡처 환산(-6.4/-10.6/-14.8/-21.2)과 빈도 정합(-7/-12/-16/-21)이 **독립적으로 일치**.
- 확정 룰 실측(2023-08~2026-08): **27회(연 9.0회)**, 현행 대비 43% 감축.
  같은 기간 QQQ 11.0회 / SPY 6.7회 / SCHD 4.7회 → 트래커 밴드 안에 들어옴.
  20년 장기로는 QLD 7.7회/년 vs SPY 7.9회/년으로 거의 동일.
- 복귀: 중앙 20거래일, 평균 35, p80 56, 최장 102거래일. 27회 중 24회 baseline 복귀.

## M.4 QLD 라운드트립 경보 승격 (별도 트리거 종류)

낙폭 경보("뭔 일 났나")와 진입·손절 신호("실행하라")는 성격이 다르다. 둘 다 alert 채널로
보내되 헤더로 구분한다. 규칙 자체는 K.6에서 확정됐고 `qld_signal`로 이미 구현돼 있다.

- **진입권**: ATH 대비 -35 / -40 / -45% 도달 → `🚨 진입권 · QLD`
- **손절**: 보유 중 진입가 대비 -18% 이탈 → `🚨 손절 · QLD`
- 근거(20.1년, ATH 회복으로 에피소드 구분):
  - -35% 이하 **5건 = 약 4년 주기**(2007-11, 2018-10, 2020-02, 2022-01, 2025-03). 타이밍은 온다.
  - **-35% 도달 5건 전부(100%)가 -40%까지 진행** → -35%는 "알림", -40%가 "분할". 전량 진입 금물.
  - -45% 도달 3건 전부(100%)가 -50%까지 → **-45%도 바닥이 아니다.**
  - ATH 회복 중앙: -35% 기준 137일, -45% 기준 514일. 최장 1095일(2008).
  - 최근 3년 에피소드 2건 — 2022-01 하락장 꼬리(-40% 도달 2023-10-26, 회복 145거래일),
    2025-03(최심 -42.3%, 회복 89거래일). -45%는 3년간 미도달.

## M.5 구현 명세

1. **신규 `automation/trigger_rules.yaml`** — 구조별 임계 + scope_label + qld_roundtrip + evidence.
   손으로 관리(=`calibration.yaml`과 달리 자동 재생성 대상 아님).
2. **`index_trigger.py`**
   - `TRIGGER_STRUCTURES` 제거 → `trigger_rules.yaml`의 `thresholds` 키를 가진 전 구조가 대상.
   - 임계를 구조별로 조회. `deepest_breached(drop, thresholds)`로 파라미터화.
   - 헤더 대상 라벨을 `scope_label`로 구조별 분기 (`지수`/`커버드콜`/`레버리지`).
   - de-dup state(`indices/trigger_state.yaml`)는 종목 단위 그대로 — 임계가 달라도 로직 동일.
3. **QLD 라운드트립 블록**(`index_trigger.py` 내 별도 함수)
   - ATH는 `yf history(period="max")` 러닝맥스로 자체 계산(권위값).
   - `position` / `entry_price` / `stop_price`는 `indices/QLD/state.yaml`에서 **읽기만** 한다.
     상태 전이는 07:00 `index_daily`가 담당 — 쓰기 충돌 금지.
   - 경보 de-dup은 `trigger_state.yaml`의 `qld` 하위 키에 별도 보관:
     `{ath_level, stop_alerted, episode_ath}`. **월 리셋 시 이 키는 보존**해야 한다
     (에피소드가 달을 넘김). 새 ATH 갱신 시 `ath_level` 리셋 = 에피소드 종료.
4. **사유 생성**: 낙폭 경보는 기존대로 tracks당 1회 공유. 라운드트립 경보는 사유 생성 없음
   (진입가/ATH 수치 자체가 메시지).

## M.6 한계 — 재보정 전제

- 커버드콜 표본 2~4년, 전부 상승장. **하락장 NAV 침식 미검증**. 상승캡처 우위도 국면 산물일 수 있다.
- QLD 깊은 낙폭 5건은 통계적으로 약하다(K.6과 동일 한계).
- 트리거가 `yf history()` 기본값(auto_adjust=True)을 쓰므로 **분배금 재투자 기준**으로 낙폭을 잰다.
  증권사 앱의 원가격보다 얕게 나온다(JEPQ 6개월 -5.9% 차이). 본 분석도 같은 기준이라 임계는 정합.
- `dd_calibration.py` 주기적 재실행 → `trigger_rules.yaml`의 `evidence` 갱신.
