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
