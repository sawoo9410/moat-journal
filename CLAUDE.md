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
