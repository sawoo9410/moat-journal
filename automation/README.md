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
