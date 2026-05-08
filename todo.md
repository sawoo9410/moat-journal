# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

남은 작업: **B (신규 종목 8개 데이터 스캐폴드 + config 갱신)**.
A(텔레그램 출처 누수 차단), Phase 4(월간 누적 + 독립 분석 구조 개편)는 모두 구현·반영 완료.

---

## B. 신규 종목 8개 추가

config 4종목(GOOGL, MCD, KO, O) → 12종목으로 확장.

추가 종목 (8개): **OXY, QCOM, NVDA, NXPI, TXN, AMZN, AMBQ, AVGO**

종목 식별:
- OXY — Occidental Petroleum (에너지, 배당)
- QCOM — Qualcomm (반도체, 모바일/IoT, 배당)
- NVDA — NVIDIA (반도체, AI 가속기)
- NXPI — NXP Semiconductors (반도체, 자동차/IoT, 배당)
- TXN — Texas Instruments (반도체, 아날로그/임베디드, 배당 compounder)
- AMZN — Amazon (이커머스 + AWS)
- AMBQ — **Ambiq Micro** (반도체, 초저전력 칩, 2025 IPO)
- AVGO — Broadcom (반도체, 인프라 + VMware, 배당 성장)

### B.1 종목별 데이터 스캐폴드 생성 (계획 세션 작업)

각 종목당 다음 파일 생성. 기존 KO/MCD/GOOGL/O 패턴 따름.

| 파일 | 필수 여부 | 내용 |
|------|----------|------|
| `companies/{TICKER}/moat.md` | **필수** | 버핏식 4축 thesis + Castle/ROIC/10년 테스트. daily 분석의 입력. |
| `companies/{TICKER}/profile.yaml` | **필수** | 종목 메타 (이름, 섹터, 시총, 핵심 지표, 트래킹 시작일 등) |
| `companies/{TICKER}/dividend.md` | 배당주만 | OXY, QCOM, NXPI, TXN, AVGO (compounder dividend 후보) |
| `companies/{TICKER}/pre-2025.md` | 필요 시 | 2025 이전 누적 컨텍스트가 있는 경우만 (OXY 등) |
| `companies/{TICKER}/moat-changelog.md` | 선택 | 최초 thesis 작성일 1줄 |

**작성 방식**: 계획 세션에서 종목 1개씩 WebSearch 기반으로 moat 4축 분석 → moat.md 초안 작성. 8개 모두 처리. 순서는 무관.
**AMBQ 주의**: 2025 IPO로 상장 이력 짧음 → moat thesis는 잠정(thesis tentative) 표기, pre-2025.md 생략 가능.

### B.2 `automation/config.yaml` tickers 갱신

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

### B.3 LaunchAgent / cron 변경 불필요

LaunchAgent wrapper는 config.yaml의 tickers를 읽으므로 추가 작업 없음. 단 12종목 × claude --print(평균 30~60s) ≈ 6~12분 → 기존 timeout=300s/종목은 문제 없음.
