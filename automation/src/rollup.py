import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import telegram_bot


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "automation" / "config.yaml"


def load_yaml_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def now_in_tz(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))


def quarter_of(month: int) -> int:
    return (month - 1) // 3 + 1


def quarter_months(quarter: int) -> tuple[int, int]:
    start = (quarter - 1) * 3 + 1
    return start, start + 2


def run_claude(prompt: str) -> str:
    proc = subprocess.run(
        ["claude", "--print", "-p", prompt],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude --print 실패 (rc={proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


def collect_daily_files(ticker: str, year: int, quarter: int) -> list[Path]:
    daily_dir = ROOT / "companies" / ticker / "daily"
    if not daily_dir.exists():
        return []
    m_start, m_end = quarter_months(quarter)
    files = []
    for f in sorted(daily_dir.glob("*.md")):
        try:
            d = datetime.strptime(f.stem, "%Y-%m-%d").date()
        except ValueError:
            continue
        if d.year == year and m_start <= d.month <= m_end:
            files.append(f)
    return files


def collect_quarterly_files(ticker: str, year: int) -> list[Path]:
    qdir = ROOT / "companies" / ticker / "quarterly"
    if not qdir.exists():
        return []
    return sorted(qdir.glob(f"{year}-Q*.md"))


QUARTERLY_PROMPT = """다음은 {ticker} 종목의 {year}년 Q{quarter} 분기 동안의 일일 moat 분석 기록이다.

================================
{joined}
================================

지시사항: 위 일일 기록을 종합하여 분기 요약을 작성하라. 버핏식 4축(pricing power, switching cost, network effect, cost advantage) 관점에서 변화를 평가하라.

출력 형식 (정확히 따를 것):

### 분기 요약
(이 분기 moat thesis 대비 변화 1~2 문단)

### Moat 변화
• (4축 중 변동 있는 축과 방향)

### 주요 이벤트
• (이 분기 가장 중요한 호재/악재 3~5개)

### Valuation 변화
(분기 초 vs 분기 말, 핵심 지표 추이)

### 다음 분기 관전 포인트
• (지켜봐야 할 주요 변수 2~3개)

### 한줄 요약
(분기를 한 문장으로)
"""


ANNUAL_PROMPT = """다음은 {ticker} 종목의 {year}년 4개 분기 요약이다.

================================
{joined}
================================

지시사항: 위 4개 분기 요약을 종합하여 연간 moat 회고를 작성하라.

출력 형식 (정확히 따를 것):

### 연간 회고
(올해 moat thesis가 어떻게 변했는가 2~3 문단)

### Moat 4축 변화
• Pricing power:
• Switching cost:
• Network effect:
• Cost advantage:

### 올해 핵심 이벤트
• (Top 5)

### Valuation 추이
(연초 vs 연말 핵심 지표)

### 내년 관전 포인트
• (Top 3)

### 한줄 회고
(한 해를 한 문장으로)
"""


def quarterly_rollup(ticker: str, year: int, quarter: int) -> Path | None:
    files = collect_daily_files(ticker, year, quarter)
    if not files:
        print(f"[rollup] {ticker} {year} Q{quarter}: daily 기록 없음", file=sys.stderr)
        return None

    joined_parts = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            joined_parts.append(f"--- {f.stem} ---\n{fh.read()}")
    joined = "\n\n".join(joined_parts)

    prompt = QUARTERLY_PROMPT.format(ticker=ticker, year=year, quarter=quarter, joined=joined)
    raw = run_claude(prompt)

    qdir = ROOT / "companies" / ticker / "quarterly"
    os.makedirs(qdir, exist_ok=True)
    out = qdir / f"{year}-Q{quarter}.md"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(raw if raw.endswith("\n") else raw + "\n")

    msg = f"📊 {ticker} {year} Q{quarter} 분기 요약\n\n{raw.strip()}"
    telegram_bot.send_message(msg)
    return out


def annual_rollup(ticker: str, year: int) -> Path | None:
    files = collect_quarterly_files(ticker, year)
    if not files:
        print(f"[rollup] {ticker} {year}: 분기 요약 없음", file=sys.stderr)
        return None

    joined_parts = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            joined_parts.append(f"--- {f.stem} ---\n{fh.read()}")
    joined = "\n\n".join(joined_parts)

    prompt = ANNUAL_PROMPT.format(ticker=ticker, year=year, joined=joined)
    raw = run_claude(prompt)

    adir = ROOT / "companies" / ticker / "annual"
    os.makedirs(adir, exist_ok=True)
    out = adir / f"{year}.md"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(raw if raw.endswith("\n") else raw + "\n")

    msg = f"📅 {ticker} {year} 연간 회고\n\n{raw.strip()}"
    telegram_bot.send_message(msg)
    return out


def usage() -> None:
    print(
        "usage:\n"
        "  python rollup.py quarterly [TICKER]\n"
        "  python rollup.py annual [TICKER]\n",
        file=sys.stderr,
    )


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in ("quarterly", "annual"):
        usage()
        return 2

    cfg = load_yaml_config()
    tz = cfg.get("schedule", {}).get("timezone", "Asia/Seoul")
    now = now_in_tz(tz)

    mode = argv[1]
    target_ticker = argv[2] if len(argv) >= 3 else None
    tickers = [target_ticker] if target_ticker else cfg["tickers"]

    if mode == "quarterly":
        # 현재 시점에서 "직전 분기"를 요약 (분기 첫날 cron 실행 가정)
        cur_q = quarter_of(now.month)
        if cur_q == 1:
            year, quarter = now.year - 1, 4
        else:
            year, quarter = now.year, cur_q - 1
        for t in tickers:
            try:
                quarterly_rollup(t, year, quarter)
            except Exception as e:
                print(f"[rollup] {t} quarterly 실패: {e}", file=sys.stderr)
    else:
        # 연초 cron 실행 가정 → 직전 연도 회고
        year = now.year - 1
        for t in tickers:
            try:
                annual_rollup(t, year)
            except Exception as e:
                print(f"[rollup] {t} annual 실패: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
