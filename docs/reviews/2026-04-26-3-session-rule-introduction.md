# 3-Session Rule Introduction (Planner / Reviewer / Editor) — Spec

**Date**: 2026-04-26
**Reviewer**: Claude (평가 세션)
**Target file(s)**:
- `docs/plan.md` (§0.5, §0.7 갱신)
- `CLAUDE.md` (두 세션 표 → 세 세션 표)
- `docs/operations.md` (§0 다이어그램 확장 + §1.5 계획 세션 신설 + §2 수정 세션 미세 갱신)
- `~/.claude/projects/-Users-seosang-u-moat-journal/memory/feedback_two_session_pattern.md` (삭제)
- `~/.claude/projects/-Users-seosang-u-moat-journal/memory/feedback_three_session_pattern.md` (신설)
- `~/.claude/projects/-Users-seosang-u-moat-journal/memory/MEMORY.md` (index 갱신)

**Status**: `applied`
**Order**: Spec A. Spec B (`2026-04-26-automation-skeleton-phase0.md`) 먼저 적용 금지.

---

## 1. 한 줄 변경 의도

기존 두 세션(Reviewer/Editor)에 **Planner 세션을 추가**하여 backlog 관리·자동화 architecture spec을 분리. 자동화/코드 도메인이 평가 세션의 moat 멘토링 톤·컨텍스트와 충돌하지 않도록 차단.

## 2. 사전 조건 / 현재 상태

- `git status`: GOOGL moat.md/changelog.md = v4 (이미 적용 완료, 미커밋). 본 spec 변경과 무관하지만 같은 working tree.
- `docs/plan.md` §0.7 헤더 = "0.7 작업 분리 — Reviewer / Editor (가장 강한 룰)"
- `CLAUDE.md` 표 = 평가/수정 두 세션
- `docs/operations.md` 제목 = "Operations — 두 세션 분리 워크플로", §1 평가 / §2 수정 (§3~§10 그대로 유지)
- `memory/feedback_two_session_pattern.md` = 두 세션 룰 명시

## 3. 데이터 (출처 + 조회일)

본 spec은 **룰 변경**이라 외부 데이터 의존 없음. 변경의 *근거*는 본 세션 대화 (사용자 결정 2026-04-26):
- 계획 세션이 단순 backlog 기록이 아닌 **텔레그램 자동화 코드 설계**까지 책임지므로 평가 세션과 도메인 분리 필요.
- 사용자 흐름: "수동 몇 번 → 패턴 → 코드". Phase 0 (수동) / Phase 1 (코드) 분리는 Spec B에서 구현.

## 4. 적용할 변경

### Edit 1 — `docs/plan.md` §0.7 헤더·표 갱신

**파일**: `docs/plan.md`

**Old**:
````
### 0.7 작업 분리 — Reviewer / Editor (가장 강한 룰)

이 저장소의 모트 작업은 **두 세션으로 분리**. 한 세션이 양쪽 다 하지 않는다.

| 세션 | 역할 | 산출물 | 파일 편집 |
|------|------|-------|----------|
| **평가(Reviewer)** — 기본 | 모트 평가, 개선 spec 생성 | `companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic}.md` spec | moat 파일 **편집 금지** |
| **수정(Editor)** | spec 받아 실제 편집 | 변경된 moat 파일 | spec 명시 항목만 편집 |

**기본 = 평가 세션**. 사용자가 "수정 세션", "edit mode", "이 세션에서 직접 수정" 등으로 명시하지 않으면 평가 세션으로 간주.

**Why**: 평가자/실행자 분리 → (1) 비평자가 자기 변경을 정당화하는 편향 차단, (2) 사용자가 spec을 인터셉트해서 검토 가능, (3) 변경 audit trail.
````

**New**:
````
### 0.7 작업 분리 — Planner / Reviewer / Editor (가장 강한 룰)

이 저장소의 작업은 **세 세션으로 분리**. 한 세션이 둘 이상 하지 않는다.

| 세션 | 역할 | 산출물 | 파일 편집 |
|------|------|-------|----------|
| **평가(Reviewer)** — 기본 | 모트 평가, 개선 spec 생성 | `companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic}.md` spec | moat 파일 + automation 코드 **편집 금지** |
| **계획(Planner)** | backlog 우선순위, 자동화 architecture spec | `docs/backlog.md`, `docs/reviews/{YYYY-MM-DD}-{topic}.md`, `automation/prompts/*.md` | moat 파일 + automation 코드 **편집 금지** |
| **수정(Editor)** | spec 받아 실제 편집 — moat 파일 + automation 코드 | 변경된 moat 파일, 변경된 automation 코드 | spec 명시 항목만 편집 |

**기본 = 평가 세션**. 다른 세션은 사용자가 명시할 때만 발동:
- "**수정 세션이야**" / "**edit mode**" → Editor
- "**계획 세션이야**" / "**planner mode**" / "**backlog 정리해줘**" → Planner

**Why**: (1) 비평자가 자기 변경을 정당화하는 편향 차단, (2) 사용자가 spec을 인터셉트해서 검토 가능, (3) 변경 audit trail. **Planner 추가의 추가 이유**: 자동화/코드 도메인은 평가의 moat 멘토링 톤·컨텍스트와 다르므로 분리해야 평가 세션의 회의주의·자본보존 집중을 보호. Planner가 코드까지 직접 짜면 자기 spec 자기 정당화 → 두 세션 룰 정신 위반이므로 코드 작성은 Editor.
````

### Edit 2 — `docs/plan.md` §0.7 "moat 파일" 블록 → 편집 권한 매트릭스

**Old**:
````
**moat 파일** (평가 세션이 수정 금지):
- `companies/*/moat.md`, `dividend.md`, `moat-changelog.md`
- `companies/*/2026/*.md` (월별 entry — 증거 원본)
- `companies/*/profile.yaml`

**예외 — 평가 세션이 수정 가능** (moat thesis 아닌 운영 파일):
- `docs/plan.md`, `CLAUDE.md`, 메모리
- `companies/*/reviews/*` (spec 자체)
````

**New**:
````
**편집 권한 매트릭스**:

| 파일 종류 | Reviewer | Planner | Editor |
|---|---|---|---|
| moat 파일 (`companies/*/moat.md`·`dividend.md`·`moat-changelog.md`·`2026/*.md`·`profile.yaml`) | ✗ | ✗ | ✓ (Reviewer spec 기반) |
| automation 코드 (`automation/src/*`) | ✗ | ✗ | ✓ (Planner spec 기반) |
| automation 데이터 (`automation/data/*`) | ✗ | ✗ | ✗ (cron / 사용자만) |
| Reviewer spec (`companies/*/reviews/*`) | ✓ Write | ✗ | status 필드만 |
| Planner spec (`docs/reviews/*`, `automation/prompts/*`) | ✗ | ✓ Write | status 필드만 |
| 운영 파일 (`docs/plan.md`·`CLAUDE.md`·`docs/operations.md`·`docs/backlog.md`·메모리) | ✓ | ✓ | ✓ (spec 기반) |

> 어느 세션이든 *자기 spec*은 작성 가능, *남의 spec*은 status 필드만 변경.
> Reviewer 가 *메타* spec(룰 변경 등)을 작성할 때는 `docs/reviews/` 위치 사용 (본 spec 자체가 그 예).
````

### Edit 3 — `docs/plan.md` §0.7 Spec 위치 컨벤션 확장

**Old**:
````
**Spec 위치 컨벤션**:
- `companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic-or-version}.md`
- 예: `companies/GOOGL/reviews/2026-04-26-v4.md`
- spec status: `pending` → 수정 세션이 적용 후 `applied` 로 변경.
````

**New**:
````
**Spec 위치 컨벤션**:

| Spec 종류 | 위치 | 예 |
|---|---|---|
| moat review (Reviewer) | `companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic-or-version}.md` | `companies/GOOGL/reviews/2026-04-26-v4.md` |
| 메타/룰 변경 (Reviewer 또는 Planner) | `docs/reviews/{YYYY-MM-DD}-{topic}.md` | `docs/reviews/2026-04-26-3-session-rule-introduction.md` |
| 자동화 프롬프트 (Planner) | `automation/prompts/{topic}.md` | `automation/prompts/weekly-googl-backlog-push.md` |

spec status: `pending` → 적용 세션이 `applied` 로 변경. 폐기되면 `superseded`.
````

### Edit 4 — `docs/plan.md` §0.5 모드 표 주석 추가

**Old**:
````
기본은 **Learn 모드** — 트리거 없으면 가르침·맥락 우선, 결론은 마지막. Draft 결과물도 다음 단계가 매수 결정이면 사용자가 Stress-test 트리거를 안 줘도 5 gates를 자발적으로 돌릴 것.
````

**New**:
````
기본은 **Learn 모드** — 트리거 없으면 가르침·맥락 우선, 결론은 마지막. Draft 결과물도 다음 단계가 매수 결정이면 사용자가 Stress-test 트리거를 안 줘도 5 gates를 자발적으로 돌릴 것.

> 위 세 모드는 **Reviewer 세션 내부 모드**. Planner / Editor 세션은 별도 (§0.7 참조).
````

### Edit 5 — `CLAUDE.md` 두 세션 표 → 3-세션 표

**Old**:
````
## 두 세션 분리 (가장 중요한 룰)

모트 작업은 **항상 두 세션으로 분리**:

| 세션 | 역할 | 파일 편집 |
|------|------|----------|
| **평가(Reviewer)** — *기본* | 모트 평가, 개선 spec 생성 | moat 파일 **직접 편집 금지** |
| **수정(Editor)** | 평가 세션의 spec 받아 적용 | spec 명시 항목만 편집 |

**기본 모드 = 평가 세션**. 사용자가 "수정 세션", "edit mode" 등으로 **명시하지 않으면** moat 파일 직접 편집 X. spec 형태로만 산출.

- **moat 파일** (평가 세션이 편집 금지) = `companies/*/moat.md` · `dividend.md` · `moat-changelog.md` · `2026/*.md` 월별 entry · `profile.yaml`
- **편집 가능** (moat thesis 아닌 운영 파일) = `docs/plan.md` · `CLAUDE.md` · 메모리 · `companies/*/reviews/*`(spec 자체)
- **평가 세션 산출물** = `companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic}.md` spec 파일

상세는 `docs/plan.md` §0.7 (룰·형식). 일상 운영 절차는 `docs/operations.md` (한 사이클 흐름·트러블슈팅·체크리스트).
````

**New**:
````
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
````

### Edit 6 — `CLAUDE.md` "단일 원천" 표 갱신

**Old**:
````
| 두 세션 분리 룰 | `docs/plan.md` §0.7 + 메모리 `feedback_two_session_pattern.md` |
````

**New**:
````
| 세 세션 분리 룰 | `docs/plan.md` §0.7 + 메모리 `feedback_three_session_pattern.md` |
| Backlog (cross-company + meta + automation) | `docs/backlog.md` (Spec B 적용 후) |
| 자동화 (Phase 0 수동 / Phase 1 코드) | `automation/README.md` (Spec B 적용 후) |
````

### Edit 7 — `docs/operations.md` 제목·도입 갱신

**Old**:
````
# Operations — 두 세션 분리 워크플로

> 이 저장소를 *매일* 어떻게 굴리나.
> 룰의 **이유**는 `plan.md` §0.7, **행동**은 여기.
````

**New**:
````
# Operations — 세 세션 분리 워크플로

> 이 저장소를 *매일* 어떻게 굴리나.
> 룰의 **이유**는 `plan.md` §0.7, **행동**은 여기.
> 세 세션 = Reviewer (기본) / Planner (명시) / Editor (명시).
````

### Edit 8 — `docs/operations.md` §0 한 사이클 다이어그램 확장

**Old**:
````
## 0. 한 사이클 (평가 → 적용 → 검증)

```
[1] 사용자: 평가 세션에 "TICKER moat 어때?" 발화
       │
[2] 평가 세션: 모트 read → spec 작성
       │   산출물: companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic}.md
       │
[3] 사용자: spec 인터셉트·검토 (마음에 안 들면 평가 세션에 수정 요청)
       │
[4] 사용자: 새 Claude Code 세션 열기 → "수정 세션이야. {spec 경로} 적용해줘"
       │
[5] 수정 세션: 사전 조건 확인 → Edit 1,2,... 적용 → spec status=applied
       │
[6] 사용자: git diff 로 검증
       │
[7] 사용자: git commit (수동)
```

핵심: **평가와 수정은 다른 세션에서**. 같은 세션에서 평가 후 바로 수정 X.
````

**New**:
````
## 0. 한 사이클

세 가지 사이클이 있음.

### 0.A moat 사이클 (평가 → 적용)
```
[1] 사용자: 평가 세션에 "TICKER moat 어때?" 발화
[2] 평가 세션: moat read → spec 작성 (companies/{TICKER}/reviews/...)
[3] 사용자: spec 인터셉트·검토
[4] 사용자: 새 세션 → "수정 세션이야. {spec 경로} 적용해줘"
[5] 수정 세션: 사전 조건 확인 → Edit 적용 → status=applied
[6] git diff → commit
```

### 0.B 계획 사이클 (계획 → 적용)
```
[1] 사용자: 계획 세션에 "이번 분기 backlog 정리" 또는 "텔레그램 알림 spec 짜줘" 발화
[2] 계획 세션: backlog.md 읽기 + spec 작성 (docs/reviews/... 또는 automation/prompts/...)
[3] 사용자: spec 인터셉트·검토
[4] 사용자: 새 세션 → "수정 세션이야. {spec 경로} 적용해줘"
[5] 수정 세션: Edit 적용 → status=applied
[6] git diff → commit
```

### 0.C 자동화 실행 사이클 (Phase 0 수동 / Phase 1 cron)
```
[Phase 0] 사용자: 일반 Claude 세션에 automation/prompts/{topic}.md 내용 → 결과 받기 → 사람이 텔레그램 직접 발송
[Phase 1] cron → claude --print → WebSearch → 요약 → Telegram Bot API → 발송
```

핵심: **각 세션은 다른 세션에서**. 같은 세션에서 평가/계획 후 바로 수정 X.
````

### Edit 9 — `docs/operations.md` §1과 §2 사이에 §1.5 신설

**위치**: §1 (평가 세션 시작) 종료 직후, §2 (수정 세션 시작) 직전.

**Old (§1 종료 ~ §2 시작 경계)**:
````
- 사용자 명시 없이 수정 세션 모드로 자가 전환

---

## 2. 수정 세션 시작 (명시 트리거 필요)
````

**New**:
````
- 사용자 명시 없이 수정 세션 모드로 자가 전환

---

## 1.5 계획 세션 시작 (명시 트리거 필요)

**발화 예시**:
- "**계획 세션이야**. 이번 분기 backlog 정리해줘"
- "**planner mode** — 텔레그램 (a) IR D-3 reminder spec 짜줘"
- "GOOGL backlog 우선순위 다시 정해줘"

**계획 세션이 *하는* 것**:
- `docs/backlog.md` 를 *읽고* 우선순위 재정렬 spec 작성
- 자동화 architecture spec 작성 (`automation/prompts/{topic}.md` 또는 `docs/reviews/{date}-automation-{topic}.md`)
- watchlist 항목 추가 spec (새 회사 후보)
- meta 변경 (plan.md / CLAUDE.md / 메모리 / 자동화 룰) spec 작성

**계획 세션이 *하지 않는* 것**:
- moat thesis 평가 (Reviewer 영역)
- moat 파일 편집 (Editor 영역)
- automation 코드 작성 (Editor 영역)

**산출물**:
- `docs/backlog.md` 갱신 spec (직접 편집 OK — backlog.md는 운영 파일)
- `docs/reviews/{YYYY-MM-DD}-{topic}.md` (메타·룰 변경)
- `automation/prompts/{topic}.md` (Phase 0 자산은 Planner 가 직접 Write — spec 자체이자 산출물)

---

## 2. 수정 세션 시작 (명시 트리거 필요)
````

### Edit 10 — `docs/operations.md` §2 수정 세션 *하는* 것 미세 갱신

**Old**:
````
**수정 세션이 *하는* 것**:
1. spec 파일을 Read
2. **사전 조건 확인** (예: 헤더 Version 매칭). 실패 시 **HALT** → 사용자에게 보고
3. Edit 1, 2, ... 순서대로 *정확히* 적용
4. spec 의 Status 를 `pending` → `applied` 로 변경 (spec 파일 자체는 평가/수정 모두 편집 가능)
5. (선택) 결과 요약 — "Edit 1~7 적용, 헤더 v4 검증 완료"
````

**New**:
````
**수정 세션이 *하는* 것**:
1. spec 파일을 Read (Reviewer spec / Planner spec 모두 가능)
2. **사전 조건 확인** (예: 헤더 Version 매칭, 의존 spec applied 여부). 실패 시 **HALT** → 사용자에게 보고
3. Edit 1, 2, ... 순서대로 *정확히* 적용
4. spec 의 Status 를 `pending` → `applied` 로 변경 (status 필드는 모든 세션이 변경 가능)
5. (선택) 결과 요약
````

### Edit 11 — 메모리 `feedback_two_session_pattern.md` 삭제

**파일**: `~/.claude/projects/-Users-seosang-u-moat-journal/memory/feedback_two_session_pattern.md`
**작업**: 파일 삭제 (`rm`).

### Edit 12 — 메모리 `feedback_three_session_pattern.md` 신설

**파일**: `~/.claude/projects/-Users-seosang-u-moat-journal/memory/feedback_three_session_pattern.md`
**작업**: 새 파일 Write.

**내용**:
```markdown
---
name: 세 세션 분리 패턴 — Planner / Reviewer / Editor
description: 모트·계획·자동화 작업은 세 세션으로 분리. Reviewer는 moat·automation 편집 금지, Planner는 backlog/automation spec 생성, Editor는 spec 적용.
type: feedback
---
**룰**: 이 저장소 작업은 항상 세 세션으로 분리.
- **평가(Reviewer) 세션** — *기본*. 모트 read·평가, 개선 spec 생성. moat·automation 파일 편집 금지.
- **계획(Planner) 세션** — 명시 트리거 ("계획 세션이야" / "planner mode"). backlog 우선순위, 자동화 architecture spec 생성. moat·automation 코드 편집 금지.
- **수정(Editor) 세션** — 명시 트리거 ("수정 세션이야" / "edit mode"). Reviewer/Planner spec 받아 실제 파일 편집.

**Why**: 사용자 명시 (2026-04-26) — 두 세션(Reviewer/Editor)으로는 *자동화/코드 설계*가 평가 세션의 moat 멘토링 톤·컨텍스트와 충돌. Planner를 분리해 평가의 회의주의·자본보존 집중을 보호. Planner 가 코드까지 직접 짜면 자기 spec 자기 정당화 → 두 세션 룰 정신 위반이므로 코드 작성은 Editor.

**How to apply**:
- 편집 권한 매트릭스: `docs/plan.md` §0.7 표 참조.
- 산출물 위치:
  - Reviewer → `companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic}.md`
  - Planner → `docs/backlog.md`, `docs/reviews/{YYYY-MM-DD}-{topic}.md`, `automation/prompts/*.md`
  - Editor → 변경된 moat 파일, 변경된 automation 코드
- spec 필수 섹션 (모든 세션 공통): `docs/plan.md` §0.7.
- 사용자가 명시 트리거 없이 발화하면 = Reviewer (기본).
```

### Edit 13 — 메모리 `MEMORY.md` index 갱신

**파일**: `~/.claude/projects/-Users-seosang-u-moat-journal/memory/MEMORY.md`

**Old**:
````
- [두 세션 분리 패턴 (Reviewer/Editor)](feedback_two_session_pattern.md) — 평가 세션은 모트 파일 직접 편집 금지, spec만 생성하여 수정 세션에 전달
````

**New**:
````
- [세 세션 분리 패턴 (Planner/Reviewer/Editor)](feedback_three_session_pattern.md) — 평가는 moat·automation 편집 금지, 계획은 backlog/automation spec 생성, 수정은 spec 적용
````

## 5. 미해결 backlog (다음 review에서 다룰 항목)

- **Planner 모드 가이드**: Planner 세션 안에서 `Learn / Draft / Stress-test` 같은 모드를 둬야 할지. 1~2 사이클 돌려보고 결정.
- **세션 모드 self-detection**: 사용자 발화에 트리거 없을 때 Claude가 "이거 계획 모드 같은데 명시할래?" 묻는 룰을 도입할지. 메타 질문 피로 vs 룰 위반 방지 트레이드오프.
- 위 두 항목은 Spec B의 `docs/backlog.md` §B 에 등록됨.

## 6. 수정 세션 핸드오프 체크리스트

- [ ] Edit 1~4: `docs/plan.md` §0.5 / §0.7 갱신 (헤더, 표 두 개, 위치 컨벤션, 모드 주석)
- [ ] Edit 5~6: `CLAUDE.md` 갱신 (세션 표, 단일 원천 표)
- [ ] Edit 7~10: `docs/operations.md` 갱신 (제목, §0 다이어그램, §1.5 신설, §2 미세 갱신)
- [ ] Edit 11: 메모리 `feedback_two_session_pattern.md` 삭제 (`rm`)
- [ ] Edit 12: 메모리 `feedback_three_session_pattern.md` 신설 (Write)
- [ ] Edit 13: 메모리 `MEMORY.md` 갱신
- [ ] 일관성 검증:
  - `grep -rn "두 세션" docs/ CLAUDE.md` → 결과 없거나 *역사 인용*만 (예: 메모리 갱신 사례)
  - `grep -rn "Reviewer / Editor" docs/ CLAUDE.md` → 결과 없거나 "Planner / Reviewer / Editor"
  - `grep -rn "feedback_two_session_pattern" .` → 결과 없음
- [ ] 본 spec status: `pending` → `applied`
- [ ] 사용자에게 보고: 변경 파일 리스트 + `git diff --stat` + 메모리 변경
- [ ] git commit 은 사용자가 직접 — 본 세션은 add/commit 금지
