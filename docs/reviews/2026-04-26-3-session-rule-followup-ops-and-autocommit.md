# 3-Session Rule Followup — Ops 일관성 + Editor 자동 commit — Spec

**Date**: 2026-04-26
**Reviewer**: Claude (평가 세션)
**Target file(s)**:
- `docs/operations.md` (§5 commit 정책 전면 갱신, §7 1줄, §10 제목 한정, §0.A/§0.B 다이어그램 [6][7])
- `docs/plan.md` (§0.7 Spec 위치 컨벤션 다음에 commit cross-ref 1줄)
- `CLAUDE.md` ("단일 원천" 표에 commit 정책 행 추가)
- `~/.claude/projects/-Users-seosang-u-moat-journal/memory/feedback_editor_auto_commit.md` (신설)
- `~/.claude/projects/-Users-seosang-u-moat-journal/memory/MEMORY.md` (index 추가)

**Status**: `applied`
**Order**: Spec C. **사전 조건**: Spec A·B 모두 status=applied.

---

## 1. 한 줄 변경 의도

(1) Spec A 적용 후 잔존 일관성 누락(§7 1줄, §10 제목 한정) 정리, (2) Editor 자동 commit 룰 도입 — 1 spec 적용 = 1 commit, push 는 사용자만, 가드레일 6개.

## 2. 사전 조건 / 현재 상태

- Spec A (`docs/reviews/2026-04-26-3-session-rule-introduction.md`) status = `applied`. pending 이면 HALT.
- Spec B (`docs/reviews/2026-04-26-automation-skeleton-phase0.md`) status = `applied`. pending 이면 HALT.
- `docs/operations.md` 현재:
  - §0 = 0.A / 0.B / 0.C 다이어그램 (Spec A 적용)
  - §1.5 계획 세션 시작 (Spec A 적용)
  - §5 = 기존 두 세션 시절 commit 정책 (사용자가 직접 commit 으로 명시)
  - §7 본문에 "두 세션 분리 룰" 1건 잔존 (Spec A 누락)
  - §10 제목 = "빠른 시작 체크리스트" (사이클 한정 표시 없음)
- `docs/plan.md` §0.7 = 3-세션 표 (Spec A 적용)
- `CLAUDE.md` = 3-세션 표 + 단일 원천 표 (Spec A 적용 후 사용자 직접 미세 갱신 포함)
- 메모리 = `feedback_three_session_pattern.md` (Spec A 적용)

## 3. 데이터 (출처 + 조회일)

본 spec 은 **룰 변경**이라 외부 데이터 의존 없음. 변경의 *근거*는 본 세션 대화 (사용자 결정 2026-04-26):
- 잔존 누락: 수정 세션이 §7 발견·보고 (spec 범위 밖이라 임의 수정 안 함). 평가 세션 추가 발견 = §10 제목 한정.
- Editor 자동 commit: 사용자 명시 — *"commit까진 알아서 했으면 좋겠는데, 나는 push만 하고 싶어서"*. push 외부 영향 분리는 그대로 사용자 책임.

## 4. 적용할 변경

### Edit 1 — `docs/operations.md` §7 본문 1줄

**파일**: `docs/operations.md`

**Old**:
````
사용자(상우)는 언제든 moat 파일을 직접 편집 가능. **두 세션 분리 룰은 Claude에게만 적용**.
````

**New**:
````
사용자(상우)는 언제든 moat 파일을 직접 편집 가능. **세 세션 분리 룰은 Claude에게만 적용**.
````

### Edit 2 — `docs/operations.md` §10 제목·도입 한정

**Old**:
````
## 10. 빠른 시작 체크리스트

처음 모트 review 사이클 돌릴 때:
````

**New**:
````
## 10. 빠른 시작 체크리스트 (moat 사이클)

처음 *모트 review* 사이클(0.A) 돌릴 때:

> 계획 사이클(0.B) / 자동화 Phase 0 사이클(0.C) 의 빠른 시작 체크리스트는 별도 사이클로 신설 예정 (`docs/backlog.md` §B).
````

### Edit 3 — `docs/operations.md` §5 Commit 정책 전면 갱신

**Old**:
````
## 5. Commit 정책

| 시점 | 무엇을 commit |
|------|--------------|
| spec 작성 직후 | spec 파일 (status=pending). 적용 전 인터셉트 검토용 audit trail. |
| spec 적용 직후 | moat 파일 변경 + spec status=applied 를 **한 commit**으로. 메시지 예: `GOOGL moat v4: unknown 채우기 + Gate 4 (per reviews/2026-04-26-v4.md)` |

### Uncommitted work 보호 (오늘 사례 교훈)

> 2026-04-26 GOOGL: 사용자 손작업 v3 + Claude v4 모두 uncommitted 였다가 `git checkout` 으로 함께 사라짐.

**룰**:
- `git checkout` / `git reset --hard` 같은 destructive 명령 *직전* 반드시 `git status`.
- uncommitted 손작업이 보이면 → `git stash` 또는 별도 branch 로 보존 후 destructive 명령.
- 평가 세션이 destructive 명령 제안 시 사용자에게 confirm 요청 (CLAUDE.md 룰).
````

**New**:
````
## 5. Commit / Push 정책

### 5.1 누가 무엇을

| 액션 | 누가 |
|------|------|
| spec 파일 작성 (status=pending) 만 먼저 commit | 평가/계획 세션 또는 사용자 (선택, audit trail 인터셉트용) |
| spec 적용 후 commit (1 spec = 1 commit) | **수정 세션 자동** |
| `git push` | **사용자만** (자동 X) |

### 5.2 수정 세션 자동 commit 룰

수정 세션은 1 spec 적용 후 1 commit 생성:

- **단위**: 1 spec = 1 commit. 같은 세션에서 여러 spec 연속 적용 시 spec 마다 별도 commit.
- **메시지 형식**: `{영역}: {요지} (per {spec 경로})`
  - 예: `GOOGL moat v4: unknown 채우기 + Gate 4 (per companies/GOOGL/reviews/2026-04-26-v4.md)`
  - 예: `3-session rule: Planner/Reviewer/Editor 분리 (per docs/reviews/2026-04-26-3-session-rule-introduction.md)`
- **Stage 범위**: spec 이 변경한 파일만 `git add <specific>`. spec status=applied 변경도 같은 commit 에 포함.

### 5.3 가드레일 (위반 시 abort + 사용자 보고)

| # | 룰 | 위반 시 |
|---|---|------|
| 1 | 수정 세션만 자동 commit | 평가/계획 세션은 자동 commit 시도 금지 |
| 2 | spec 이 변경한 파일만 stage | 무관한 untracked / 미관련 modified 가 스테이징되면 abort |
| 3 | `.env` / `*.key` / `secrets/` 매치 시 abort | 시크릿 commit 직전 차단 |
| 4 | `--no-verify` / `--amend` 금지 | hook 실패 시 fix → new commit (amend X) |
| 5 | `git push` 자동 금지 | push 는 항상 사용자만 |
| 6 | `git add -A` / `git add .` 금지 | 사이드 이펙트 격리 — 항상 specific path |

### 5.4 Uncommitted work 보호 (2026-04-26 사례 교훈)

> GOOGL: 사용자 손작업 v3 + Claude v4 모두 uncommitted 였다가 `git checkout` 으로 함께 사라짐. 자동 commit 룰 (§5.2) 도입으로 동일 사고 재발 가능성 감소 — uncommitted 가 빠르게 commit 되어 보호.

**여전히 유효한 룰**:
- `git checkout` / `git reset --hard` 같은 destructive 명령 *직전* 반드시 `git status`.
- uncommitted 손작업이 보이면 → `git stash` 또는 별도 branch 로 보존 후 destructive 명령.
- 평가 세션이 destructive 명령 제안 시 사용자에게 confirm 요청 (CLAUDE.md 룰).
````

### Edit 4 — `docs/operations.md` §0.A 다이어그램 [6] 갱신

**Old**:
````
### 0.A moat 사이클 (평가 → 적용)
```
[1] 사용자: 평가 세션에 "TICKER moat 어때?" 발화
[2] 평가 세션: moat read → spec 작성 (companies/{TICKER}/reviews/...)
[3] 사용자: spec 인터셉트·검토
[4] 사용자: 새 세션 → "수정 세션이야. {spec 경로} 적용해줘"
[5] 수정 세션: 사전 조건 확인 → Edit 적용 → status=applied
[6] git diff → commit
```
````

**New**:
````
### 0.A moat 사이클 (평가 → 적용)
```
[1] 사용자: 평가 세션에 "TICKER moat 어때?" 발화
[2] 평가 세션: moat read → spec 작성 (companies/{TICKER}/reviews/...)
[3] 사용자: spec 인터셉트·검토
[4] 사용자: 새 세션 → "수정 세션이야. {spec 경로} 적용해줘"
[5] 수정 세션: 사전 조건 확인 → Edit 적용 → status=applied
[6] 수정 세션: git diff 자가 검증 → 자동 commit (1 spec = 1 commit, §5.2)
[7] 사용자: git push (선택)
```
````

### Edit 5 — `docs/operations.md` §0.B 다이어그램 [6] 갱신

**Old**:
````
### 0.B 계획 사이클 (계획 → 적용)
```
[1] 사용자: 계획 세션에 "이번 분기 backlog 정리" 또는 "텔레그램 알림 spec 짜줘" 발화
[2] 계획 세션: backlog.md 읽기 + spec 작성 (docs/reviews/... 또는 automation/prompts/...)
[3] 사용자: spec 인터셉트·검토
[4] 사용자: 새 세션 → "수정 세션이야. {spec 경로} 적용해줘"
[5] 수정 세션: Edit 적용 → status=applied
[6] git diff → commit
```
````

**New**:
````
### 0.B 계획 사이클 (계획 → 적용)
```
[1] 사용자: 계획 세션에 "이번 분기 backlog 정리" 또는 "텔레그램 알림 spec 짜줘" 발화
[2] 계획 세션: backlog.md 읽기 + spec 작성 (docs/reviews/... 또는 automation/prompts/...)
[3] 사용자: spec 인터셉트·검토
[4] 사용자: 새 세션 → "수정 세션이야. {spec 경로} 적용해줘"
[5] 수정 세션: Edit 적용 → status=applied
[6] 수정 세션: git diff 자가 검증 → 자동 commit (1 spec = 1 commit, §5.2)
[7] 사용자: git push (선택)
```
````

### Edit 6 — `docs/plan.md` §0.7 Spec 위치 컨벤션 다음에 cross-ref 1줄

**Old**:
````
spec status: `pending` → 적용 세션이 `applied` 로 변경. 폐기되면 `superseded`.
````

**New**:
````
spec status: `pending` → 적용 세션이 `applied` 로 변경. 폐기되면 `superseded`.

**Editor 자동 commit**: 수정 세션은 1 spec 적용 후 자동 commit (1 spec = 1 commit). 가드레일·메시지 형식: `docs/operations.md` §5.
````

### Edit 7 — `CLAUDE.md` "단일 원천" 표에 commit 정책 행 추가

**Old**:
````
| 일상 운영 절차 (사이클·트러블슈팅) | `docs/operations.md` |
| 사용자 프로필·한도·환율·작업가설 | 메모리 |
````

**New**:
````
| 일상 운영 절차 (사이클·트러블슈팅) | `docs/operations.md` |
| Commit / Push 정책 (Editor 자동 commit, push 사용자) | `docs/operations.md` §5 + 메모리 `feedback_editor_auto_commit.md` |
| 사용자 프로필·한도·환율·작업가설 | 메모리 |
````

### Edit 8 — 신설 메모리 `feedback_editor_auto_commit.md`

**파일**: `~/.claude/projects/-Users-seosang-u-moat-journal/memory/feedback_editor_auto_commit.md`
**작업**: 새 파일 Write.

**내용**:
```markdown
---
name: 수정 세션 자동 commit / push 사용자 한정
description: 수정 세션은 1 spec 적용 후 자동 commit. push 는 항상 사용자만. 가드레일 6개 (시크릿 매치 abort, hook 우회 금지, 등).
type: feedback
---
**룰**: 1 spec 적용 = 1 commit, 수정 세션 자동. push 는 사용자만.

**Why**: 사용자 명시 (2026-04-26) — *"commit까진 알아서 했으면 좋겠는데, 나는 push만 하고 싶어서"*. commit 단계 손에서 제거 + push 외부 영향 분리. spec 파일 1개 ↔ commit 1개 1:1 매핑이라 audit trail 추적 깔끔 (git log 에서 spec 경로 인용으로 어느 사이클의 변경인지 즉시 확인).

**How to apply**:
- 수정 세션만 자동 commit. 평가/계획 세션은 그대로 사용자가 commit (또는 spec 파일만 미리 commit — audit trail 인터셉트용).
- 메시지 형식: `{영역}: {요지} (per {spec 경로})`. 예: `GOOGL moat v4: unknown 채우기 + Gate 4 (per companies/GOOGL/reviews/2026-04-26-v4.md)`.
- Stage: spec 이 변경한 파일만 `git add <specific>`. `git add -A` / `git add .` 금지.
- 가드레일 위반 시 abort + 사용자 보고:
  1. 평가/계획 세션이 자동 commit 시도
  2. 무관한 untracked / 미관련 modified 가 스테이징됨
  3. `.env` / `*.key` / `secrets/` 매치
  4. `--no-verify` / `--amend` 사용 강요됨 (hook 실패 시 fix → new commit)
  5. `git push` 자동
  6. `git add -A` / `git add .`
- 상세: `docs/operations.md` §5.
```

### Edit 9 — 메모리 `MEMORY.md` index 추가

**Old**:
````
- [세 세션 분리 패턴 (Planner/Reviewer/Editor)](feedback_three_session_pattern.md) — 평가는 moat·automation 편집 금지, 계획은 backlog/automation spec 생성, 수정은 spec 적용
````

**New**:
````
- [세 세션 분리 패턴 (Planner/Reviewer/Editor)](feedback_three_session_pattern.md) — 평가는 moat·automation 편집 금지, 계획은 backlog/automation spec 생성, 수정은 spec 적용
- [수정 세션 자동 commit / push 사용자 한정](feedback_editor_auto_commit.md) — 1 spec 적용 = 1 commit 자동, push 는 사용자만, 가드레일 6개
````

## 5. 미해결 backlog (다음 사이클)

- **§10 빠른 시작 체크리스트 (계획 사이클 0.B / 자동화 Phase 0 사이클 0.C)** — 본 spec Edit 2 가 한정 표시만 추가. 신설은 별도 Planner 사이클. `docs/backlog.md` §B 에 등록 권장 (수정 세션이 등록).
- **`companies/KO/`, `companies/MCD/` 진단 사이클** — `docs/backlog.md` §A 에 P0 등록되어 있음. 다음 Reviewer 사이클.
- **`docs/dollar-flow.md` 처리** — 본 사이클 무관, 별도 commit 또는 사용자 판단.
- **§5.1 표의 "spec 파일만 먼저 commit" 옵션 활용 패턴 정착 후 룰 명문화** — 현재는 선택. 1~2 사이클 후 결정.

## 6. 수정 세션 핸드오프 체크리스트

### Step 1 — Spec C 본문 적용

- [ ] 사전 조건: Spec A·B status=applied 인지 spec 파일 head 에서 확인. pending 이면 HALT.
- [ ] Edit 1: `docs/operations.md` §7 1줄
- [ ] Edit 2: `docs/operations.md` §10 제목·도입 한정
- [ ] Edit 3: `docs/operations.md` §5 commit 정책 전면 갱신
- [ ] Edit 4: `docs/operations.md` §0.A [6][7]
- [ ] Edit 5: `docs/operations.md` §0.B [6][7]
- [ ] Edit 6: `docs/plan.md` §0.7 commit cross-ref 1줄
- [ ] Edit 7: `CLAUDE.md` 단일 원천 표 commit 정책 행
- [ ] Edit 8: 메모리 `feedback_editor_auto_commit.md` 신설 (Write)
- [ ] Edit 9: 메모리 `MEMORY.md` index 추가
- [ ] 일관성 검증:
  - `grep -rn "두 세션" docs/ CLAUDE.md` → spec 파일 자체 인용 외 0건
  - `grep -rn "git diff → commit" docs/operations.md` → 0건
- [ ] 본 spec status: `pending` → `applied`

### Step 2 — 누적 미커밋 5 commit 분할 (자동 commit 룰의 첫 적용)

이번 사이클은 룰 도입 *이전* 변경(사이클 1·2)이 미커밋으로 쌓인 상태에서 룰이 시작되므로, 같은 형식으로 묶어서 정리. 순서대로:

| # | spec | stage 대상 | 메시지 |
|---|---|---|---|
| 1 | `companies/GOOGL/reviews/2026-04-26-v3-recovery.md` | `companies/GOOGL/moat.md`, `companies/GOOGL/moat-changelog.md` (v3 entry 부분), `companies/GOOGL/reviews/2026-04-26-v3-recovery.md` | `GOOGL moat v2→v3 recovery (per companies/GOOGL/reviews/2026-04-26-v3-recovery.md)` |
| 2 | `companies/GOOGL/reviews/2026-04-26-v4.md` | `companies/GOOGL/moat.md`, `companies/GOOGL/moat-changelog.md` (v4 entry 부분), `companies/GOOGL/reviews/2026-04-26-v4.md` | `GOOGL moat v3→v4: unknown 채우기 + Gate 4 (per companies/GOOGL/reviews/2026-04-26-v4.md)` |
| 3 | `docs/reviews/2026-04-26-3-session-rule-introduction.md` | `docs/plan.md` (§0/§8.x 부분), `CLAUDE.md`, `docs/operations.md`, `docs/reviews/2026-04-26-3-session-rule-introduction.md` | `3-session rule: Planner/Reviewer/Editor 분리 (per docs/reviews/2026-04-26-3-session-rule-introduction.md)` |
| 4 | `docs/reviews/2026-04-26-automation-skeleton-phase0.md` | `.gitignore`, `automation/`, `docs/backlog.md`, `docs/plan.md` (§5 부분), `docs/reviews/2026-04-26-automation-skeleton-phase0.md` | `automation: Phase 0 골격 + GOOGL backlog push prompt (per docs/reviews/2026-04-26-automation-skeleton-phase0.md)` |
| 5 | `docs/reviews/2026-04-26-3-session-rule-followup-ops-and-autocommit.md` | Step 1 의 모든 Edit 가 변경한 파일 + 본 spec | `ops: §7/§10 일관성 + Editor auto-commit 룰 (per docs/reviews/2026-04-26-3-session-rule-followup-ops-and-autocommit.md)` |

**중요 — commit 1·2 의 회고적 분할**:
- `companies/GOOGL/moat.md` 와 `moat-changelog.md` 는 v3·v4 가 누적된 *현재 상태*. v3-recovery commit 에는 v3 까지 만 들어가고, v4 commit 에 v4 변경이 추가되어야 함.
- 깔끔한 방법: `git stash` → v3-recovery 만 적용한 상태 시뮬레이션 어렵 (v4 도 이미 적용됨). 따라서 **단순화**: commit 1 에 두 파일 *전체*를 올리고, commit 2 는 두 파일에 변경 없음 → **빈 commit 회피를 위해 commit 1·2 를 합쳐 1 commit** 으로 처리:
  - 합친 메시지: `GOOGL moat v2→v4: v3 recovery + v4 unknown 채우기 + Gate 4 (per companies/GOOGL/reviews/2026-04-26-v3-recovery.md, ...v4.md)`
  - stage: `companies/GOOGL/moat.md`, `companies/GOOGL/moat-changelog.md`, `companies/GOOGL/reviews/2026-04-26-v3-recovery.md`, `companies/GOOGL/reviews/2026-04-26-v4.md`
- 따라서 **실제 commit 수 = 4** (v3+v4 합침, Spec A, Spec B, Spec C). 룰의 `1 spec = 1 commit` 은 *앞으로의* 룰 — 회고 변경에 한해 합침을 허용.

### Step 3 — 가드레일 적용

각 commit 직전 다음 확인:
- [ ] `git status` 에서 stage 대상이 spec 명시 파일과 일치
- [ ] `git diff --cached --name-only | grep -E "\.env|\.key|secrets/"` → 0건이어야 함
- [ ] `git diff --cached --name-only | grep -E "companies/(KO|MCD)|docs/dollar-flow"` → 0건이어야 함 (이번 사이클 범위 밖)
- [ ] `git add -A` / `git add .` 사용 금지 — 항상 specific path
- [ ] hook 실패 시 fix → new commit (`--amend` / `--no-verify` 금지)

### Step 4 — 보고

- [ ] `git log --oneline -10` (실제 commit 수, 메시지 확인)
- [ ] `git status --short` (남은 untracked: KO/, MCD/, dollar-flow.md — 사용자 별도 처리)
- [ ] 가드레일 위반 발생 여부
- [ ] 다음 안내: "사용자가 `git push` (선택). KO/MCD 진단은 다음 Reviewer 사이클, dollar-flow 처리는 사용자 판단."
