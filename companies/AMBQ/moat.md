# AMBQ Moat Thesis (버핏식)
_Last updated: 2026-05-09 · Version: v1 (draft — 잠정 thesis, 2025 IPO)_
**Lane**: `compounder` _(무배당 — 재투자 중심 초기 성장주. `dividend.md` = 무배당 stub.)_

> ⚠ **잠정(tentative) thesis**: AMBQ는 2025-07 IPO 기업. 공개 재무 이력이 매우 짧고, 분기 실적 1~2회분만 존재. 본 thesis는 잠정 평가이며, 최소 4분기 실적 누적 후 본격 판단.

## One-liner
서브-스레숄드 전력 기술(SPOT) 기반 초저전력 MCU + edge AI SoC. 웨어러블/히어러블/IoT에서 전력 효율이 핵심 구매 기준인 틈새 시장을 공략. 규모는 작으나 기술 차별화가 thesis의 핵심.

---

## Buffett 4축 현황

| 축 | 현재 상태 | 방향 | 핵심 숫자 / 비고 |
|---|---|---|---|
| ROIC 품질 | **적자** (2025 순손실 ~$36M) | _[unknown]_ | IPO 초기 — ROIC 양전환 시점 미정. 매출 $72.5M(2025) 대비 손실 과대. _[unknown — 2026-H2 분기 실적으로 추세 확인 필요]_ |
| 가격결정력 | 제한적 추정 | _[unknown]_ | SPOT 기술의 전력 효율 프리미엄 존재 여부 — ASP 추이로 판단. 2025 GM 44.8%(non-GAAP)는 fabless 평균 수준. _[unknown — ASP YoY 추이 미공개]_ |
| 자본집약도 | Fabless → light | 유지 추정 | 자체 fab 없음. R&D 비중 높을 것으로 추정. capex 절대액 _[unknown — 10-K/10-Q 확인 필요]_ |
| 산업 안정성 | 변동 중 | **불확실** | IoT/edge AI 시장 자체가 빠르게 변화. ARM 생태계 경쟁 심화. 10년 테스트 불합격 가능성 높음. |

> **Reasoning chain** — AMBQ의 thesis는 "SPOT 기술 = 전력 효율에서 구조적 우위 → 웨어러블/IoT에서 design win 누적 → 규모 확보 → moat 형성"이라는 *순서*. 현재는 1~2단계. 3단계(규모)에 도달하지 못하면 기술만으로는 moat 유지 불가. 핵심 추적 변수 = design win 파이프라인 크기 + 매출 성장률.

---

## Castle 분석

### 성벽 (현재 moat — 잠정)
1. **SPOT 기술 (Sub-threshold Power Optimized Technology)** — 특허 기반. 일반 파운드리 공정 대비 전력 소모 10배 이상 절감 [추정]. 서브-스레숄드 전압 영역(0.5V 이하)에서 동작하는 회로 설계 노하우.
2. **Design win 누적** — Fossil Group 하이브리드 스마트워치, 기타 웨어러블/히어러블 OEM. _[unknown — 전체 design win 목록 및 고객 수 미공개]_
3. **Apollo SoC 제품 라인업** — Apollo4/Apollo510 시리즈. edge AI 기능 탑재 (Atomiq 플랫폼).

### 공격자 (Castle 외부 위협)
1. **ARM 생태계 대형 경쟁자** — STM, Nordic Semi, Renesas, Microchip 등. 자본·유통·고객 기반 압도적 차이.
2. **고객 집중 리스크** — 소수 대형 OEM 의존 가능성 높음. _[unknown — 고객별 매출 비중 미공개. 10-K에서 확인 필요]_
3. **ARM Cortex-M 로드맵** — ARM 자체의 저전력 IP 개선이 SPOT 기술 격차를 축소할 가능성.
4. **대형 반도체사 진입** — Qualcomm/Infineon 등이 웨어러블/IoT 전용 초저전력 칩 출시 시 시장 잠식.
5. **매출 규모 미달** — $72.5M(2025) 수준에서 R&D 투자 지속 가능성. 흑자 전환 실패 시 자본 소진 위험.

### 무한 자본 공격 테스트
> _"대형 반도체사가 무한 자본으로 초저전력 MCU를 공격하면?"_

**진단**: _[unknown — 실증 불가]_. 아직 시장 자체가 작아 대형사의 본격 진입 유인이 제한적. 시장이 커지면 진입 압력 증가. SPOT 특허가 방어벽이 되는지, 아니면 대안 기술로 우회 가능한지 — **이것이 thesis의 핵심 리스크**.

---

## ROIC 카테고리 분류 (버핏 3분류)

| 카테고리 | 해당 사업 | 비고 |
|---|---|---|
| **See's Candy 급** (capital-light, 고ROIC) | — | 해당 없음 (적자 상태) |
| **FlightSafety 후보** (capital-heavy, 양호한 리턴) | — | Fabless이므로 capital-light *구조*이나, 현재 적자 |
| **Airline 급** (capital-heavy, 저ROIC) | — | _[분류 유보 — 최소 4분기 흑자 실적 필요]_ |

> **판단 유보**: IPO 1년 미만, 순손실 상태. ROIC 카테고리 분류는 흑자 전환 + 2년 실적 누적 후 시도.

---

## Downside 시나리오 (Capital-preservation gate)

### 현재 Valuation 출발점

- **2026-05 기준** [추정]: 시총 ~$645M (stockanalysis.com 기준, 조회일 불명확).
- **멀티플**: 적자 기업 → P/E 의미 없음. EV/Revenue ~8~9× [추정].
- **해석**: IPO 프리미엄 + edge AI 테마 기대가 반영된 멀티플. 기대 대비 매출 성장 미달 시 급격한 멀티플 압축 가능.

### -50% 시나리오
- **trigger 후보**:
  1. 매출 성장 2분기 연속 한 자릿수 또는 마이너스
  2. 주요 design win 고객 이탈 (Fossil 등)
  3. gross margin 40% 하회 (가격 경쟁 심화 신호)
  4. 대형 반도체사의 동등 전력 효율 제품 출시 발표
  5. 현금 소진율 가속 + 추가 자본 조달 필요 (dilution)
- **대응 룰**: 위 5개 중 2개 동시 발생 시 thesis 재작성 또는 관찰 중단.

### Gate 4 — 포트폴리오 한도 체크 (매수 *직전* 필수)
- _[AMBQ 아직 포트폴리오 미편입. 편입 검토 시 user_investment_framework.md 한도 확인 필수.]_

---

## Moat 방향성 Timeline
- **2010~2024 (비상장)**: 기술 개발 + design win 누적 (관찰 불가)
- **2025-07 (IPO)**: 공개 시장 진입. 매출 $72.5M, 순손실 $36M.
- **2026~현재**: **잠정 관찰 단계** — moat 존재 여부 자체가 미확인.
- **2026 체크포인트**:
  - Q1/Q2 2026 매출 성장률 (컨센서스 +25% YoY)
  - gross margin 추이 (44.8% 유지/확대 여부)
  - 신규 design win 공시
  - Apollo510/Atomiq 양산 진척도
  - 고객 집중도 공시 (10-K)

---

## Unknown Backlog (Thick)

> 2025 IPO 기업. 공개 정보 극히 제한적. 아래 항목 모두 thesis 판단에 필수이나 현재 답 없음.

| # | 항목 | 중요도 | 확인 경로 | 상태 |
|---|---|---|---|---|
| 1 | SPOT 특허 포트폴리오 범위 및 만료 시점 | 높음 | USPTO / 10-K IP 섹션 | _[unknown]_ |
| 2 | 고객 집중도 (상위 3 고객 매출 비중) | 높음 | 10-K 고객 공시 | _[unknown]_ |
| 3 | R&D 비율 (매출 대비) | 중간 | 10-K/10-Q | _[unknown]_ |
| 4 | Apollo SoC 세대별 ASP 추이 | 중간 | IR 자료 / 컨퍼런스 콜 | _[unknown]_ |
| 5 | Atomiq (edge AI) 매출 기여도 | 높음 | 분기 실적 | _[unknown]_ |
| 6 | TAM 크기 및 시장 점유율 | 중간 | S-1 / 애널리스트 | _[unknown]_ |
| 7 | 경영진 주식 보유 비율 및 lockup 만료 | 중간 | DEF 14A / S-1 | _[unknown]_ |
| 8 | IPO 자금 사용 계획 vs 실제 | 중간 | 10-Q MD&A | _[unknown]_ |
| 9 | 경쟁사 대비 전력 효율 정량 비교 (독립 벤치마크) | 높음 | EEMBC / 독립 리뷰 | _[unknown]_ |
| 10 | 장기 계약 vs 스팟 주문 비율 | 중간 | 10-K | _[unknown]_ |
| 11 | 지역별 매출 비중 (중국 의존도) | 중간 | 10-K 지역 공시 | _[unknown]_ |
| 12 | Fabless 파운드리 의존도 (TSMC? 기타?) | 중간 | S-1 / 10-K | _[unknown]_ |
| 13 | 흑자 전환 예상 시점 (경영진 가이던스) | 높음 | 컨퍼런스 콜 | _[unknown]_ |
| 14 | stock-based compensation 규모 (dilution) | 중간 | 10-Q | _[unknown]_ |

---

## 10년 테스트
> _"2036년의 IoT/edge AI MCU 시장 구조를 지금 예측 가능한가?"_

**정직한 답**: 아니오. IoT/edge AI 시장은 태동기. 기술 표준, 승자 구조 모두 유동적. 버핏이 경고하는 "rapidly changing industry" 전형. **분기마다 재평가 필수**.

---

## Key Evidence (최근 6개월)
_IPO 초기 — 실적 누적 시 여기에 역링크._

- 2025-07: IPO ($24/share, NYSE). 총 조달 $110.4M.
- 2025 full year: 매출 $72.5M (-4.7% YoY), 순손실 ~$36M.
- 2025-Q3: non-GAAP GM 44.8% (+YoY).
- 2026 가이던스: 매출 ~$82M (+25% YoY) [애널리스트 추정].

---

**주의**: v1 잠정 draft. Unknown Backlog 14개 항목 중 절반 이상이 채워져야 thesis 격상(v2) 가능. 현재는 *관찰 단계* — 매수 판단 근거로 사용 금지.
