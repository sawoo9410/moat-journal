# Backlog — Cross-company + Meta + Watchlist

> 사용자 단일 원천. Planner 세션이 우선순위 정렬 spec 작성, Reviewer/Editor 세션은 *읽기*.
> 우선순위: **P0** 이번 사이클 / **P1** 다음 사이클 / **P2** 후속.

_Last updated: 2026-04-26 (Spec B 최초 적용)_

---

## A. Company backlog

### GOOGL (lane: compounder)

source: `companies/GOOGL/reviews/2026-04-26-v4.md` §5

| P | 항목 | 출처/근거 |
|---|------|----------|
| **P1** | `## Capital Allocation` 섹션 신설 (capex / buyback / 배당 / M&A 비중·의도) | compounder lane 핵심 축 누락 |
| **P1** | `## Reinvestment Runway` 섹션 신설 (AI capex → 매출 전환 *속도*) | compounder lane 핵심 축 누락 |
| **P2** | Pre-2021 ROIC (2015~2020) — 10-K 직접 또는 무료 소스 발굴 | stockanalysis 5년 한계 |
| **P2** | `## Unknown Backlog` consolidated 리스트 — `_[unknown]_` 박스 통합·우선순위화 | 정리 작업 |
| **P2** | Worst case 확률 자가평가 — 멘토 워크드 추정치 + reasoning + "검증 필요" 라벨 | downside 정량화 |

### MCD (lane: moat + dividend)

| P | 항목 | 출처/근거 |
|---|------|----------|
| **P0** | 1차 moat·dividend thesis 진단 (Reviewer 사이클) | thesis 자체 미수행. 디렉토리 스캐폴드만 존재, 평가 세션 검수 0회 |

### KO (lane: moat + dividend)

| P | 항목 | 출처/근거 |
|---|------|----------|
| **P0** | 1차 moat·dividend thesis 진단 (Reviewer 사이클) | thesis 자체 미수행. 디렉토리 스캐폴드만 존재 |

### OXY / QCOM / SOUN / NVDA

| P | 항목 | 출처/근거 |
|---|------|----------|
| **P2** | 회사 디렉토리 스캐폴드 (profile.yaml + pre-2025.md) | `plan.md` §8.3 추적 7개 중 4개 미스캐폴드 |

---

## B. Meta backlog

| P | 항목 | 출처/근거 |
|---|------|----------|
| **P1** | Planner 모드 (Learn/Draft/Stress-test 별도?) 1~2 사이클 후 결정 | Spec A §5 |
| **P1** | 세션 모드 self-detection 룰 검토 (메타 질문 피로 vs 룰 위반 방지) | Spec A §5 |
| **P2** | `topics/` 공통 서사 디렉토리 도입 검토 | `plan.md` §8.5 — 6개월 운영 후 |

---

## C. Automation backlog (Phase별)

### Phase 0 (수동 prototype) — *지금*
- [x] `automation/prompts/weekly-googl-backlog-push.md` 신설 (본 spec)
- [ ] **사용자 task**: 매주 월요일 위 프롬프트 1회 수동 실행 → 결과 평가 → 패턴 안정화 확인
- [ ] 안정화 판정 기준: 3회 연속 *유용한* 답 (사용자 판단)

### Phase 1 (cron + bot) — Phase 0 통과 후

| P | 항목 | 비고 |
|---|------|------|
| **P1** | Telegram bot 신설 (예: `@moat_journal_bot`) | 사용자 작업 |
| **P1** | `automation/src/notifier.py` — `~/investment-strategy` `TelegramNotifier` 패턴 차용 | Editor |
| **P1** | `automation/src/run.py` — `claude --print < prompts/{topic}.md` 호출 → 출력 → notifier | Editor |
| **P1** | macOS launchd 또는 cron entry — 매주 월 09:00 KST | 사용자 작업 |
| **P2** | `claude --print` headless 모드 검증 (권한 모드, MCP 설정, 토큰 비용, 답 일관성) | Phase 1 진입 전 |
| **P2** | (a) IR D-3 reminder 추가 (분기 1회 / 회사) | 두 번째 자동화 |
| **P3** | Airflow DAG 이전 검토 | 봇 5개+ 시점 |

---

## D. Watchlist (새 회사 후보)

_(현재 비어 있음. 새 회사 신호 들어오면 P 등급 + 근거와 함께 추가.)_
