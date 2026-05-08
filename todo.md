# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

진행 순서: **A (긴급 코드 수정) → B (신규 종목 데이터) → Phase 4 (구조 개편)**.
Phase 1~3(텔레그램 봇, 기본 daily/rollup 인프라, 자동화 등록)은 완료.
긴급 수정 E.0/E.1/E.2 모두 종결 — cron→LaunchAgent + Keychain OAuth 토큰 주입으로 자동화 정상 동작 확인.

---

## A. (긴급) 텔레그램 출처 누수 차단

증상: MCD 5/9 텔레그램 detail 메시지 끝에 `Sources:` + URL 7개가 그대로 발송됨.

원인 (2중):
1. claude가 답변 끝에 `Sources:` 블록을 자동 부착 (프롬프트의 "출처 표시 금지"는 각 섹션 내부에만 적용된 것으로 해석됨)
2. 파서 정규식 `r"###\s+(.+?)\n(.*?)(?=\n###\s|\Z)"`가 `### 한줄평` 섹션을 다음 `### `이나 문서 끝까지 캡처 → `Sources:`는 `### `가 아니므로 한줄평 섹션에 통째로 흡수 → `build_detail`이 그대로 텔레그램으로 송출

3중 방어. **A.1 (파서)**가 본질적 차단. A.2/A.3은 보강·정합성.

### A.1 파서 방어 — `parse_output` 진입 전 raw 트림 (필수)

`automation/src/daily_moat.py`의 `parse_output(text)` 함수 첫 줄:

```python
def parse_output(text: str) -> dict:
    # 트레일링 출처 블록 제거 (claude가 답변 끝에 Sources:/References:/출처: 자동 부착하는 케이스)
    m = re.search(r"\n+(Sources?|References?|출처|참고문헌)\s*:", text, flags=re.IGNORECASE)
    if m:
        text = text[: m.start()].rstrip() + "\n"
    sections: dict[str, str] = {}
    ...
```

이 한 컷으로 어떤 섹션이든 트레일링 출처 흡수 차단. 같은 처리를 `rollup.py`의 출력 파이프라인에도 적용 검토 (현재는 raw를 그대로 저장하므로 텔레그램 누수 우려 적지만, 향후 분기/연간도 텔레그램 송출 시 동일 트림 필요).

### A.2 프롬프트 강화 — `automation/prompts/daily.md`

기존 "출처 표시 금지" 라인에 트레일링 블록 명시 추가. 출력 형식 섹션 끝 또는 지시사항 끝에:

```markdown
## 절대 금지

- 출력 끝에 `Sources:` / `References:` / `출처:` / `참고문헌` 등 어떤 형태로도 출처/링크/매체 목록 섹션을 부착하지 말 것.
- URL, 매체명, 정확한 헤드라인 인용 일체 금지 (각 섹션 내부 + 트레일링 모두).
- 사실의 *내용*만 기술. "Bloomberg 보도", "CNBC에 따르면" 같은 출처 지칭 표현도 금지.
```

### A.3 `build_detail` CLAUDE.md 스펙 정합화

[automation/src/daily_moat.py:144 build_detail()](automation/src/daily_moat.py:144) 현재 `🟢 호재` / `🔴 악재` bullets를 텔레그램에 포함 → CLAUDE.md 스펙 위반.

CLAUDE.md 스펙대로 detail 메시지 = 헤더 + `💰 가격/지표` 한 줄 + `💬 한줄평`만:

```python
def build_detail(date: str, ticker: str, parsed: dict) -> str:
    bar = "━" * 16
    lines = [
        bar,
        f"  {ticker} — {date}",
        f"  Moat: {parsed['moat_status'] or '(미상)'}",
        bar,
        "",
    ]
    val = parsed["valuation"].strip()
    if val:
        # multi-line bullet → 한 줄로 압축 (첫 줄만 또는 ' / '로 join)
        val_one_line = " / ".join(_normalize_lines(val)[:3])
        lines.append(f"💰 {val_one_line}")
        lines.append("")
    comment = parsed["comment"].strip()
    if comment:
        lines.append(f"💬 {comment}")
    return "\n".join(lines).strip() + "\n"
```

호재/악재 bullets는 월간 .md 파일에는 그대로 보존 (이미 raw 저장이라 손댈 필요 없음).

### 검증 절차 (수정 세션 종료 후)

1. 수정 후 LaunchAgent 1회 수동 트리거 (`launchctl start com.moat-journal.daily`)
2. 텔레그램 메시지 — Sources 블록 / 호재·악재 bullets 모두 없는지 확인
3. 월간 .md 파일 — 호재/악재/Valuation bullets 정상 보존, Sources 블록은 제거되어도 무방 (파서가 raw에서 잘라냄)

---

## B. 신규 종목 8개 추가

config 4종목(GOOGL, MCD, KO, O) → 12종목으로 확장.

추가 종목 (8개): **OXY, QCOM, NVDA, NXPI, TXN, AMZN, AMBQ, AVGO**

종목 식별:
- OXY — Occidental Petroleum (에너지, 배당)
- QCOM — Qualcomm (반도체, 모바일/IoT, 배당)
- NVDA — NVIDIA (반도체, AI 가속기)
- NXPI — NXP Semiconductors (반도체, 자동차/IoT, 배당)
- TXN — Texas Instruments (반도체, 아날로그/임베디드, 배당 compounder)
- AMZN — Amazon (이커머스 + AWS)
- AMBQ — **Ambiq Micro** (반도체, 초저전력 칩, 2025 IPO)
- AVGO — Broadcom (반도체, 인프라 + VMware, 배당 성장)

### B.1 종목별 데이터 스캐폴드 생성 (계획 세션 작업)

각 종목당 다음 파일 생성. 기존 KO/MCD/GOOGL/O 패턴 따름.

| 파일 | 필수 여부 | 내용 |
|------|----------|------|
| `companies/{TICKER}/moat.md` | **필수** | 버핏식 4축 thesis + Castle/ROIC/10년 테스트. daily 분석의 입력. |
| `companies/{TICKER}/profile.yaml` | **필수** | 종목 메타 (이름, 섹터, 시총, 핵심 지표, 트래킹 시작일 등) |
| `companies/{TICKER}/dividend.md` | 배당주만 | OXY, QCOM, NXPI, TXN, AVGO (compounder dividend 후보) |
| `companies/{TICKER}/pre-2025.md` | 필요 시 | 2025 이전 누적 컨텍스트가 있는 경우만 (OXY 등) |
| `companies/{TICKER}/moat-changelog.md` | 선택 | 최초 thesis 작성일 1줄 |

**작성 방식**: 계획 세션에서 종목 1개씩 WebSearch 기반으로 moat 4축 분석 → moat.md 초안 작성. 8개 모두 처리. 순서는 무관.
**AMBQ 주의**: 2025 IPO로 상장 이력 짧음 → moat thesis는 잠정(thesis tentative) 표기, pre-2025.md 생략 가능.

### B.2 `automation/config.yaml` tickers 갱신

```yaml
tickers:
  - GOOGL
  - MCD
  - KO
  - O
  - OXY
  - QCOM
  - NVDA
  - NXPI
  - TXN
  - AMZN
  - AMBQ      # Ambiq Micro
  - AVGO
```

### B.3 LaunchAgent / cron 변경 불필요

LaunchAgent wrapper는 config.yaml의 tickers를 읽으므로 추가 작업 없음. 단 12종목 × claude --print(평균 30~60s) ≈ 6~12분 → 기존 timeout=300s/종목은 문제 없음.

---

## Phase 4 — 구조 개편 (월간 누적 + 독립 분석)

기존 구조(daily 파일/일 + daily→quarterly→annual 계단식 압축)를 폐기하고:
- **파일**: 일별 파일 폐지 → **월간 누적 파일** (`companies/{TICKER}/{YYYY}/{YYYY-MM}.md`)
- **분석**: 계단식 압축 폐지 → daily/quarterly/annual **각자 독립 분석** (각자 다른 목적, 다른 입력)

### 4.1 디렉토리 구조 변경

```
companies/{TICKER}/
  moat.md                       ← thesis (변경 없음)
  moat-changelog.md             ← (변경 없음)
  dividend.md                   ← (변경 없음)
  profile.yaml                  ← (변경 없음)
  pre-2025.md                   ← (변경 없음)
  {YYYY}/
    {YYYY-MM}.md                ← 일일 분석 누적 (예: 2026/2026-05.md)
    quarterly-Q{N}.md           ← 분기 독립 분석 (예: 2026/quarterly-Q2.md)
    annual.md                   ← 연간 독립 회고 (예: 2026/annual.md)
```

기존 `daily/`, `quarterly/`, `annual/` 디렉토리는 사용 안 함.

### 4.2 월간 누적 파일 포맷

`companies/{TICKER}/{YYYY}/{YYYY-MM}.md` — 한 파일에 그 달의 daily 분석을 append.

```markdown
# {TICKER} — {YYYY}년 {M}월

## {YYYY-MM-DD}

(claude --print로 받은 daily 분석 결과 그대로)

---

## {YYYY-MM-DD}

...
```

**Append 규칙:**
- 파일 없으면 헤더(`# {TICKER} — {YYYY}년 {M}월\n\n`) 포함하여 새로 생성
- 파일 있으면 끝에 `\n## {날짜}\n\n{분석}\n\n---\n` append
- 같은 날짜 중복 실행 시: **기존 entry는 건드리지 않고 끝에 append** (재실행 흔적 그대로 남김). 정합성보다 단순함 우선.

### 4.3 daily_moat.py 수정

저장 경로만 변경:
- 기존: `companies/{TICKER}/daily/{YYYY-MM-DD}.md` (덮어쓰기)
- 신규: `companies/{TICKER}/{YYYY}/{YYYY-MM}.md` (append, 4.2 포맷)

디렉토리 자동 생성(`os.makedirs(..., exist_ok=True)`). 텔레그램 전송/git commit 흐름은 그대로.

git add 경로도 변경: `companies/*/{YYYY}/{YYYY-MM}.md`

### 4.4 rollup.py 전면 재작성 — 독립 분석

**이전 daily 누적 방식 폐기.** quarterly와 annual은 각자 그 시점에서 새로 종합 분석한다.

#### quarterly_rollup(ticker, year, quarter)

입력:
- `companies/{TICKER}/moat.md` (현재 thesis)
- `companies/{TICKER}/profile.yaml`
- 그 분기에 해당하는 월간 파일들 (`{YYYY}/{YYYY-MM}.md` × 3개월) — **참고용 컨텍스트**로만 첨부 (압축 대상이 아님)

프롬프트 (`automation/prompts/quarterly.md` 신규):
- claude의 WebSearch로 그 분기의 **실적 발표, 가이던스, 주요 이벤트**를 새로 조사
- moat.md thesis와 비교하여 **분기 단위 thesis 점검**
- 월간 파일은 "내가 그 분기 동안 관찰한 것" 참고로만 사용 (재요약 X)

출력: `companies/{TICKER}/{YYYY}/quarterly-Q{N}.md`

#### annual_rollup(ticker, year)

입력:
- `companies/{TICKER}/moat.md`
- `companies/{TICKER}/profile.yaml`
- 그 해 4개 분기 파일 (`{YYYY}/quarterly-Q{1..4}.md`) — **참고용**

프롬프트 (`automation/prompts/annual.md` 신규):
- WebSearch로 1년 단위 **moat 변화, 산업 구조 변화, 장기 thesis 검증**
- 4축(pricing power / switching cost / network effect / cost advantage) 연간 회고
- 분기 파일은 참고만, 재요약 X

출력: `companies/{TICKER}/{YYYY}/annual.md`

#### 공통

- 두 함수 모두 입력 파일 없어도 실행 (WebSearch + moat.md만으로도 분석 가능). 단 월간/분기 파일이 있으면 컨텍스트로 첨부.
- 텔레그램 전송, CLI(`python rollup.py quarterly [TICKER]` 등) 인터페이스는 유지.

### 4.5 프롬프트 파일 분리

기존 `rollup.py` 내 하드코딩된 `QUARTERLY_PROMPT` / `ANNUAL_PROMPT` 제거. 다음 두 파일 신규 생성:

- `automation/prompts/quarterly.md` — 분기 독립 분석 템플릿 (4.4의 quarterly 명세대로)
- `automation/prompts/annual.md` — 연간 독립 회고 템플릿 (4.4의 annual 명세대로)

`daily.md`와 동일하게 `{TICKER}`, `{MOAT_CONTENT}`, `{YEAR}`, `{QUARTER}` 등 placeholder 치환 방식.

세 프롬프트 모두 A.2와 동일한 "절대 금지" 블록(트레일링 Sources/References/출처 부착 금지) 포함.

### 4.6 CLAUDE.md 업데이트

CLAUDE.md의 "디렉토리 구조" 섹션과 "자동화 흐름" 섹션을 4.1 / 4.4의 새 구조로 갱신.
추가로 자동화 흐름 섹션의 "매일 07:00 KST (cron)" 표기를 **LaunchAgent**로 정정 (실제로는 `~/Library/LaunchAgents/com.moat-journal.*.plist` 트리거 + wrapper에서 Keychain OAuth 토큰을 `CLAUDE_CODE_OAUTH_TOKEN`으로 주입). `automation/cron/` 디렉토리 이름은 유지하지만 실체는 launchd임을 명기.

### 4.7 기존 데이터 처리

옛 구조에 남은 잔여물 정리:
- `companies/*/daily/` 디렉토리의 5월 개별 파일들 (`2026-05-07.md`, `2026-05-08.md` 등) — 새 구조의 `{YYYY}/{YYYY-MM}.md`로 **수동 병합 후 daily/ 디렉토리 제거**.
  - 4월분(`2026/2026-04.md`)은 이미 새 구조로 존재하므로 그대로 둠.
- `companies/*/quarterly/`, `companies/*/annual/` 디렉토리도 비어있거나 옛 구조라면 제거.
- git rm으로 추적 해제 + 디렉토리 삭제.
