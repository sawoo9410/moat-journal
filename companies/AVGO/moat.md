# AVGO Moat Thesis (버핏식)
_Last updated: 2026-05-09 · Version: v1 (draft — 사용자 검토 필요)_
**Lane**: `compounder + dividend` _(배당 성장주 — 배당 추적 포함. `dividend.md` 참조.)_

## One-liner
커스텀 ASIC 설계 독점(hyperscaler 3사 XPU) × 네트워킹 스위칭 지배력 × VMware 인프라 소프트웨어 락인 × Hock Tan의 M&A 규율. 반도체 + 소프트웨어 혼합으로 **60%+ 영업이익률**이라는 반도체 업계 최상위 수익성.

> **용어 메모** — _커스텀 ASIC (XPU)_: 범용 GPU 대신 특정 hyperscaler(Google, Meta 등)의 AI 워크로드에 최적화된 맞춤형 칩. 설계에 2~3년 걸리므로 한번 채택되면 전환비용이 매우 높음.

---

## Buffett 4축 현황

| 축 | 현재 상태 | 방향 | 핵심 숫자 / 비고 |
|---|---|---|---|
| ROIC 품질 | **~21%** [추정] | **개선 방향** | stockanalysis 기준 ROIC ~21%. VMware 인수 부채 상환 + 소프트웨어 마진 개선으로 투하자본 효율 상승 중. FY2025 FCF $26.9B (+39% YoY). ※ 출처: stockanalysis.com (2026-05) |
| 가격결정력 | 매우 강함 | 유지 | 커스텀 ASIC은 고객별 맞춤 → 가격 협상력 높음. VMware 라이선싱 → 구독 전환으로 가격 인상 실현. 네트워킹 ASIC 시장 과점 |
| 자본집약도 | **fabless** — 상대적 경량 | 유지 | TSMC 외주 제조. R&D 집중 모델. capex/매출 비중 낮음 (소프트웨어 부문은 거의 0) |
| 산업 안정성 | AI 수요 급증기 — "changing but favorable" | **호재 방향** | 커스텀 ASIC + 네트워킹은 AI 인프라 필수. 다만 AI capex 사이클 지속성은 [unknown] |

> **Reasoning chain** — ROIC가 GOOGL 대비 낮아 보이지만(~21% vs 33%), VMware 인수($61B)로 투하자본이 급증한 상태. 부채 상환 + 소프트웨어 마진(기존 하드웨어 50% → 소프트웨어 90%+) 반영되면 ROIC는 구조적으로 상승. FCF 마진 42%+(FY2025)는 이미 동종 최상위.

---

## Castle 분석

### 성벽 (현재 moat)
1. **커스텀 ASIC 설계 독점** — hyperscaler 3사(Google, Meta, ByteDance [추정])와 다년 계약. 설계 2~3년 → 전환비용 극대. 경쟁사 진입까지 최소 2~3년 리드타임
2. **네트워킹 ASIC 지배력** — Memory Fabric(Jericho/Ramon), Ethernet 스위칭(Memory) 시장 70%+ 점유 [추정]. AI 클러스터 간 연결의 사실상 표준
3. **VMware 인프라 소프트웨어** — Fortune 500 대부분이 VMware 기반 가상화. 구독 전환으로 recurring revenue + 가격결정력 강화
4. **Hock Tan의 M&A 규율** — "선택과 집중" 철학. 인수 후 비핵심 사업 정리, 마진 극대화. CA Technologies·Symantec·VMware 모두 인수 후 마진 대폭 개선
5. **Wireless RF 프론트엔드** — Apple iPhone에 Wi-Fi/Bluetooth/RF 공급. 장기 공급 계약

### 공격자 (Castle 외부 위협)
1. **고객 집중 리스크** — Apple이 RF 내재화 추진 중 (자체 Wi-Fi/모뎀 칩). 매출의 상당 부분이 Apple 의존 [unknown — 정확 비중 비공시]
2. **hyperscaler 자체 설계** — Google(TPU는 자체), Amazon(Trainium/Inferentia). 커스텀 ASIC 고객이 경쟁자가 될 수 있음
3. **커스텀 ASIC 경쟁 진입** — Marvell(MRVL), 신규 진입자(Alchip, MediaTek). 설계 인력 확보 경쟁 치열
4. **VMware 통합 리스크** — 라이선싱 모델 변경으로 고객 이탈 가능성. OpenStack/Nutanix 등 대안 존재
5. **AI capex 사이클 종료** — hyperscaler의 AI 투자 감속 시 커스텀 ASIC + 네트워킹 매출 동시 타격

### 무한 자본 공격 테스트
> _"Intel이 무한 자본으로 커스텀 ASIC + 네트워킹을 공격하면 점유율이 유의미하게 이동하는가?"_

**평가**: Intel은 2020년대 초반부터 파운드리·FPGA·네트워킹에 투자했으나, Broadcom의 커스텀 ASIC 설계 역량(수천 명의 전문 엔지니어 + hyperscaler와의 다년 협업 관계)을 재현하기 어려움. **castle 유효** — 단, NVDA가 커스텀 ASIC 시장 진입 시 더 심각한 위협. _[이 평가는 정성적 — 시장점유율 정량 데이터 필요]_

---

## ROIC 카테고리 분류 (버핏 3분류)

| 카테고리 | 해당 사업 | 비고 |
|---|---|---|
| **See's Candy 급** (capital-light, 고ROIC) | Infrastructure Software (VMware·CA·Symantec) | 소프트웨어는 한계비용 ~0. 인수 후 비용 절감으로 마진 극대화. 구독 전환 완료 시 recurring 수익 |
| **FlightSafety 급** (capital-moderate, 양호한 리턴) | Semiconductor (커스텀 ASIC·네트워킹·무선) | fabless 모델이라 자본집약도 낮지만, R&D 비용이 높음. 고객 락인으로 안정적 리턴 |
| **Airline 급** (capital-heavy, 저ROIC) | — | 해당 사업 없음. Hock Tan의 철학 = 저ROIC 사업은 매각/정리 |

---

## Unknown Backlog

> 채워야 할 핵심 미지수. 분기 IR·10-K 발표 시 업데이트.

| 항목 | 어디서 확인 | 우선순위 |
|---|---|---|
| Apple 매출 비중 정확치 | 10-K 고객 집중도 공시 | 높음 |
| 커스텀 ASIC 고객사 3사 정확한 명단 | IR 콜 + 업계 보도 | 높음 |
| AI 반도체 매출 vs 전통 반도체 매출 비중 | 분기 IR (FY2026-Q2+) | 높음 |
| VMware 구독 전환율 (ARR) 현황 | 분기 IR 소프트웨어 세그먼트 | 중간 |
| Net debt / EBITDA 추이 | 10-Q 재무제표 | 중간 |
| FY2026 capex 가이던스 | Q2 IR 콜 | 중간 |
| 네트워킹 ASIC 시장점유율 정량 | 3자 리서치 (Dell'Oro 등) | 낮음 |

---

## 10년 테스트
> _"2036년의 반도체/AI 인프라 시장 구조를 지금 예측 가능한가?"_

**답변**: 부분적으로 가능.
- **예측 가능**: 데이터센터 네트워킹, 엔터프라이즈 가상화 수요는 10년 후에도 존재. Broadcom의 설계 역량 + 고객 전환비용은 구조적.
- **예측 불가**: AI ASIC의 아키텍처 진화 속도, hyperscaler의 자체 설계 확대 범위, Apple의 RF 내재화 시점.
- **결론**: 전통 반도체+소프트웨어 부분은 "stable industry", AI ASIC 부분은 "rapidly changing". **혼합형** → 분기마다 AI 비중 변화 추적 필수.

---

## Moat 방향성 Timeline
- **2009~2019 (Avago→Broadcom M&A 시대)**: widening — LSI·Brocade·CA 연속 인수로 확장
- **2019~2023 (VMware 인수 전후)**: widening — $61B VMware 인수로 소프트웨어 moat 추가
- **2024~현재 (AI ASIC 폭발)**: **accelerating** — AI 수요로 커스텀 ASIC + 네트워킹 동시 성장
- **2026 분기 체크포인트**:
  - AI 반도체 매출 성장률 지속성 (FY2026-Q2 IR)
  - VMware ARR 전환 완료도
  - Apple Wi-Fi/RF 자체 칩 진척 (WWDC 2026, iPhone 18 [추정])
  - hyperscaler capex 가이던스 변화

---

**주의**: v1 draft. Unknown Backlog의 항목들은 분기 IR 발표 직후 채워넣고, 채워질 때마다 `moat-changelog.md`에 기록.
