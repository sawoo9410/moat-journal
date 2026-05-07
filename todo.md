# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

남은 작업: **Phase 4 — 구조 개편 (월간 누적 + 독립 분석)**.
Phase 1~3(텔레그램 봇, 기본 daily/rollup 인프라, cron 등록)은 완료.

기존 구조(daily 파일/일 + daily→quarterly→annual 계단식 압축)를 폐기하고:
- **파일**: 일별 파일 폐지 → **월간 누적 파일** (`companies/{TICKER}/{YYYY}/{YYYY-MM}.md`)
- **분석**: 계단식 압축 폐지 → daily/quarterly/annual **각자 독립 분석** (각자 다른 목적, 다른 입력)

---

## 4.1 디렉토리 구조 변경

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

## 4.2 월간 누적 파일 포맷

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

## 4.3 daily_moat.py 수정

저장 경로만 변경:
- 기존: `companies/{TICKER}/daily/{YYYY-MM-DD}.md` (덮어쓰기)
- 신규: `companies/{TICKER}/{YYYY}/{YYYY-MM}.md` (append, 4.2 포맷)

디렉토리 자동 생성(`os.makedirs(..., exist_ok=True)`). 텔레그램 전송/git commit 흐름은 그대로.

git add 경로도 변경: `companies/*/{YYYY}/{YYYY-MM}.md`

## 4.4 rollup.py 전면 재작성 — 독립 분석

**이전 daily 누적 방식 폐기.** quarterly와 annual은 각자 그 시점에서 새로 종합 분석한다.

### quarterly_rollup(ticker, year, quarter)

입력:
- `companies/{TICKER}/moat.md` (현재 thesis)
- `companies/{TICKER}/profile.yaml`
- 그 분기에 해당하는 월간 파일들 (`{YYYY}/{YYYY-MM}.md` × 3개월) — **참고용 컨텍스트**로만 첨부 (압축 대상이 아님)

프롬프트 (`automation/prompts/quarterly.md` 신규):
- claude의 WebSearch로 그 분기의 **실적 발표, 가이던스, 주요 이벤트**를 새로 조사
- moat.md thesis와 비교하여 **분기 단위 thesis 점검**
- 월간 파일은 "내가 그 분기 동안 관찰한 것" 참고로만 사용 (재요약 X)

출력: `companies/{TICKER}/{YYYY}/quarterly-Q{N}.md`

### annual_rollup(ticker, year)

입력:
- `companies/{TICKER}/moat.md`
- `companies/{TICKER}/profile.yaml`
- 그 해 4개 분기 파일 (`{YYYY}/quarterly-Q{1..4}.md`) — **참고용**

프롬프트 (`automation/prompts/annual.md` 신규):
- WebSearch로 1년 단위 **moat 변화, 산업 구조 변화, 장기 thesis 검증**
- 4축(pricing power / switching cost / network effect / cost advantage) 연간 회고
- 분기 파일은 참고만, 재요약 X

출력: `companies/{TICKER}/{YYYY}/annual.md`

### 공통

- 두 함수 모두 입력 파일 없어도 실행 (WebSearch + moat.md만으로도 분석 가능). 단 월간/분기 파일이 있으면 컨텍스트로 첨부.
- 텔레그램 전송, CLI(`python rollup.py quarterly [TICKER]` 등) 인터페이스는 유지.

## 4.5 프롬프트 파일 분리

기존 `rollup.py` 내 하드코딩된 `QUARTERLY_PROMPT` / `ANNUAL_PROMPT` 제거. 다음 두 파일 신규 생성:

- `automation/prompts/quarterly.md` — 분기 독립 분석 템플릿 (4.4의 quarterly 명세대로)
- `automation/prompts/annual.md` — 연간 독립 회고 템플릿 (4.4의 annual 명세대로)

`daily.md`와 동일하게 `{TICKER}`, `{MOAT_CONTENT}`, `{YEAR}`, `{QUARTER}` 등 placeholder 치환 방식.

## 4.6 CLAUDE.md 업데이트

CLAUDE.md의 "디렉토리 구조" 섹션과 "자동화 흐름" 섹션을 4.1 / 4.4의 새 구조로 갱신.

## 4.7 기존 데이터 처리

옛 구조에 남은 잔여물 정리:
- `companies/*/daily/` 디렉토리의 5월 개별 파일들 (`2026-05-07.md`, `2026-05-08.md` 등) — 새 구조의 `{YYYY}/{YYYY-MM}.md`로 **수동 병합 후 daily/ 디렉토리 제거**.
  - 4월분(`2026/2026-04.md`)은 이미 새 구조로 존재하므로 그대로 둠.
- `companies/*/quarterly/`, `companies/*/annual/` 디렉토리도 비어있거나 옛 구조라면 제거.
- git rm으로 추적 해제 + 디렉토리 삭제.
