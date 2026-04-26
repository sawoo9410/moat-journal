# GOOGL Moat Changelog

_moat.md가 변경될 때마다 여기에 이력을 남깁니다._
_과거 thesis는 이 파일에서만 확인 가능 — **survivorship bias 방지용이므로 삭제 금지**._

---

## v4 — 2026-04-26 (patch — unknown 채우기 + Gate 4)

리뷰에서 지적된 *채울 수 있는 unknown* + *Gate 4 cross-ref 누락* 보강. **실질 thesis 변화 없음**, 정량 보강.

### 채워넣은 unknown (출처 명시)
- **ROIC 시계열 2021~2025** (stockanalysis.com, 2026-04-24): 45.7 / 36.5 / 36.3 / 38.8 / **33.4**.
  - 정성 추정 "역사적 25~30%"는 보수적이었음 — 실제는 33~46% 구간.
  - **2024→2025 -5.4%p 하락**으로 reasoning chain의 ROIC 하락 가설 1차 정량 확인 (capex $52B → $75B 시기).
  - ※ stockanalysis 산식 ≠ Buffett NOPAT/IC. 10-K 재계산은 사용자 영역.
- **Bing 글로벌 점유율** (StatCounter, 2026-03): Google 89.85% / **Bing 5.13%**. 무한 자본 공격 테스트 castle 유효성 1차 정량 통과.
- **현재 valuation** (stockanalysis.com, 2026-04-24): 주가 $344.40 / 시총 $4.17T / TTM P/E 31.89 / Forward P/E 29.44 / EV/EBITDA 27.34 / EV/EBIT 31.82.
  - Downside 섹션의 -50% 시나리오 baseline 명시화.
  - 기존 "P/E 25× → 15×" 압축 시나리오를 **"32× → 15×"** 로 갱신.

### 신설 섹션
- **`### 현재 Valuation 출발점`** (Downside 섹션 최상단) — 모든 downside gate baseline.
- **`### Gate 4 — 포트폴리오 한도 체크`** — `user_investment_framework.md` 한도 cross-ref. plan.md §0.4 의 5 gates 중 누락이었던 항목.

### 미해결 (다음 v5에서)
- Pre-2021 ROIC (2015~2020) — stockanalysis는 5년만 노출, macrotrends 페이월. 10-K 직접 또는 다른 무료 소스 필요.
- `## Capital Allocation` 섹션 신설 (capex / buyback / 배당 / M&A 비중·의도).
- `## Reinvestment Runway` 섹션 (AI capex → 매출 전환 *속도* 추적 룰).
- `## Unknown Backlog` consolidated 리스트.

---

## v3 — 2026-04-26

- **프레임 유지, 운영성 보강**. Buffett 4축/Castle/ROIC 3분류 구조는 그대로.
- 추가:
  - 헤더에 **`Lane: compounder`** 명시 (user_profile.md 룰: 회사 분석 시작 시 레인 선언).
  - 4축 표에 **숫자 슬롯** + **`_[unknown — 어디서 보면 됨]_` 박스** — thesis-evidence 분리(plan.md §6.1) 방지.
  - **Reasoning chain** 박스 — ROIC 하락 산수 노출(초보 멘토링).
  - **Downside 시나리오 섹션** 신설 — Worst case + -50% trigger 후보 4종. 매수 직전 capital-preservation gate.
  - **Active Threats 진행률 추적 표** 부활 — Castle 공격자는 *구조*, 이 표는 *진행률*.
  - **가격결정력 실측 지표** 섹션에 해석 룰 추가 — "RPM 성장 없이 매출 성장 = 가격결정력 약화 신호".
  - 용어 메모(See's Candy 정의), Apple Intelligence를 분기 체크포인트에 명시.
- 수정:
  - GCP를 FlightSafety **확정** → **후보**로 격하 (자본조정 ROIC 미검증).
  - Search 광고 = See's Candy 분류에 **"증분 관점" 단서** — 절대 capex는 무겁지만 marginal ROIC가 high.
  - Waymo "상업화 전" → **"commercial 단계(SF/LA/Phoenix), unit economics unknown"** 으로 갱신.
- 실질 thesis 변화 없음. 운영성·정량성·capital-preservation 보강만.

## v2 — 2026-04-24
- 프레임워크를 **버핏식(2007 shareholder letter 기반)으로 전면 개편**.
- 핵심 변경:
  - Moat Components 4개 나열 → **Buffett 4축**(ROIC / 가격결정력 / 자본집약도 / 산업안정성) + **Castle 분석** 구조로 교체.
  - **ROIC 카테고리 분류** (See's Candy / FlightSafety / Airline) 추가.
  - **"무한 자본 공격 테스트"** 명시 — MS가 무한 자본으로 Bing+Copilot 공격 시 castle 유효성 평가.
  - **Moat 방향성 Timeline** 기록 — 역사적 widening → 현재 erosion 리스크 관찰.
  - **10년 테스트** 추가 — "rapidly changing industry" 진단 명시.
- 실질 thesis 변화는 없음. **평가 프레임만 교체**.

## v1 — 2026-04-23
- 파일럿 시작. `moat.md` 최초 작성 (draft).
- 초기 구성요소: (1) 검색 데이터 플라이휠 (2) 유통 (3) AI 인프라(TPU) (4) 보조 플라이휠(YouTube/Android).
- 주요 위협: DOJ remedy, AI-native 검색, EU DMA, Apple 자체 LLM.
- **근거**: 2025 이전까지 공개된 일반 분석 + 실제 월별 수집은 2026-04부터 시작.
- **미결**: remedy 확정 후 "유통" 강도 재평가 필요.
