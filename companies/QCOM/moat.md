# QCOM Moat Thesis (버핏식)
_Last updated: 2026-05-09 · Version: v1 (draft)_
**Lane**: `compounder` + `dividend` _(배당 추적 병행 — dividend.md 참조.)_

## One-liner
5G 셀룰러 특허 포트폴리오(140,000+건)의 라이선싱 수익 × Snapdragon SoC의 프리미엄 Android 지배력 — **칩을 팔면서 동시에 경쟁사에게도 특허료를 받는** 이중 moat 구조.

---

## Buffett 4축 현황

| 축 | 현재 상태 | 방향 | 핵심 숫자 / 비고 |
|---|---|---|---|
| ROIC 품질 | **FY2025: 13.2%** [추정] | 안정 | ROE 26.1%, ROIC > WACC(9.1%). R&D 집약적이나 라이선싱(QTL)이 capital-light 수익 제공. ※ 출처: roic.ai/artificall (2026-05) |
| 가격결정력 | QTL: 특허 로열티 (기기당 %) / QCT: 프리미엄 SoC 가격 | 유지 (구조적) | QTL은 5G 표준필수특허(SEP) 기반 — 경쟁사가 피할 수 없는 구조. QCT는 프리미엄 AP 점유율 60%+로 가격 유지력 보유. |
| 자본집약도 | R&D 중심 (제조는 파운드리 위탁) | **light** | 팹리스 모델 — TSMC/삼성에 위탁. capex 부담은 팹 보유 경쟁사(Intel) 대비 경미. R&D 비율 ~20%+ |
| 산업 안정성 | 5G → 6G 전환, AI Edge 확장 | 변화 중이나 **점진적** | 무선 통신 표준 세대교체는 10년 주기. 반도체는 순환적이나 QCOM은 통신표준 소유로 안정성 확보. |

> **Reasoning chain** — QCOM의 이중 moat 산수: QTL(라이선싱)은 매출 $5.6B에 영업이익률 70%+ 추정 → capital 거의 없이 발생하는 수익. QCT(칩)는 매출 $38.4B으로 규모가 크지만 마진은 QTL보다 낮음. **QTL이 전체 이익의 상당 부분을 차지하면서 ROIC를 끌어올리는 구조**. QTL 계약 갱신 리스크가 thesis의 핵심 변수.

---

## Castle 분석

### 성벽 (현재 moat)
1. **5G 표준필수특허(SEP) 포트폴리오** — 140,000+ 특허/출원. CDMA→WCDMA→LTE→5G 30년 누적. 경쟁사(Apple·삼성·화웨이)도 로열티 지불 의무.
2. **Snapdragon 프리미엄 지배력** — 프리미엄 Android AP 점유율 60%+, 5G 베이스밴드 점유율 ~70%.
3. **자동차·IoT 확장** — Snapdragon Digital Chassis 디자인 파이프라인 $45B. FY2025 자동차 매출 분기 $1B+ 돌파.
4. **팹리스 자본 효율** — 제조 위탁으로 capex 부담 경미. R&D 집중 가능.

### 공격자 (Castle 외부 위협)
1. **Apple 자체 모뎀** — iPhone 모뎀 내재화 추진. QCOM iPhone 매출(QCT의 상당 비중) 직격.
2. **MediaTek 추격** — 중저가 5G 칩 시장에서 점유율 40% 확보. 프리미엄 시장 진출 시도 중.
3. **QTL 계약 분쟁 리스크** — 과거 Apple·화웨이와 대형 소송 이력. 계약 갱신 실패 시 QTL 매출 급감.
4. **ARM 자체 칩 설계 확대** — ARM이 직접 GPU·CPU 설계 라이선스 제한 시 Snapdragon 아키텍처 위협.
5. **NVIDIA Edge AI** — 자동차·IoT에서 NVIDIA와 직접 경쟁 심화.

### 무한 자본 공격 테스트
> _"MediaTek이 무한 자본으로 프리미엄 SoC 시장을 공격하면 Snapdragon 점유율이 유의미하게 이동하는가?"_

**실증**: MediaTek은 중저가 시장에서 물량 점유율 40%를 확보했으나, 프리미엄($400+ 기기)에서는 Snapdragon 8 시리즈가 여전히 지배적. OEM 벤치마크·브랜드 인지도·통신사 인증에서 Snapdragon의 선행 우위 유지.
**해석**: *프리미엄 SoC*에서는 castle 유효. 다만 **중저가 시장 잠식**은 이미 진행 중이며, 프리미엄 경계가 하향 이동하면 위협 확대.

---

## ROIC 카테고리 분류 (버핏 3분류)

| 카테고리 | 해당 사업 | 비고 |
|---|---|---|
| **See's Candy 급** (capital-light, 고ROIC) | QTL (특허 라이선싱) | 추가 자본 거의 없이 로열티 수취. 영업이익률 70%+ [추정]. moat의 진짜 엔진. |
| **FlightSafety 후보** (capital-heavy, 양호한 리턴) | QCT (칩 설계·판매) | 팹리스라 제조 capex는 없으나 R&D 투자 연 $8B+ [추정]. 규모의 경제로 양호한 마진. |
| **신규 투자** (성장 단계, ROIC 미확정) | Automotive · IoT | 디자인 파이프라인 $45B이나 현재 매출 규모 대비 수익성 검증 필요. [unknown — 세그먼트별 ROIC 미공시] |

---

## Downside 시나리오 (Capital-preservation gate)

### 현재 Valuation 출발점

- **2026-05 기준**: 주가·시총·멀티플 [unknown — 최신 데이터 확인 필요]
- **갱신 룰**: 분기 IR 직후 또는 ±15% 가격 변동 시.

### Worst case — moat 붕괴 최단 시나리오
- **트리거 조합**: Apple 모뎀 내재화 완료(iPhone 매출 전량 상실) + QTL 주요 라이선시(삼성·중국 OEM) 계약 분쟁으로 로열티 매출 -30%.
- **결과 추정**: QCT 매출 -15~20%, QTL 매출 -30%. 합산 영업이익 -40%+. **멀티플 압축 동시 발생 시 -50~60% 시나리오**.
- **확률 자가평가**: _[unknown — 사용자 판단 영역. Apple 모뎀 일정이 핵심 변수]_

### -50% 시나리오 (주가 기준)
- **trigger 후보**:
  1. Apple 자체 모뎀 탑재 iPhone 출시 확정 발표
  2. QTL 주요 계약 분쟁 재발 (삼성·중국 OEM)
  3. Snapdragon 프리미엄 점유율 50% 이하 하락
  4. 거시 — 반도체 사이클 하락 + 스마트폰 시장 역성장
- **대응 룰 후보**: 위 4개 중 2개 동시 발생 시 비중 재검토. _구체 임계치는 사용자 정의 영역._

---

## Moat 방향성 Timeline
- **역사적 (2000~2019)**: widening — CDMA→LTE 특허 누적, Snapdragon 지배력 확장
- **2019~2021 (Apple 소송·화해)**: uncertain — 대규모 소송 후 화해, 모뎀 공급 재개
- **2022~현재 (2026-05)**: **stable with transition risks** — 5G 성숙, Apple 모뎀 내재화 진행, 자동차·IoT 다각화 추진

---

## Active Threats — 분기 진행률 추적

| 위협 | 현재 상태 | 다음 트리거 | 마지막 업데이트 |
|---|---|---|---|
| Apple 자체 모뎀 | 개발 진행 중, 일부 모델 탑재 시작 [추정] | iPhone 전 라인업 자체 모뎀 전환 시점 | 2026-05-09 |
| MediaTek 프리미엄 진출 | 중저가 지배, 프리미엄 도전 중 | Dimensity 프리미엄 AP OEM 채택 확대 여부 | 2026-05-09 |
| QTL 계약 리스크 | 주요 계약 안정 유지 중 | 삼성·중국 OEM 계약 갱신 일정 | 2026-05-09 |
| ARM 관계 변화 | ARM IPO 후 라이선스 조건 재협상 리스크 | ARM v9+ 라이선스 갱신 | 2026-05-09 |

---

## Unknown Backlog

- [ ] FY2025 10-K 기준 정확한 ROIC (NOPAT/IC 정의로 재계산)
- [ ] QTL 세그먼트 영업이익률 정확 수치 (10-K 세그먼트 공시)
- [ ] Apple 모뎀 내재화 일정 — 전 라인업 전환 예상 시점
- [ ] 자동차·IoT 세그먼트별 ROIC 또는 영업이익률
- [ ] Snapdragon X Elite PC 시장 진출 성과 (Windows on ARM)
- [ ] 현재 valuation 멀티플 (주가·P/E·EV/EBITDA)
- [ ] QTL 주요 라이선시별 계약 만료 일정
- [ ] 5G-Advanced / 6G 특허 출원 현황

---

## 10년 테스트
> _"2036년에도 QCOM이 무선 통신 특허 로열티를 받고, Snapdragon이 프리미엄 모바일 AP를 지배하고 있을까?"_

**정직한 답**: QTL은 **예** — 무선 통신 표준은 10년 주기로 전환되며, QCOM의 30년 누적 특허는 5G→6G에서도 유효할 가능성 높음. 표준필수특허는 FRAND 의무가 있으나, 그 자체가 moat.
QCT(칩)는 **불확실** — Apple 모뎀 내재화, ARM 자체 설계 확대, MediaTek 추격 등 변수. 다만 팹리스 모델의 유연성과 자동차·IoT 다각화가 방어 요소.

따라서 **QTL은 연간 모니터링, QCT는 분기 모니터링** 필요.

---

## Key Evidence (최근 6개월)
_파일럿 초기 — 월 파일 entry 누적 시 여기에 역링크. 신호강도 ≥3 entry만._

_(아직 월별 수집 없음 — 2026-05부터 시작)_

---

**주의**: v1 draft. 4축 표·ROIC 시계열·Valuation의 `[unknown]` 박스는 분기 IR 발표 직후 사용자가 채워넣고, 채워질 때마다 `moat-changelog.md`에 기록.
