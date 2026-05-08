"""분기/연간 독립 moat 분석.

todo.md 4.4: 이전 daily 누적 방식 폐기. quarterly와 annual은 각자 그 시점에서
새로 종합 분석한다. 월간/분기 파일은 "관찰 기록"의 참고일 뿐, 재요약 대상 아님.
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import telegram_bot


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "automation" / "config.yaml"
PROMPTS_DIR = ROOT / "automation" / "prompts"


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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def collect_monthly_for_quarter(ticker: str, year: int, quarter: int) -> str:
    """분기에 해당하는 월간 누적 파일들을 합쳐 컨텍스트 문자열로 반환.

    참고용. 없어도 빈 문자열 반환 (분석은 진행).
    """
    m_start, m_end = quarter_months(quarter)
    parts: list[str] = []
    for m in range(m_start, m_end + 1):
        path = ROOT / "companies" / ticker / str(year) / f"{year}-{m:02d}.md"
        if path.exists():
            parts.append(f"--- {year}-{m:02d}.md ---\n{read_text(path)}")
    return "\n\n".join(parts)


def collect_quarterly_for_year(ticker: str, year: int) -> str:
    """그 해 4개 분기 분석 파일을 합쳐 컨텍스트 문자열로 반환. 참고용."""
    parts: list[str] = []
    for q in range(1, 5):
        path = ROOT / "companies" / ticker / str(year) / f"quarterly-Q{q}.md"
        if path.exists():
            parts.append(f"--- quarterly-Q{q}.md ---\n{read_text(path)}")
    return "\n\n".join(parts)


def render_prompt(template: str, **kwargs: str) -> str:
    out = template
    for key, value in kwargs.items():
        out = out.replace("{" + key + "}", value)
    return out


def quarterly_rollup(ticker: str, year: int, quarter: int) -> Optional[Path]:
    template = read_text(PROMPTS_DIR / "quarterly.md")
    if not template:
        print("[rollup] prompts/quarterly.md 없음", file=sys.stderr)
        return None

    moat_content = read_text(ROOT / "companies" / ticker / "moat.md")
    profile_content = read_text(ROOT / "companies" / ticker / "profile.yaml")
    monthly_context = collect_monthly_for_quarter(ticker, year, quarter)

    prompt = render_prompt(
        template,
        TICKER=ticker,
        YEAR=str(year),
        QUARTER=str(quarter),
        MOAT_CONTENT=moat_content or "(thesis 없음)",
        PROFILE_CONTENT=profile_content or "(profile 없음)",
        MONTHLY_CONTEXT=monthly_context or "(월간 누적 없음 — WebSearch + thesis 만으로 분석)",
    )

    raw = run_claude(prompt)

    out_dir = ROOT / "companies" / ticker / str(year)
    os.makedirs(out_dir, exist_ok=True)
    out = out_dir / f"quarterly-Q{quarter}.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(raw if raw.endswith("\n") else raw + "\n")

    msg = f"📊 {ticker} {year} Q{quarter} 분기 분석\n\n{raw.strip()}"
    telegram_bot.send_message(msg)
    return out


def annual_rollup(ticker: str, year: int) -> Optional[Path]:
    template = read_text(PROMPTS_DIR / "annual.md")
    if not template:
        print("[rollup] prompts/annual.md 없음", file=sys.stderr)
        return None

    moat_content = read_text(ROOT / "companies" / ticker / "moat.md")
    profile_content = read_text(ROOT / "companies" / ticker / "profile.yaml")
    quarterly_context = collect_quarterly_for_year(ticker, year)

    prompt = render_prompt(
        template,
        TICKER=ticker,
        YEAR=str(year),
        MOAT_CONTENT=moat_content or "(thesis 없음)",
        PROFILE_CONTENT=profile_content or "(profile 없음)",
        QUARTERLY_CONTEXT=quarterly_context or "(분기 분석 없음 — WebSearch + thesis 만으로 분석)",
    )

    raw = run_claude(prompt)

    out_dir = ROOT / "companies" / ticker / str(year)
    os.makedirs(out_dir, exist_ok=True)
    out = out_dir / "annual.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(raw if raw.endswith("\n") else raw + "\n")

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
        # 분기 첫날 cron 실행 가정 → "직전 분기" 분석
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
