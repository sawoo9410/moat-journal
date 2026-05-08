# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

남은 작업: **B (신규 종목 8개 데이터 스캐폴드 + config 갱신)**.
A(텔레그램 출처 누수 차단), Phase 4(월간 누적 + 독립 분석 구조 개편)는 모두 구현·반영 완료.

---

## B. 신규 종목 8개 추가

config 4종목(GOOGL, MCD, KO, O) → 12종목으로 확장.

추가 종목 (8개): **OXY, QCOM, NVDA, NXPI, TXN, AMZN, AMBQ, AVGO**

종목 식별:
- OXY — Occidental Petroleum (에너지, 배당, Berkshire 대주주)
- QCOM — Qualcomm (반도체, 모바일/IoT, 배당)
- NVDA — NVIDIA (반도체, AI 가속기)
- NXPI — NXP Semiconductors (반도체, 자동차/IoT, 배당)
- TXN — Texas Instruments (반도체, 아날로그/임베디드, 배당 compounder)
- AMZN — Amazon (이커머스 + AWS, 무배당 성장)
- AMBQ — **Ambiq Micro** (반도체, 초저전력 칩, 2025 IPO)
- AVGO — Broadcom (반도체, 인프라 + VMware, 배당 성장)

### B.1 종목별 데이터 스캐폴드 — 산출물 명세

각 종목당 아래 5종 파일 생성. 기존 KO/MCD/GOOGL/O 패턴 그대로.

| 파일 | 모든 종목 | 분량 (참고) | 내용 |
|------|----------|------------|------|
| `companies/{TICKER}/moat.md` | ✅ | 50~150줄 | 버핏식 4축(pricing power / switching cost / network effect / cost advantage) + Castle (성벽·공격자) + ROIC 요약 + Unknown Backlog |
| `companies/{TICKER}/profile.yaml` | ✅ | 45~90줄 | ticker, name, aliases, sector, sub_segments, established, tracking_since, tracking_purpose, related, keywords. 배당지급 종목은 `dividend:` 블록 포함 |
| `companies/{TICKER}/dividend.md` | ✅ | 50~130줄 | **전 종목 작성**. 배당지급 종목은 Snapshot 표 + Coverage/Sustainability + 갱신 트리거. 무배당(NVDA, AMZN, AMBQ)은 "현재 무배당 — 자본정책: 자사주매입/재투자 중심" 1~2 문단으로 짧게 기록. 향후 배당 도입 시 갱신. |
| `companies/{TICKER}/pre-2025.md` | OXY만 | 50~100줄 | 2025 이전 누적 컨텍스트 (OXY는 2019 Berkshire 우선주, Anadarko 합병, 2022 정점 등). 나머지 종목은 미생성. |
| `companies/{TICKER}/moat-changelog.md` | ✅ | 1~3줄 | `v1 (2026-05-09): 초기 thesis 작성` 정도의 1줄 entry |

**총 파일 수**: 8 moat + 8 profile + 8 dividend + 1 pre-2025 + 8 changelog = **33개**.

### B.2 데이터 모드 / 작성 원칙

- **지식 컷오프 기반 + 마크 일관 사용**: `[추정]` / `[검증 필요]` / `[unknown]` / `[YYYY-MM 기준]` 표기. 정확한 숫자는 다음 daily 사이클 + 분기 실적에서 보강. 기존 KO/MCD/GOOGL/O 패턴과 동일.
- **버핏 thesis 본질에 집중**: 가격 추적이 아니라 4축 변화 평가 가능한 thesis 골격. 숫자는 보조.
- **AMBQ 특별 처리**: 2025 IPO로 상장 이력 짧음 → moat thesis는 *잠정(tentative)* 표기, Unknown Backlog 두텁게, pre-2025.md 생략.
- **무배당 종목 dividend.md**: NVDA / AMZN / AMBQ는 "현재 무배당. 자본정책 = {자사주매입 / 재투자}. 도입 트리거: {조건}" 형식. 추후 배당 도입 시 동일 파일에 Snapshot 추가.

### B.3 작성 순서 (각 세션 내, 종목당)

1. **profile.yaml** 먼저 — 식별·관계·키워드 확정 (다른 파일의 인덱스 역할)
2. **moat.md** — thesis 본문 (One-liner + 4축 표 + Castle + ROIC 요약 + Unknown Backlog)
3. **dividend.md** — 배당주는 풀 양식, 무배당은 짧게
4. **pre-2025.md** — OXY만
5. **moat-changelog.md** — v1 작성일 1줄

### B.4 실행 방식 — 그룹 2세션 분할 (권장)

**세션 1: 반도체 6종 — QCOM, NVDA, NXPI, TXN, AVGO, AMBQ**
- 동일 산업군이라 4축 비교 톤·용어 일관성 유지하기 좋음
- 산출물: 6 × 4파일(moat/profile/dividend/changelog) = 24파일

**세션 2: 비반도체 2종 — OXY, AMZN**
- 성격 다른 종목 별도 처리
- 산출물: 2 × 4파일 + OXY pre-2025.md = 9파일

각 세션 끝에 commit. 단일 세션 일괄(8종목 33파일)도 가능하나 컨텍스트 부담 + 종목 간 톤 흔들림 위험.

### B.5 마무리 (마지막 세션 끝)

1. `automation/config.yaml`의 `tickers` 12개로 갱신:
   ```yaml
   tickers:
     - GOOGL
     - MCD
     - KO
     - O
     - OXY
     - QCOM
     - NVDA
     - NXPI
     - TXN
     - AMZN
     - AMBQ      # Ambiq Micro
     - AVGO
   ```
2. `todo.md`에서 B 섹션 전체 제거 (목표 종결)
3. `companies/{8 tickers}/`, `automation/config.yaml`, `todo.md` 일괄 commit + push

### B.6 LaunchAgent / 자동화 변경 불필요

LaunchAgent wrapper는 config.yaml의 tickers를 읽으므로 추가 작업 없음.
12종목 × claude --print(평균 30~60s) ≈ 6~12분 → 기존 timeout=300s/종목 그대로 충분.
