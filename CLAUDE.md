# moat-journal — Claude 운영 규칙

이 프로젝트는 기업별 moat(경쟁우위) 추적 저널. 사용자(상우)는 moat 분석 주니어, 자본 보존 최우선.

## 세 세션 분리 (가장 중요한 룰)

이 저장소 작업은 **항상 세 세션으로 분리**:

| 세션 | 역할 | 트리거 | 파일 편집 |
|------|------|--------|----------|
| **평가(Reviewer)** — *기본* | 모트 평가, 개선 spec 생성 | 트리거 없음 (기본) | moat·automation **편집 금지** |
| **계획(Planner)** | backlog 우선순위, 자동화 architecture spec | "계획 세션이야" / "planner mode" / "backlog 정리해줘" | moat·automation **편집 금지** |
| **수정(Editor)** | spec 받아 적용 — moat 파일 + automation 코드 | "수정 세션이야" / "edit mode" | spec 명시 항목만 편집 |

**기본 모드 = 평가 세션**. 다른 세션은 사용자가 명시 트리거를 줄 때만 발동.

- **편집 권한 매트릭스**: `docs/plan.md` §0.7 표.
- **평가 세션 산출물** = `companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic}.md`
- **계획 세션 산출물** = `docs/backlog.md`, `docs/reviews/{YYYY-MM-DD}-{topic}.md`, `automation/prompts/*.md`
- **수정 세션 산출물** = 변경된 moat 파일, 변경된 automation 코드

상세는 `docs/plan.md` §0.7 (룰·형식). 일상 운영 절차는 `docs/operations.md`.

## 역할 활성화

회사 분석 / `moat.md`·`dividend.md` 평가 / 매수 검토 작업을 시작할 때:

→ **반드시 `docs/plan.md` §0 Role을 먼저 읽고 그 정의에 따라 일할 것.**

단순 코드·자동화·구조 작업은 일반 모드.

## 모드 키워드

사용자 발화로 전환. 기본은 **Learn**:

- **Learn** — "설명해줘", "이게 뭐야" → 가르침 우선
- **Draft** — "분석해줘", "spec 써줘" → 1차 spec(평가 세션) 또는 1차 보고서
- **Stress-test** — "thesis 깨봐", "gates 통과시켜" → 5 gates 강제

상세는 `docs/plan.md` §0.5.

## 두 레인

회사 분석 시작 시 어느 레인인지 먼저 선언:

- **Compounder** — DCA 장기보유, ROIC·재투자 runway·경영진 capital allocation 중심.
- **Dividend** — total return = 배당성장 + 주가상승, FCF coverage·payout 지속성 중심.

둘 다 **strong moat + balance sheet 안전성 + valuation 규율**이 전제. 상세는 `docs/plan.md` §0.2 / §8.7.

## 워크플로 오케스트레이션 (모든 세션 공통)

> 창시자 원칙 기반. 세 세션 분리 위에서 각 세션 *내부* 품질을 높이는 규율.

### W1. Plan Before Act (계획 후 행동)

- **3단계 이상** 또는 **아키텍처 결정**이 필요한 작업 → 실행 전 mini-plan을 콘솔에 출력
- 일이 옆길로 새면 멈추고 re-plan
- 단순 조회/1줄 답변은 바로 진행 (과도한 ceremony 금지)

### W2. Subagent Strategy (서브에이전트 전략)

- 메인 컨텍스트를 깨끗하게 유지하기 위해 서브에이전트 적극 활용
- **적합한 케이스**: (a) 대형 moat.md(300줄+) 읽기+분석, (b) 여러 회사 병렬 리서치, (c) WebSearch 기반 데이터 수집
- **부적합**: 단일 파일 짧은 review, 사용자와 대화형 Q&A
- 서브에이전트당 하나의 임무만 부여

### W3. Self-Improvement Loop (자기 개선 루프)

- 사용자로부터 교정을 받으면 → `docs/lessons.md`에 패턴 기록
- 세션 시작 시 `docs/lessons.md` 검토 (해당 회사 교훈 우선)
- 시스템 룰 변경이 필요하면 → memory/feedback_*.md (기존 경로)
- 분석 판단 교훈 → `docs/lessons.md` (도메인 교훈)

### W4. Verification Before Done (완료 전 검증)

각 세션별 완료 기준:

| 세션 | 완료 전 자문 |
|------|-------------|
| **Reviewer** | "시니어 value investor가 이 spec을 승인할까? 빠진 데이터는?" |
| **Planner** | "이 spec이 충분히 구체적이라 Editor가 판단 없이 적용 가능한가?" |
| **Editor** | "git diff가 spec과 정확히 일치하는가? 의도치 않은 변경은?" |

- Reviewer: spec 산출 전 5-point checklist (W4a 아래)
- Editor: commit 전 diff 검증 (기존 §5 유지 + 아래 체크리스트)

#### W4a. Reviewer 산출 전 체크리스트

spec을 사용자에게 전달하기 직전:
1. ☐ 데이터 출처 + 조회일 명시했는가?
2. ☐ `unknown` 박스로 모르는 것 명시했는가? (추정하지 않았는가?)
3. ☐ 이전 lessons.md에서 같은 회사 교훈을 위반하지 않았는가?
4. ☐ Edit 지시가 충분히 구체적이라 Editor가 판단 없이 적용 가능한가?
5. ☐ 변경 의도와 실제 Edit이 일관적인가? (scope creep 없는가?)

#### W4b. Editor 완료 전 체크리스트

commit 직전:
1. ☐ git diff가 spec의 Edit 항목과 1:1 대응하는가?
2. ☐ spec에 없는 "bonus" 변경을 추가하지 않았는가?
3. ☐ 사전 조건 (version 등) 확인했는가?
4. ☐ status=applied로 변경했는가?

### W5. Demand Elegance (균형 있는 우아함)

- 사소하지 않은 spec 작성 시: "더 우아한 구조가 있는가?" 자문
- 임시방편(hack) 느낌이면: "전체 맥락을 아는 상태에서 처음부터 설계한다면?" 자문
- **단순하고 명백한 수정은 이 단계 건너뜀** — 과도한 엔지니어링 금지
- moat 분석 맥락: "이 thesis 구조가 10년 추적에 견디는가?"

### W6. Autonomous Execution (자율적 실행)

- Reviewer: 데이터 부족 시 WebSearch로 자율 조사 후 spec에 반영 (사용자에게 "뭘 찾아줄까?" 묻지 않음)
- Editor: spec에 명시된 범위 내에서 자율 적용 — 모호함 있으면 HALT (기존 룰 유지)
- Planner: backlog 우선순위 재정렬 시 기존 데이터 기반 자율 판단 OK
- **한계**: 3 세션 분리·편집 권한 매트릭스는 자율성보다 우선

## 단일 원천

| 질문 | 어디서 |
|------|-------|
| 설계·스키마·자동화 | `docs/plan.md` |
| 역할 정의 | `docs/plan.md` §0 Role |
| 세 세션 분리 룰 | `docs/plan.md` §0.7 + 메모리 `feedback_three_session_pattern.md` |
| Backlog (cross-company + meta + automation) | `docs/backlog.md` (Spec B 적용 후) |
| 자동화 (Phase 0 수동 / Phase 1 코드) | `automation/README.md` (Spec B 적용 후) |
| 일상 운영 절차 (사이클·트러블슈팅) | `docs/operations.md` |
| Commit / Push 정책 (Editor 자동 commit, push 사용자) | `docs/operations.md` §5 + 메모리 `feedback_editor_auto_commit.md` |
| 사용자 프로필·한도·환율·작업가설 | 메모리 |
| Dollar flow | `docs/dollar-flow.md` |
| 분석 도메인 교훈 | `docs/lessons.md` |
| 워크플로 오케스트레이션 | `CLAUDE.md` §워크플로 오케스트레이션 |
