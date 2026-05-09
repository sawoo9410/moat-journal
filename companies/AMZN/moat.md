# AMZN Moat Thesis (버핏식)
_Last updated: 2026-05-09 · Version: v1 (draft)_
**Lane**: `compounder` _(무배당 — 총수익 관점. `dividend.md` = stub.)_

## One-liner
AWS 클라우드 #1(점유율 ~30%) + e-commerce 물류 플라이휠 + Prime 2억+ 회원 락인. 본업 e-commerce는 박리다매이나 AWS·광고가 이익 엔진.

---

## Buffett 4축 현황

| 축 | 현재 상태 | 방향 | 핵심 숫자 / 비고 |
|---|---|---|---|
| ROIC 품질 | **2025: ~14%** [추정] · 5Y 추이: 18.5→-2.1→9.8→15.7→14.0 | **회복 후 정체** | 2022 적자(-2.1%)에서 회복했으나 capex 급증으로 2024→2025 소폭 하락. 출처마다 산식 차이 큼(gurufocus 14%, alphaspread 11~12%). 10-K 기준 재계산 필요 [unknown] |
| 가격결정력 | Prime 가격 인상 이력 + AWS 종량제 | 유지 | Prime: $99→$119→$139(미국). 고객 이탈 제한적 — 플라이휠 락인 효과. AWS: 경쟁 심화로 가격 인하 압력 존재하나 전환비용 높음 |
| 자본집약도 | capex 급증 | **매우 heavy** | 2024 ~$83B → 2025 $131.8B → 2026 가이던스 $200B. FCF 2024 $38.2B → 2025 $11.2B(-71%). 자본집약도 빠르게 악화 |
| 산업 안정성 | e-commerce: stable / Cloud+AI: changing | **혼재** | e-commerce 구조는 안정적이나, AI 인프라 경쟁은 "rapidly changing" 영역 |

> **Reasoning chain** — Amazon의 ROIC 딜레마: 2025 매출 $717B(+12%), 영업이익 $80B(+17%)로 본업은 건재. 그러나 capex $131.8B(매출의 18.4%)가 투하자본(분모)을 급격히 키움. 2026 $200B capex 시 FCF 추가 압축 불가피. **핵심 질문**: AI capex가 AWS 매출 가속으로 이어지는가, 아니면 "Airline급" 자본 함정인가.

---

## Castle 분석

### 성벽 (현재 moat)
1. **AWS 클라우드 #1** — 글로벌 IaaS 점유율 ~30%(2025). Azure(20%)·GCP(13%) 대비 리드. 엔터프라이즈 전환비용 높음.
2. **물류 네트워크** — 미국 내 자체 배송망(same-day/next-day). 20년+ 투자 누적. 후발주자 복제 비용 막대.
3. **Prime 플라이휠** — 회원 2억+ [추정, 공식 미공개]. 무료배송·Prime Video·Music 번들 → 높은 락인.
4. **광고 사업** — 2025 매출 ~$68B(+22% YoY). 쇼핑 의도 데이터 기반 → Google/Meta와 차별화된 high-intent 광고.
5. **규모의 경제** — 매출 $717B. 물류·기술 고정비를 압도적 매출로 분산.

### 공격자 (Castle 외부 위협)
1. **반독점 규제** — FTC 소송(2023~) 진행 중. 마켓플레이스 관행·셀러 수수료 구조 변경 리스크.
2. **Azure/GCP 경쟁** — MS의 OpenAI 통합, Google의 Gemini. AI 워크로드 시장에서 점유율 방어 필요.
3. **e-commerce 박리다매 마진** — North America 영업이익률 ~5~6%. 물류비 상승 시 마진 압축 취약.
4. **Temu/Shein** — 초저가 cross-border 모델. 미국 de minimis 면세 변경 시 완화되나, 가격 민감 고객층 잠식 중.
5. **대규모 capex 리스크** — 2026 $200B. AI capex가 매출로 전환되지 않으면 ROIC 구조적 하락.

---

## ROIC 카테고리 분류 (버핏 3분류)

| 카테고리 | 해당 사업 | 비고 |
|---|---|---|
| **See's Candy 급** (capital-light, 고ROIC) | 광고 사업 | 기존 e-commerce 트래픽 위 광고 수익화. 추가 자본 거의 없이 매출 $68B. marginal ROIC 매우 높음 추정 |
| **FlightSafety 후보** (capital-heavy, 양호한 리턴) | AWS | 2025 영업이익 $45.6B(Amazon 전체의 ~57%). heavy capex이나 높은 이익률(~37%). 세그먼트 ROIC [unknown — capex 배분 미공시] |
| **Airline 급** (capital-heavy, 저ROIC) | e-commerce 물류 | 물류 네트워크 = moat이지만 자본수익률은 낮음. "고객 경험 투자"로 정당화하나 standalone ROIC [unknown] |

---

## Unknown Backlog

- [ ] ROIC 시계열: 출처별 산식 차이 큼. 10-K NOPAT/IC 기준 재계산 필요
- [ ] AWS 세그먼트 ROIC: capex 중 AWS 배분 비율 미공시 (콘퍼런스 콜 코멘트로만 추정)
- [ ] e-commerce 물류 세그먼트 standalone 수익성
- [ ] Prime 정확한 회원 수: 2021년 이후 공식 발표 없음. 2억~2.6억 추정 범위
- [ ] FTC 소송 결과 및 마켓플레이스 관행 변경 영향 범위
- [ ] 2026 $200B capex의 AWS/물류/기타 배분 비율
- [ ] 자사주매입 규모·프로그램 현황 [unknown]

---

## 10년 테스트
> _"2036년의 e-commerce + 클라우드 시장 구조를 지금 예측 가능한가?"_

**e-commerce**: 상당 부분 예측 가능. 온라인 침투율 상승 추세 지속, Amazon 물류 우위 유지 가능성 높음. **stable**.

**AWS/클라우드**: AI 워크로드 폭증으로 시장 자체는 성장하나, AI 칩·모델·플랫폼 경쟁 구조는 빠르게 변동. Azure+OpenAI, Google+Gemini 등 경쟁 구도 유동적. **"changing" 영역**.

**종합**: e-commerce moat는 10년 테스트 통과 가능성 높으나, AWS의 AI 시대 경쟁우위는 분기 재평가 필요. 버핏 관점에서 **혼합 판정** — e-commerce만으로는 compounder, AWS 방향에 따라 thesis 강도 변동.

---

## Key Evidence (최근 6개월)
_파일럿 초기 — 월 파일 entry 누적 시 여기에 역링크. 신호강도 >= 3 entry만._

- 2025 연간 실적: 매출 $717B(+12%), 영업이익 $80B(+17%), AWS $128.7B(+24%)
- 2026 capex 가이던스: $200B (AI 인프라 집중)
- FCF 급감: $38.2B → $11.2B (-71%, capex 증가 영향)

---

**주의**: v1 draft. ROIC·세그먼트 수익성의 `[unknown]` 박스는 10-K 정밀 분석 및 분기 IR 후 갱신 필요.
