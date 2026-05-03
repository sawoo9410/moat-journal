# Operations — 세 세션 분리 워크플로

> 이 저장소를 *매일* 어떻게 굴리나.
> 룰의 **이유**는 `plan.md` §0.7, **행동**은 여기.
> 세 세션 = Reviewer (기본) / Planner (명시) / Editor (명시).

---

## 0. 한 사이클

세 가지 사이클이 있음.

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

### 0.C 자동화 실행 사이클 (Phase 0 수동 / Phase 1 cron)
```
[Phase 0] 사용자: 일반 Claude 세션에 automation/prompts/{topic}.md 내용 → 결과 받기 → 사람이 텔레그램 직접 발송
[Phase 1] cron → claude --print → WebSearch → 요약 → Telegram Bot API → 발송
```

핵심: **각 세션은 다른 세션에서**. 같은 세션에서 평가/계획 후 바로 수정 X.

---

## 0.5 세션 시작 공통 루틴 (모든 세션)

모든 세션은 시작 시 다음을 수행:

1. **lessons.md 스캔** — `docs/lessons.md`에서 해당 회사 또는 해당 작업 유형의 교훈 확인
2. **mini-plan 출력** (3단계 이상 작업 시) — 무엇을 어떤 순서로 할지 콘솔에 1~5줄 plan
3. **세션 선언** — 현재 세션 유형 + 수행할 작업 1줄 명시

> 단순 Q&A (1~2턴)에는 이 루틴 생략 가능.

---

## 1. 평가 세션 시작 (기본 모드)

기본 모드 = 평가 세션. 별도 트리거 불필요. 그냥 평소처럼 발화하면 됨.

**발화 예시**:
- "GOOGL moat 어때?"
- "MCD moat에 dividend layer 빠진 거 같은데 봐줘"
- "KO 평가 한번 돌려봐"
- "방금 OXY moat 다시 봐줘"
- "이 spec 적용 전에 한 번 더 검토해줘" (← spec 자체에 대한 review도 평가 세션 영역)

**평가 세션이 *하는* 것**:
- 모트 파일을 *읽고* (Read only)
- `plan.md` §0 Role 에 따라 평가 (Learn / Draft / Stress-test 모드 — §6 참조)
- 개선 spec을 `companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic}.md` 에 **Write**
- 콘솔에 요약 + spec 경로 보고

**평가 세션이 *하지 않는* 것**:
- `moat.md`·`dividend.md`·`moat-changelog.md`·월별 entry·`profile.yaml` 직접 편집
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

수정 세션은 **명시적 트리거**가 필요. **새 Claude Code 세션을 여는 게 권장** — 같은 세션에서 모드 전환하면 평가 컨텍스트가 수정 판단에 섞임.

**발화 예시** (셋 중 하나):
- "**수정 세션이야**. `companies/GOOGL/reviews/2026-04-26-v4.md` 적용해줘"
- "**edit mode** — spec apply: `./companies/GOOGL/reviews/2026-04-26-v3-recovery.md`"
- "이 spec 받아서 moat 파일 **수정해줘 — 수정 세션 모드**"

**수정 세션이 *하는* 것**:
1. spec 파일을 Read (Reviewer spec / Planner spec 모두 가능)
2. **사전 조건 확인** (예: 헤더 Version 매칭, 의존 spec applied 여부). 실패 시 **HALT** → 사용자에게 보고
3. Edit 1, 2, ... 순서대로 *정확히* 적용
4. spec 의 Status 를 `pending` → `applied` 로 변경 (status 필드는 모든 세션이 변경 가능)
5. (선택) 결과 요약

**수정 세션이 *하지 않는* 것**:
- spec에 없는 추가 변경 (즉흥 개선 X — 즉흥적 개선이 떠오르면 평가 세션에 다음 review 요청)
- spec 내용 의심·재검토 (사용자가 이미 인터셉트 단계에서 검토함)
- 평가 의견 추가

**수정 세션 완료 전 체크리스트** (commit 직전):
1. ☐ `git diff` 가 spec Edit 항목과 1:1 대응
2. ☐ spec 에 없는 "bonus" 변경 없음
3. ☐ 사전 조건 (version, 의존 spec) 확인 완료
4. ☐ spec status=`applied` 로 변경 완료
5. ☐ commit message 형식 준수 (`{영역}: {요지} (per {spec 경로})`)

---

## 3. Spec 파일 — 명명·위치·생애주기

### 위치
```
companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic-or-version}.md
```

### 명명 예시

| 파일명 | 용도 |
|--------|------|
| `2026-04-26-v4.md` | 버전업 패치 (가장 흔한 형태) |
| `2026-04-26-v3-recovery.md` | 1회성 복원 — 특수 case |
| `2026-05-15-quarterly-checkpoint.md` | 분기 체크포인트 review |
| `2026-06-01-data-refresh.md` | 데이터만 갱신 (thesis 동일) |
| `2026-07-10-stress-test-pre-buy.md` | 매수 직전 5 gates stress-test |

### Status 생애주기
```
pending → applied
```
(필요 시 `superseded` 도 가능 — 다른 spec 으로 대체된 경우)

### 형식 (필수 섹션)
1. 한 줄 변경 의도
2. 사전 조건 / 현재 상태
3. 데이터 (출처 + 조회일)
4. 적용할 변경 — `Edit N` 단위 (파일 / 위치 / Old / New)
5. 미해결 backlog
6. 수정 세션 핸드오프 체크리스트

세부는 `plan.md` §0.7. 모범 예시는 `companies/GOOGL/reviews/2026-04-26-v4.md`.

---

## 4. 적용 순서 / 의존성

여러 spec이 쌓이면 **사전 조건이 의존성을 정의**. 일반적으로 날짜 + 버전 순.

**예 — GOOGL 오늘 상태**:
```
1. 2026-04-26-v3-recovery.md  (사전 조건: v2)  → 적용 → moat.md 가 v3
2. 2026-04-26-v4.md           (사전 조건: v3)  → 적용 → moat.md 가 v4
```

수정 세션이 사전 조건 mismatch 발견 시:
- **HALT** → 평가 세션에 보고
- 평가 세션이 빈 단계 spec 작성 (예: "v2 → v3 spec이 누락됐다, 만들어줘")

---

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

---

## 6. 평가 세션 *내부* 모드 (Learn / Draft / Stress-test)

`plan.md` §0.5 상세. 운영 관점 요약:

| 모드 | 언제 | 산출물 |
|------|------|--------|
| **Learn** (기본) | 새 회사 입문, 개념 학습 | 설명·정의·포인터 (spec 아닐 수 있음) |
| **Draft** | 1차 spec 작성 | spec 파일 (`pending`) |
| **Stress-test** | 매수 결정 직전 검증 | 5 gates 통과 여부 + 보강 spec |

전환 트리거 = 사용자 발화 (`plan.md` §0.5 표 참조). 세션 도중 전환 가능.

---

## 7. 사용자가 *직접* 모트 편집

사용자(상우)는 언제든 moat 파일을 직접 편집 가능. **세 세션 분리 룰은 Claude에게만 적용**.

사용자가 직접 편집했을 때 권장 흐름:
1. 적당한 시점에 **commit** — uncommitted 로 두면 다음 destructive 명령에 휘둘릴 수 있음 (오늘 v3 사례).
2. 다음 평가 세션 시작 시 *알리기* — "방금 손으로 X 추가했어, 이걸 반영해서 review 해줘".
3. 평가 세션은 그 변경을 인지하고 review 베이스라인으로 사용.

---

## 8. 여러 회사 동시 운영

- **동시 review 가능** — 평가 세션 한 번에 GOOGL·MCD·KO 등 여러 회사 spec 작성 OK.
- **각 spec은 별도 파일** — cross-company spec 금지. (applied 되돌리기 / partial apply 어려움)
- 수정 세션도 한 세션에서 여러 spec 적용 가능. 사전 조건 의존성 순서로.

---

## 9. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 평가 세션이 moat 파일 직접 편집함 | 룰 위반 (오늘 v4 패치 사례) | `git checkout` 으로 되돌리기 → 같은 변경을 spec으로 재작성 |
| 평가 세션이 명시 없이 수정 모드로 자가 전환 | 룰 미준수 | "평가 세션 모드로 돌아가" 명시. CLAUDE.md 룰 재읽기 요청 |
| 수정 세션이 사전 조건 무시하고 적용함 | 사전 조건 검증 누락 | `git diff` 로 잘못 적용 확인 → `git checkout` 후 평가 세션에 재시도 요청 |
| spec applied 했는데 commit 안 함 | 사용자 누락 | 즉시 commit. 다음 destructive 명령 전에 반드시. |
| moat 파일이 v2 인데 v4 spec 적용 시도 | 중간 spec 누락 (v2→v3 빠짐) | 수정 세션이 HALT 보고 → 평가 세션에 v2→v3 recovery spec 요청 |
| 평가 세션이 spec 너무 길게 씀 | Edit-by-Edit 분량 과다 | "특수 case spec" 으로 표시 + 전체 Write 형식 허용 (오늘 v3-recovery 사례) |
| 같은 회사에 review 가 너무 자주 쌓임 | review cadence 미정 | `plan.md` §4 cadence (분기 단위 thesis 갱신) 따름. 일별/월별 변경은 월 파일 entry에 기록 |

---

## 10. 빠른 시작 체크리스트 (moat 사이클)

처음 *모트 review* 사이클(0.A) 돌릴 때:

> 계획 사이클(0.B) / 자동화 Phase 0 사이클(0.C) 의 빠른 시작 체크리스트는 별도 사이클로 신설 예정 (`docs/backlog.md` §B).

- [ ] **평가 세션** 시작 → "TICKER moat 어때?" 발화
- [ ] 평가 세션이 `companies/{TICKER}/reviews/{YYYY-MM-DD}-{topic}.md` 생성 → 경로 보고
- [ ] spec 검토 (인터셉트 단계) — 마음에 안 들면 평가 세션에 수정 요청
- [ ] (선택) spec 만 먼저 commit — audit trail 보존
- [ ] **새 Claude Code 세션** 열기
- [ ] "**수정 세션이야**. `{spec 경로}` 적용해줘" 발화
- [ ] 수정 세션이 사전 조건 확인 → Edit 적용 → spec status=applied
- [ ] `git diff` 로 검증
- [ ] commit (메시지에 spec 경로 인용)
- [ ] (선택) 평가 세션 다시 열어 "적용 결과 검토" — 다음 review cycle 진입

---

## 참고 cross-link

- 룰의 *이유* 와 *형식 명세*: `plan.md` §0.7
- Always-on 활성화 룰: `CLAUDE.md`
- 사용자 프로필·한도·환율: 메모리 (`~/.claude/projects/-Users-seosang-u-moat-journal/memory/`)
- 사용자 자유 편집 권한: 본 문서 §7
