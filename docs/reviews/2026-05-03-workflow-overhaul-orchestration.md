# Spec: 워크플로 오버홀 — 창시자 오케스트레이션 원칙 적용

> status: `applied`
> 작성 세션: Planner (2026-05-03)
> 적용 대상: `CLAUDE.md`, `docs/operations.md`, `docs/lessons.md` (신설), `docs/plan.md` §0.7

---

## 한 줄 변경 의도

Claude Code 창시자의 6대 워크플로 원칙(Plan Default, Subagent Strategy, Self-Improvement Loop, Verification Before Done, Demand Elegance, Autonomous Execution)을 moat-journal 세 세션 구조에 통합하여 Claude의 자율 품질을 높인다.

---

## 사전 조건

- `CLAUDE.md` — 현재 세 세션 분리 룰 존재 (변경 전 베이스)
- `docs/operations.md` — 현재 §0~§10 존재
- `docs/lessons.md` — **존재하지 않음** (이 spec에서 신설)
- `docs/plan.md` §0.7 — 편집 권한 매트릭스 존재

---

## 설계 결정 (Why)

### 현재 갭 분석

| 창시자 원칙 | 현재 커버리지 | 갭 |
|---|---|---|
| Plan Node Default | Planner 세션이 커버 — 하지만 Reviewer 세션 내부에서 3단계 이상 평가를 바로 쏟아내는 경우 있음 | Reviewer가 복잡한 평가 시 mini-plan 없이 진행 |
| Subagent Strategy | 활용 없음 | 대형 평가(GOOGL moat.md 500줄+) 시 컨텍스트 낭비 |
| Self-Improvement Loop | memory/feedback_*.md — 시스템 룰 수정용 | moat 분석 도메인 교훈 저장소 없음 |
| Verification Before Done | Editor가 `git diff` 확인 | 체크리스트 부재, "시니어 investor가 승인할까" 관점 없음 |
| Demand Elegance | 없음 | spec이 임시방편인지 검증하는 단계 없음 |
| Autonomous Execution | Editor는 spec 그대로만 적용 | Reviewer가 data fetch 가능하지만 자율 조사 룰 없음 |

### 적용 철학

1. **세 세션 분리는 유지** — 이건 moat-journal의 핵심 가치 (편향 차단). 창시자 원칙은 각 세션 *내부*의 품질을 높이는 데 쓴다.
2. **과도한 의식(ceremony) 금지** — 단순 질문이나 1줄 수정에까지 plan mode 강제하지 않는다.
3. **lessons.md는 도메인 교훈** — 시스템 룰(memory/feedback_*.md)과 분리. "KO 분석할 때 FCF→배당 커버리지를 먼저 봐야 했다" 같은 것.

---

## 적용할 변경

### Edit 1 — `docs/lessons.md` 신설

**파일**: `docs/lessons.md` (새 파일)

```markdown
# Lessons — moat 분석 도메인 교훈

> Claude가 분석 과정에서 배운 교훈을 누적. 세션 시작 시 검토하여 같은 실수 반복 방지.
> 시스템 룰 변경은 memory/feedback_*.md, 여기는 **분석 판단** 교훈만.

_Last updated: 2026-05-03 (초기화)_

---

## 형식

```
### {YYYY-MM-DD} — {한 줄 교훈}
- **상황**: 무엇을 하고 있었나
- **실수/발견**: 무엇이 잘못되었거나 발견되었나
- **규칙**: 앞으로 어떻게 할 것인가
- **관련 회사**: {TICKER} (해당 시)
```

---

## 교훈 목록

_(아직 없음 — 첫 교훈이 추가되면 위 형식으로 기록)_
```

---

### Edit 2 — `CLAUDE.md` 워크플로 오케스트레이션 섹션 추가

**파일**: `CLAUDE.md`
**위치**: 기존 `## 단일 원천` 섹션 **앞**에 삽입

**New** (삽입할 내용):

```markdown
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
```

---

### Edit 3 — `CLAUDE.md` 단일 원천 테이블 항목 추가

**파일**: `CLAUDE.md`
**위치**: `## 단일 원천` 테이블 마지막 행 뒤에 추가

**Old**:
```
| Dollar flow | `docs/dollar-flow.md` |
```

**New**:
```
| Dollar flow | `docs/dollar-flow.md` |
| 분석 도메인 교훈 | `docs/lessons.md` |
| 워크플로 오케스트레이션 | `CLAUDE.md` §워크플로 오케스트레이션 |
```

---

### Edit 4 — `docs/operations.md` 세션 시작 공통 프리앰블 추가

**파일**: `docs/operations.md`
**위치**: `## 1. 평가 세션 시작` **바로 앞**에 새 섹션 삽입

**New** (삽입할 내용):

```markdown
## 0.5 세션 시작 공통 루틴 (모든 세션)

모든 세션은 시작 시 다음을 수행:

1. **lessons.md 스캔** — `docs/lessons.md`에서 해당 회사 또는 해당 작업 유형의 교훈 확인
2. **mini-plan 출력** (3단계 이상 작업 시) — 무엇을 어떤 순서로 할지 콘솔에 1~5줄 plan
3. **세션 선언** — 현재 세션 유형 + 수행할 작업 1줄 명시

> 단순 Q&A (1~2턴)에는 이 루틴 생략 가능.

---
```

---

### Edit 5 — `docs/operations.md` Editor 세션 완료 체크리스트 추가

**파일**: `docs/operations.md`
**위치**: `## 2. 수정 세션 시작` 의 `**수정 세션이 *하지 않는* 것**:` 블록 **뒤**에 추가

**New** (삽입할 내용):

```markdown

**수정 세션 완료 전 체크리스트** (commit 직전):
1. ☐ `git diff` 가 spec Edit 항목과 1:1 대응
2. ☐ spec 에 없는 "bonus" 변경 없음
3. ☐ 사전 조건 (version, 의존 spec) 확인 완료
4. ☐ spec status=`applied` 로 변경 완료
5. ☐ commit message 형식 준수 (`{영역}: {요지} (per {spec 경로})`)
```

---

### Edit 6 — `docs/plan.md` §0.7 운영 파일 목록에 lessons.md 추가

**파일**: `docs/plan.md`
**위치**: §0.7 하단의 `**일상 운영 절차**` 줄 뒤에 추가

**Old**:
```
**일상 운영 절차** (한 사이클 흐름 / 트러블슈팅 / 빠른 시작 체크리스트): `docs/operations.md`. 본 §0.7은 룰·형식 정의, `operations.md`는 행동 매뉴얼.
```

**New**:
```
**일상 운영 절차** (한 사이클 흐름 / 트러블슈팅 / 빠른 시작 체크리스트): `docs/operations.md`. 본 §0.7은 룰·형식 정의, `operations.md`는 행동 매뉴얼.

**분석 도메인 교훈**: `docs/lessons.md`. 사용자 교정 시 업데이트. 세션 시작 시 검토. 시스템 룰(memory/feedback_*.md)과 분리 — 여기는 moat 분석 판단 교훈만.
```

---

## 변경하지 않는 것 (명시적 제외)

| 항목 | 이유 |
|---|---|
| 세 세션 분리 구조 자체 | 핵심 가치 유지 — 편향 차단 |
| 편집 권한 매트릭스 | 구조 변경 아님 — 각 세션 내부 품질 향상만 |
| Commit/Push 정책 (§5) | 이미 충분히 견고 |
| Reviewer 내부 모드 (Learn/Draft/Stress-test) | 그대로 유지 — W1~W6은 모드와 직교 |
| memory/feedback_*.md 체계 | 시스템 룰용으로 계속 사용 |

---

## 미해결 backlog (다음 사이클)

| P | 항목 | 비고 |
|---|------|------|
| P1 | lessons.md 첫 엔트리 — 다음 Reviewer 세션에서 자연스럽게 발생 시 기록 | 빈 파일 운영 확인 |
| P2 | 서브에이전트 활용 실전 검증 — GOOGL moat.md 대형 평가에서 시험 | W2 유효성 |
| P2 | W4a 체크리스트 마찰 측정 — 2~3 사이클 후 과도하면 축소 | ceremony vs 품질 균형 |

---

## 수정 세션 핸드오프 체크리스트

Editor에게 전달 시:
- [ ] Edit 1: `docs/lessons.md` 신설 (전체 Write)
- [ ] Edit 2: `CLAUDE.md`에 `## 워크플로 오케스트레이션` 섹션 삽입 (`## 단일 원천` 앞)
- [ ] Edit 3: `CLAUDE.md` 단일 원천 테이블 행 추가
- [ ] Edit 4: `docs/operations.md`에 `## 0.5 세션 시작 공통 루틴` 삽입 (`## 1.` 앞)
- [ ] Edit 5: `docs/operations.md` Editor 완료 체크리스트 추가
- [ ] Edit 6: `docs/plan.md` §0.7에 lessons.md 언급 추가
- [ ] 모든 Edit 적용 후 `git diff` 로 검증
- [ ] 이 spec status → `applied`
