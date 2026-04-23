# Moat Journal — 설계 계획

> 매일 Claude Code가 자동 실행되어 기업별 기사를 수집·정리하고, 주/월/연/전체 모트(moat)를 계층적으로 축적하는 시스템.

---

## 1. 목표 및 전제

- **목표**: 각 기업의 "경쟁우위(moat)"가 시간이 지나며 어떻게 강화/침식되는지 증거 기반으로 추적.
- **전제**:
  - 매일 수십~수백 건의 뉴스 중 **대부분은 모트와 무관한 노이즈**. 필터가 가장 중요.
  - 모트 자체는 분기 단위로 천천히 변함. 매일 갱신할 대상은 "증거"이지 "thesis"가 아님.
  - 시스템은 **재생성 가능(idempotent)** 해야 함 → 일별 원본만 진짜 데이터, 나머지는 파생물.

---

## 2. 폴더 구조 (권장)

기존 제안(`google/2026/1월.md`)을 다음과 같이 개선합니다.

```
moat-journal/
├── companies/
│   ├── GOOGL/                          # 티커 기반 (브랜드명 변경/합병 대응)
│   │   ├── profile.yaml                # 메타데이터 (ticker, 별칭, 섹터, 소스)
│   │   ├── moat.md                     # 총괄 모트 (현재 canonical thesis)
│   │   ├── moat-changelog.md           # 모트 변경 이력 (언제 왜 바뀌었는가)
│   │   ├── pre-2025.md                 # 2025 이전 요약 (일회성, 고정)
│   │   ├── 2026/
│   │   │   ├── 2026-01.md              # 월 파일 (일별 entry 누적)
│   │   │   ├── 2026-02.md
│   │   │   └── ...
│   │   ├── 2027/
│   │   │   └── ...
│   │   └── summaries/                  # 파생물 (재생성 가능)
│   │       ├── 2026-W03.md             # 주간 요약 (ISO week)
│   │       ├── 2026-Q1.md              # 분기 요약
│   │       └── 2026.md                 # 연 요약
│   └── QCOM/
│       └── ...
├── docs/
│   ├── plan.md                         # 이 문서
│   ├── schema.md                       # 각 파일의 스키마 정의
│   └── automation.md                   # 자동화 설계 상세
├── scripts/                            # 수집/요약 스크립트 (선택)
└── .claude/
    └── settings.json                   # 훅, 권한
```

### 왜 이렇게 바꾸는가

| 변경 | 이유 |
|---|---|
| `google/` → `companies/GOOGL/` | 티커가 더 안정적. 알파벳/메타 등 리브랜딩에도 견고. `companies/` 네임스페이스로 루트 오염 방지. |
| `1월.md` → `2026-01.md` | 사전순 정렬, `ls 2026-*.md` 같은 패턴 매칭 가능, 다국어 중립. |
| `2025 이전 요약.md` → `pre-2025.md` | 공백/한글 파일명은 스크립트 처리 시 번거로움. |
| 주간/분기/연 요약을 `summaries/`로 분리 | **원본(월 파일)과 파생물(요약)을 물리적으로 구분** — 파생물은 언제든 재생성 가능. |
| `profile.yaml` 추가 | 별칭("Google", "Alphabet", "구글") 기반 dedup, 뉴스 소스 설정, 관련 기업 링크. |
| `moat-changelog.md` 분리 | `moat.md`는 항상 "현재 최선의 thesis". 이력은 따로 보존 — 과거 판단 근거 추적 가능. |

---

## 3. 파일 스키마

### 3.1 `profile.yaml`

```yaml
ticker: GOOGL
name: Alphabet Inc.
aliases: [Google, 구글, 알파벳, GOOG]    # dedup/매칭용
sector: Internet / Ad-tech
related: [META, MSFT, AMZN]              # 경쟁/보완 관계
sources:
  - type: rss
    url: https://...
  - type: query
    q: "Google OR Alphabet"
established: 1998
tracking_since: 2026-01-01
```

### 3.2 월 파일 (`2026-01.md`) — 원본 (source of truth)

```markdown
# GOOGL — 2026-01

## 2026-01-03

### Gemini 3 공개, 추론 벤치마크 reclaim
- **출처**: https://... (The Information, 2026-01-03)
- **요약**: 3줄 이내.
- **모트 관점**: `strengthen` — AI 모델 리더십 회복은 검색 방어선에 직결.
- **태그**: `#ai` `#search-defense`
- **신호 강도**: 3/5

### DOJ 검색 리메디 최종안 발표
- **출처**: ...
- ...

## 2026-01-04
...
```

**필드 설명**
- **모트 관점**: `strengthen` / `weaken` / `neutral` / `uncertain` — 4값 고정. 이게 있어야 월/연 요약에서 "이번 달 모트가 강해졌나?"를 집계 가능.
- **신호 강도**: 1~5. 낮은 값은 요약 단계에서 자동으로 컷.
- **태그**: 자유 형식이되 재사용 권장 (`#ai`, `#antitrust`, `#capex`, `#talent`).

### 3.3 `moat.md` — 총괄 모트

```markdown
# GOOGL Moat Thesis
_Last updated: 2026-04-15 · Version: v7_

## One-liner
검색 쿼리 데이터 플라이휠 × 배포 계약(default placement) × AI 인프라 수직통합.

## Moat Components
1. **데이터 플라이휠**: 쿼리 → 품질 → 쿼리. 견고.
2. **유통 계약**: Apple Safari default 등. **DOJ 리메디로 약화 진행 중 (2026-01 기준)**.
3. **인프라**: TPU 자체 실리콘. 강화 중.

## Active Threats
- DOJ 검색 antitrust 리메디 (2026)
- AI-native 검색 대체 (Perplexity, ChatGPT)

## Key Evidence (최근 6개월)
- → `2026-01.md#2026-01-03` (Gemini 3)
- → `2025-11.md#2025-11-14` (DOJ 예비안)
```

### 3.4 `moat-changelog.md`

```markdown
# Moat Changelog

## v7 — 2026-04-15
- 유통 계약 평가를 "견고"에서 "약화 진행 중"으로 하향. 근거: 2026-01 DOJ 예비안.

## v6 — 2026-01-10
- AI 인프라 항목을 moat component에 신규 추가. 근거: TPU v6 출시 후 캡티브 물량 증가.
...
```

---

## 4. 요약 계층 (Cadence)

| 주기 | 산출물 | 트리거 | 무엇을 하는가 |
|---|---|---|---|
| **일별** | 월 파일에 entry append | 매일 cron | 원본 수집·분류. **여기만 진짜 데이터**. |
| **주간** | `summaries/2026-W03.md` | 매주 월요일 | 그 주 entry 중 신호 강도 ≥3만 추려 3~5줄 요약. |
| **월간** | 월 파일 끝에 `## Month Summary` 섹션 자동 생성 | 월초 | 그 달의 모트 방향성 집계 (`strengthen` N건, `weaken` M건). |
| **분기** | `summaries/2026-Q1.md` + `moat.md` 갱신 검토 | 분기 종료 후 | **모트 thesis를 다시 쓸지 판단하는 체크포인트**. |
| **연간** | `summaries/2026.md` | 연말 | 그 해의 주요 변화. |
| **전체 모트** | `moat.md` + `moat-changelog.md` | 분기 체크포인트에서 필요 시 | thesis 자체 수정. **매월이 아닌 분기 단위** 권장. |

### 왜 분기인가?
- 매월 thesis를 수정하면 노이즈에 휘둘림.
- 매년 한 번은 너무 느려서 반대 증거가 쌓여도 놓침.
- 분기: 실적 발표 주기와 일치, 정보 밀도가 자연스럽게 높음.

---

## 5. 자동화 설계

### 5.1 실행 구조

```
[cron / launchd]  → Claude Code 세션 시작
      │
      ▼
  daily-ingest 스킬/프롬프트 실행
      │
      ├─ 1. profile.yaml 읽어 추적 기업 목록 확보
      ├─ 2. 각 기업별 뉴스 소스에서 최근 24h 기사 수집
      ├─ 3. 중복/무관 기사 필터 (alias 매칭, 키워드)
      ├─ 4. 기사별 요약 + 모트 관점 태깅
      ├─ 5. 해당 월 파일에 append (idempotent — 같은 URL은 skip)
      └─ 6. 실행 로그를 `.runs/YYYY-MM-DD.md`에 기록
```

### 5.2 주기별 훅

- **일별** (매일 새벽 예: 07:00): `/schedule` 또는 OS cron + `claude -p "daily-ingest GOOGL QCOM ..."`
- **주간** (월요일): 일별 훅 안에서 "오늘이 월요일이면 주간 요약도 생성" 분기.
- **분기**: 수동 트리거 권장 (`/loop` 또는 사용자 명령) — thesis 수정은 사람 판단 필요.

### 5.3 Idempotency 원칙

- 월 파일에 entry 추가 시 **URL 해시로 dedup**.
- 재실행해도 중복 entry 생기지 않아야 함.
- 파생 요약 파일(`summaries/*.md`)은 **항상 전체 재생성** — append 금지.

### 5.4 비용/토큰 관리

- 기업 수 × 기사 수 × 요약 토큰 → 금방 불어남.
- **필터를 모델이 아니라 규칙으로 먼저**: alias 매칭 + 소스 화이트리스트 → 그 다음에 요약.
- 월 파일이 너무 커지면 검색 성능/컨텍스트 비용 모두 상승 → 월 단위 분할이 적절한 경계.

### 5.5 출력 채널 — 텔레그램 일일 배달 (향후)

사용자 사용 패턴: **매일 아침 텔레그램으로 digest 수신 → 모바일에서 스캔**.

설계 함의:
- **Telegram 메시지 길이 제한 ~4096자** — deep entry는 1건/메시지 단위로 포맷.
- **light entry는 묶어서 한 메시지** (요약 불릿 리스트 형태).
- 생성 시점: daily-ingest 완료 직후 `.digests/YYYY-MM-DD.md` 생성 → Telegram Bot API push.
- 환경 변수: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- **지금 구현 X** — 포맷 확정 + 자동화 1차 안정화 이후 도입.

---

## 6. 주의할 함정

1. **Thesis drift**: moat.md가 증거에서 분리되어 혼자 떠다니게 됨 → "Key Evidence" 섹션에 원본 링크 강제.
2. **Survivorship bias**: 실패한 thesis는 changelog에만 남고 기억에서 지워짐 → changelog는 삭제 금지.
3. **노이즈 과다**: 신호 강도 태깅을 강제하지 않으면 주간 요약이 entry 전체를 그냥 나열하게 됨.
4. **기업 리브랜딩/합병**: 티커 변경 시 `profile.yaml`의 `aliases`에 이전 이름 보존.
5. **월 파일 비대화**: 월 1회 이상 추가되는 기업(GOOGL 등)은 월 파일이 수천 줄 될 수 있음 → 월 경계가 적절. 그 이상 분할은 과잉.
6. **언어**: 한국어/영어 혼용 시 태그/필드명은 영어로 통일 권장 (스크립트 처리 용이).

---

## 7. 다음 단계 (제안 순서)

1. **`docs/schema.md`** 작성 — 위 3번 섹션을 공식 스펙으로 분리.
2. **첫 기업 1개로 수동 파일럿** — GOOGL 한 달치만 수동으로 채워 포맷 검증.
3. **`profile.yaml` + 월 파일 포맷 확정**.
4. **자동화 스크립트/프롬프트 작성** — `docs/automation.md`.
5. **2~3개월 운영 후 구조 재평가** — 실제 써보면 뭐가 불편한지 드러남. 그 전에 과설계 금지.

---

## 8. 확정 사항

### 8.1 뉴스 소스 — 하이브리드 (유료 0원 시작)

| Tier | 소스 | 목적 |
|---|---|---|
| 1 | 각 기업 공식 IR·블로그 RSS | 1차 정보 |
| 2 | 섹터 매체 RSS (Reuters, CNBC, The Verge, OilPrice 등) | 일반 뉴스 |
| 3 | SEC EDGAR (8-K, 10-Q, 13F) | 공식 공시, 특히 OXY·SOUN 필수 |
| 보조 | 수동 URL 붙여넣기 | 유료지(FT/WSJ/Bloomberg/The Information) 핵심 기사 |

- **유료 뉴스 API는 시작 시 도입 안 함**. 2~3개월 운영 후 커버리지 부족 발견 시 NewsAPI/Polygon/Tiingo 추가 검토.
- 수동 크롤링은 비권장 (TOS/유지보수 리스크).

### 8.2 언어 — 한국어 베이스

- 본문: 한국어
- 고유명사·기술 용어: 영어 병기 허용
- **파일명·태그·필드명·스키마 키는 영어 고정** (스크립트 처리 안정성)

### 8.3 추적 기업 초기 리스트 (6개)

| 티커 | 섹터 | moat 성격 | 특별 체크 |
|---|---|---|---|
| GOOGL | 인터넷/광고 | 네트워크·데이터·유통 | DOJ 리메디, AI 검색 대체 |
| OXY | 에너지 | 원가 우위·자원 | 유가, 버핏 지분, Permian 생산량 |
| QCOM | 반도체 | 특허·표준 | Apple 모뎀 내재화, 로열티 소송 |
| SOUN | 소프트웨어(소형) | 형성 중 | **희석(ATM), 고객 집중도, 캐시 런웨이** |
| NVDA | 반도체 | 소프트웨어 생태계(CUDA) | 빅테크 자체 칩, 중국 수출 규제 |
| MCD | QSR | 브랜드·프랜차이즈·부동산 | SSSG, affordability, GLP-1 영향 |

### 8.4 실행 환경 — 로컬 macOS + Claude Code

- **launchd 권장** (cron보다 안정적 — sleep에서 깨워 실행 가능).
- 실행 방식: `claude -p "$(cat docs/prompts/daily-ingest.md)" --allowedTools Read Write Edit Bash WebFetch`
- 필수:
  - 비대화형(`-p`) 실행, 권한 프롬프트는 `--allowedTools`로 사전 허가
  - 실행 로그 `.runs/YYYY-MM-DD.log` 보존
  - 실패 시 macOS 알림(`osascript`) 또는 에러 파일 생성
  - 토큰 비용 관리: 프롬프트 내부에서 "제목/URL 필터 → 통과분만 상세 요약" 2단계 강제

### 8.6 엔트리 포맷 — Two-tier (Buffett 4축)

- **신호 강도 기준 분기**: 1~2 = light (한 줄), 3~5 = deep (Buffett scorecard).
- **Deep entry의 Buffett 4축**: ROIC · 가격결정력 · 자본집약도 · 산업 안정성.
- **moat.md 프레임**: 버핏 2007 shareholder letter 기반 (Castle 분석, ROIC 3분류, 10년 테스트, 무한 자본 공격 테스트).
- 포맷 상세: `companies/GOOGL/2026/2026-04.md` 상단 섹션 참조 (canonical template).

### 8.5 교차 참조 방식 — `profile.yaml` + cross-post 태그

**`topics/` 공통 서사 파일은 지금 도입하지 않음.** 6개월 운영 후 반복되는 큰 서사가 드러나면 그때 추가.

**(A) `profile.yaml`에 관계 선언** — 정적 관계

```yaml
related:
  - ticker: NVDA
    relation: supplier        # customer / competitor / supplier / peer / sector-linked
    note: TPU 자체 개발로 의존 감소 방향
```

**(B) 일별 entry에 `#cross:<TICKER>` 태그** — 사례별 연쇄

```markdown
### NVDA B200 물량 배분 발표
- **태그**: `#ai-chip` `#cross:GOOGL` `#cross:META`
```

주간/월간 요약 생성 시 `#cross:<TICKER>` 달린 entry는 해당 기업 요약에도 **링크로** 포함. 원본은 발표 기업 파일에만 — 중복 저장 금지.
