# moat-journal

매일 종목별 moat(경쟁우위)을 자동 분석하고, 텔레그램으로 전달하고, git에 기록하는 시스템.

## 구조

```
companies/{TICKER}/
  moat.md               ← moat thesis
  {YYYY}/
    {YYYY-MM}.md         ← 일일 분석 월간 누적
    quarterly-Q{N}.md    ← 분기 독립 분석
    annual.md            ← 연간 독립 회고

automation/
  config.yaml            ← 추적 종목, 텔레그램 설정
  src/
    daily_moat.py         ← 매일 cron 실행
    telegram_bot.py       ← 텔레그램 전송
    rollup.py             ← 분기/연간 분석
  prompts/
    daily.md              ← 일일 분석 프롬프트
  cron/
    daily_moat.sh         ← cron wrapper
    rollup.sh             ← rollup wrapper
```

## 흐름

```
매일 07:00 KST (cron)
  → claude --print로 종목별 버핏식 moat 분석
  → 월간 파일에 누적 기록
  → 텔레그램 전송
  → git auto-commit
```

## 텔레그램

- 요약 메시지 1건 + 변동 종목별 상세 메시지
- 출처/뉴스 상세 없이 한줄평으로 호악재 종합
- 안정 종목은 이름만 나열

## 세팅

```bash
cp automation/.env.example .env
# .env에 MOAT_TELEGRAM_BOT_TOKEN, MOAT_TELEGRAM_CHAT_ID 입력
pip install -r requirements.txt
```

## 추적 종목

`automation/config.yaml`에서 관리. 현재: GOOGL, MCD, KO.
