# Automation Skeleton Phase 0 — Spec

**Date**: 2026-04-26
**Author**: Claude (평가 세션 — Planner 룰 도입 *전* 작성. Spec A 적용 후엔 Planner 가 작성할 종류의 spec)
**Target file(s)**:
- 신설: `docs/backlog.md`
- 신설: `automation/README.md`
- 신설: `automation/prompts/weekly-googl-backlog-push.md`
- 신설: `automation/.env.example`
- 신설: `automation/src/.gitkeep`
- 갱신: `.gitignore`
- 갱신: `docs/plan.md` §5 (자동화 설계 — Phase 0/1 frame, §5.5 미세 갱신)

**Status**: `applied`
**Order**: Spec B. **사전 조건**: Spec A (`2026-04-26-3-session-rule-introduction.md`) 가 status=applied 여야 함.

---

## 1. 한 줄 변경 의도

자동화 디렉토리 골격을 만들고, 첫 자동화 타깃(GOOGL backlog 주간 푸시)을 *Phase 0 수동 프롬프트* 형태로 시작. 봇·cron·코드는 Phase 1로 분리.

## 2. 사전 조건 / 현재 상태

- **Spec A applied 확인**: `docs/reviews/2026-04-26-3-session-rule-introduction.md` 의 Status 가 `applied`. pending 이면 본 spec **HALT**.
- 현 `.gitignore` = 5 항목 (Claude Code 로컬 / macOS / 자동화 산출물 placeholder / 에디터)
- `automation/` 디렉토리 없음
- `docs/backlog.md` 없음
- GOOGL v4 spec §5 미해결 5개 — 본 spec 이 backlog.md 로 이주

## 3. 데이터 (출처 + 조회일)

- **참조 자산**: `~/investment-strategy/docs/telegram-alerts.md` (조회 2026-04-26) — `TelegramNotifier` 클래스 패턴, 발송 스케줄, 3회 재시도, rate limit (429 retry_after) 처리, HTML parse_mode. moat-journal Phase 1 에서 이 패턴 차용.
- **GOOGL v4 spec §5 미해결** (출처: `companies/GOOGL/reviews/2026-04-26-v4.md`):
  1. Pre-2021 ROIC (2015~2020) — stockanalysis 5년 한계
  2. `## Capital Allocation` 섹션 신설 — capex / buyback / 배당 / M&A
  3. `## Reinvestment Runway` 섹션 신설 — AI capex → 매출 전환 *속도*
  4. `## Unknown Backlog` consolidated 리스트 — 산재된 `_[unknown]_` 통합
  5. Worst case 확률 자가평가 — 정량 보강
- **사용자 결정** (본 세션 2026-04-26): 첫 자동화 타깃 = (d) 분기/주간 backlog 푸시, GOOGL 부터.

## 4. 적용할 변경

### Edit 1 — 신설 `docs/backlog.md`

**파일**: `docs/backlog.md`
**작업**: 새 파일 Write.

**내용**:
````markdown
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
````

### Edit 2 — 신설 `automation/README.md`

**파일**: `automation/README.md`
**작업**: 새 파일 Write (`automation/` 디렉토리 자동 생성).

**내용**:
````markdown
# automation/ — Phase 0 / 1 분리

> 자동화는 두 단계로 점진적. Phase 0 = 수동 prototype, Phase 1 = cron + bot.
> 룰은 `docs/plan.md` §0.7 (3-세션) + §5 (자동화 설계).

## 디렉토리 구조

```
automation/
├── README.md                        ← 본 파일
├── .env.example                     ← 환경변수 템플릿 (실 값은 .env, gitignore)
├── prompts/                         ← Phase 0 자산. 수동 실행 프롬프트.
│   └── weekly-googl-backlog-push.md
├── src/                             ← Phase 1 자산. 코드.
│   └── .gitkeep                     ← Phase 0 동안 비어 있음
└── data/                            ← 실행 산출물. gitignore.
```

## Phase 0 — 수동 prototype (지금)

**목적**: 프롬프트 패턴이 안정 답을 내는지 검증. 봇·cron 없음.

**실행 절차**:
1. 일반 Claude Code 세션 시작 (어떤 세션이든 무관 — 기본 Reviewer 가능)
2. `automation/prompts/{topic}.md` 내용을 그대로 붙여넣기 (또는 `@automation/prompts/{topic}.md 실행해줘`)
3. Claude 답변 확인
4. 사용자가 직접 텔레그램에 (필요 시) 복사·전송
5. 매 실행 결과를 `automation/data/manual-runs/{YYYY-MM-DD}-{topic}.md` 같이 기록 (선택, gitignore)

**Phase 1 진입 조건**: 같은 프롬프트 3회 연속 *유용한* 답 (사용자 판단). 이 시점에 Planner 세션이 Phase 1 spec 작성.

## Phase 1 — cron + bot (Phase 0 통과 후)

**예상 구조** (확정 X — Phase 1 spec 작성 시 결정):
- `src/notifier.py` — Telegram Bot API wrapper. `~/investment-strategy/docs/telegram-alerts.md` `TelegramNotifier` 패턴 차용.
- `src/run.py` — `claude --print < prompts/{topic}.md` 호출 → 출력 캡처 → notifier 발송.
- macOS launchd 또는 cron entry — 주기 정의.
- `.env` — `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

**검증 필요** (Phase 1 spec 에 `_[검증 필요]_` 박스):
- `claude --print` headless 모드 권한 모드, MCP 설정
- 같은 질문 → 같은 답 일관성 (WebSearch 노이즈)
- 토큰 비용 / 실행 시간

## 보안

| 단계 | 정책 |
|------|------|
| **MVP (지금)** | `.env` + `.gitignore`. 1인 프로젝트, 외부 노출 표면 적음. |
| **격상 조건** | GitHub Actions / 클라우드 이전 → GitHub Secrets / Cloud Secret Manager. 토큰 3개+ 늘면 `direnv` 또는 `1Password CLI`. |

`.gitignore` 항목 (Spec B 적용 시 추가됨):
- `.env`, `.env.local`
- `*.key`
- `secrets/`
- `automation/data/`

## 봇 분리

moat-journal 전용 봇 신설. `~/investment-strategy` 의 봇과 chat 분리해 알림 출처 혼동 없게.
````

### Edit 3 — 신설 `automation/prompts/weekly-googl-backlog-push.md`

**파일**: `automation/prompts/weekly-googl-backlog-push.md`
**작업**: 새 파일 Write (`automation/prompts/` 디렉토리 자동 생성).

**내용**:
````markdown
# Prompt — Weekly GOOGL Backlog Push

> Phase 0 수동 실행 프롬프트. 매주 월요일 1회.
> 일반 Claude Code 세션에서 본 파일 내용을 붙여넣거나 `@automation/prompts/weekly-googl-backlog-push.md 실행해줘`

---

## 너의 역할

너는 사용자(상우)의 GOOGL moat 사이클 진행을 도와주는 어시스턴트. 본 프롬프트는 **매주 월요일 아침에 1회 실행**되어, GOOGL backlog 우선순위 3개를 텔레그램 메시지 형식으로 만든다.

## 입력

다음 두 파일을 읽어:
1. `docs/backlog.md` — 전체 backlog
2. `companies/GOOGL/moat.md` — 현재 thesis (Version 확인)

## 작업

1. `docs/backlog.md` §A.GOOGL 표에서 P0 → P1 → P2 우선순위로 항목 추출.
2. 위에서 **3개**를 골라 우선순위 정렬:
   - 단순 등급 카운트가 아닌 *지금 사이클에 진행 가능한가* 판단.
   - 예: "Pre-2021 ROIC"는 데이터 발굴 필요(P2)지만, "Capital Allocation 섹션 신설"은 평가 세션이 즉시 시작 가능(P1).
3. `companies/GOOGL/moat.md` 헤더 Version 확인.
4. 다음 형식으로 **하나의 텔레그램 메시지** 생성 (HTML, ~1500자 이내).

## 출력 형식 (HTML)

```html
<b>📊 GOOGL Weekly Backlog — {YYYY-MM-DD}</b>
<i>moat.md: {버전}</i>

<b>이번 주 우선 3개</b>

1. <b>{항목 1 제목}</b>
   {1~2줄 설명. 어떤 액션이 필요한지.}

2. <b>{항목 2 제목}</b>
   {1~2줄 설명.}

3. <b>{항목 3 제목}</b>
   {1~2줄 설명.}

<b>다음 액션</b>
{사용자가 *오늘* 할 수 있는 액션 1줄. 예: "평가 세션에 'GOOGL Capital Allocation 섹션 신설 spec 짜줘' 발화."}

<i>출처: docs/backlog.md §A.GOOGL</i>
```

## 가드레일

- `docs/backlog.md` 를 *직접 편집하지 마*. 본 프롬프트는 어느 세션도 아닌 *읽기 전용* 보고용.
- 새 backlog 항목을 *발견*해도 출력에 포함만 하고 backlog.md 에 추가 안 함 — 사용자가 다음 Planner 세션에서 처리.
- 데이터를 만들어내지 마. backlog.md / moat.md 에 *명시된* 것만.
- HTML 길이 제한 ~4096자 (Telegram). 1500자 목표.
- 이모지는 헤더 1개만 (📊). 본문에는 사용 X.

## 사용자 후속 작업

출력을:
- 그대로 텔레그램으로 복사·전송 (Phase 0)
- 또는 Phase 1 cron 자동 발송 (Phase 1 도달 후)
````

### Edit 4 — 신설 `automation/.env.example`

**파일**: `automation/.env.example`

**내용**:
````
# Telegram Bot — moat-journal 전용 (investment-strategy 봇과 분리)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# 향후 (Phase 1 진입 시 추가)
# CLAUDE_BIN=/usr/local/bin/claude
# LOG_LEVEL=info
````

### Edit 5 — 신설 `automation/src/.gitkeep`

**파일**: `automation/src/.gitkeep`
**내용**: (빈 파일)
**목적**: Phase 0 동안 빈 디렉토리 유지를 위한 placeholder.

### Edit 6 — `.gitignore` 갱신

**파일**: `.gitignore`

**Old (마지막 부분)**:
````
# 에디터
.vscode/
.idea/
*.swp
````

**New**:
````
# 에디터
.vscode/
.idea/
*.swp

# 환경변수 / 시크릿
.env
.env.local
*.key
secrets/

# 자동화 실행 산출물
automation/data/
````

### Edit 7 — `docs/plan.md` §5 헤더 직후 §5.0 Phase 분리 추가

**파일**: `docs/plan.md`

**Old**:
````
## 5. 자동화 설계

### 5.1 실행 구조
````

**New**:
````
## 5. 자동화 설계

### 5.0 Phase 0 / Phase 1 분리

자동화는 두 단계로 점진적 도입.

| Phase | 목적 | 산출물 | 코드 |
|-------|------|--------|------|
| **Phase 0 — 수동 prototype** | 프롬프트 패턴 검증 | `automation/prompts/*.md` (수동 실행) | 0 |
| **Phase 1 — cron + bot** | 무인 자동화 | `automation/src/*` + cron entry | Telegram wrapper, run.py |

**Phase 1 진입 조건**: 같은 프롬프트 3회 연속 *유용한* 답. Planner 세션이 Phase 1 spec 작성, Editor 세션이 코드 적용.

상세 룰: `automation/README.md`. 첫 프롬프트: `automation/prompts/weekly-googl-backlog-push.md`.

### 5.1 실행 구조 (Phase 1 — 향후)
````

### Edit 8 — `docs/plan.md` §5.5 텔레그램 섹션 미세 갱신

**Old (§5.5 끝부분)**:
````
- 환경 변수: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- **지금 구현 X** — 포맷 확정 + 자동화 1차 안정화 이후 도입.
````

**New**:
````
- 환경 변수: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — `automation/.env.example` 참조.
- **참조 패턴**: `~/investment-strategy/docs/telegram-alerts.md` 의 `TelegramNotifier` 클래스 (requests 직접 호출, 3회 재시도, rate limit 처리, HTML parse_mode). Phase 1 에서 차용.
- **봇 분리**: moat-journal 전용 봇 신설 (investment-strategy 봇과 chat 분리).
- **Phase 0 동안**: 프롬프트만 (`automation/prompts/`), 발송은 사용자 수동 복사. Phase 1 진입 조건은 §5.0.
````

## 5. 미해결 backlog (다음 사이클)

- **Phase 0 → Phase 1 전환 spec** — Phase 0 프롬프트가 안정화되면 Planner 세션이 작성. `automation/src/` 코드 spec.
- **MCD/KO P0 진단** — `docs/backlog.md` §A.MCD/KO 에 등록. Reviewer 세션이 사이클 진입.
- **OXY/QCOM/SOUN/NVDA 스캐폴드** — `docs/backlog.md` §A 에 P2 등록.
- **(a) IR D-3 reminder 자동화** — Phase 0 (d) 안정화 후 두 번째 프롬프트 추가.
- **`docs/plan.md` §5.1~§5.4 의 "daily-ingest" 모델 vs Phase 0/1 모델 정합성**: 기존 §5.1~§5.4 는 *과거 설계 (자동 daily ingest)*, Phase 0/1 은 *새 모델 (사용자 트리거 weekly push)*. 일관성 정리는 다음 Planner 사이클.

## 6. 수정 세션 핸드오프 체크리스트

- [ ] **사전 조건**: `docs/reviews/2026-04-26-3-session-rule-introduction.md` Status = `applied` 인지 확인. `pending` 이면 **HALT** 후 사용자 보고.
- [ ] Edit 1: `docs/backlog.md` 신설 (Write)
- [ ] Edit 2: `automation/README.md` 신설 (Write — `automation/` 디렉토리 자동 생성)
- [ ] Edit 3: `automation/prompts/weekly-googl-backlog-push.md` 신설 (Write — `automation/prompts/` 자동 생성)
- [ ] Edit 4: `automation/.env.example` 신설 (Write)
- [ ] Edit 5: `automation/src/.gitkeep` 신설 (Write — `automation/src/` 자동 생성)
- [ ] Edit 6: `.gitignore` 갱신 (Edit)
- [ ] Edit 7: `docs/plan.md` §5 헤더 직후 §5.0 추가 (Edit)
- [ ] Edit 8: `docs/plan.md` §5.5 미세 갱신 (Edit)
- [ ] 검증:
  - `ls automation/` → README.md, .env.example, prompts/, src/ 모두 존재
  - `ls automation/.env` → 없어야 함 (gitignore 만 적용; 실제 .env는 사용자가 별도 작성)
  - `grep "^.env$" .gitignore` → 매치
  - `git status --short` → 신규 파일 5개 (`automation/` 4개 + `docs/backlog.md`) + `.gitignore` 수정 + `docs/plan.md` 수정 보임
- [ ] 본 spec status: `pending` → `applied`
- [ ] 사용자 보고: `git status --short`, `git diff --stat`
- [ ] git commit 은 사용자가 직접 — 본 세션은 add/commit 금지
