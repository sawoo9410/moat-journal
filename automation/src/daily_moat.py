import os
import re
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


def today_str(tz_name: str) -> str:
    return datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")


def render_prompt(template: str, ticker: str, moat_content: str) -> str:
    return template.replace("{TICKER}", ticker).replace("{MOAT_CONTENT}", moat_content)


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


SECTION_RE = re.compile(r"###\s+(.+?)\n(.*?)(?=\n###\s|\Z)", re.DOTALL)


def parse_output(text: str) -> dict:
    sections: dict[str, str] = {}
    for m in SECTION_RE.finditer(text):
        sections[m.group(1).strip()] = m.group(2).strip()
    return {
        "moat_status": sections.get("Moat 상태", ""),
        "bullish": sections.get("호재", ""),
        "bearish": sections.get("악재", ""),
        "valuation": sections.get("Valuation", ""),
        "comment": sections.get("한줄평", ""),
        "raw": text,
    }


def _normalize_lines(block: str) -> list[str]:
    out: list[str] = []
    for line in block.splitlines():
        s = line.strip().lstrip("•-*").strip()
        if s:
            out.append(s)
    return out


def is_empty_or_none(block: str) -> bool:
    lines = _normalize_lines(block)
    if not lines:
        return True
    return all(l == "없음" for l in lines)


def is_stable(parsed: dict) -> bool:
    return is_empty_or_none(parsed["bullish"]) and is_empty_or_none(parsed["bearish"])


def save_daily(ticker: str, date: str, raw: str) -> Path:
    daily_dir = ROOT / "companies" / ticker / "daily"
    os.makedirs(daily_dir, exist_ok=True)
    out = daily_dir / f"{date}.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(raw if raw.endswith("\n") else raw + "\n")
    return out


def build_summary(date: str, results: list[dict]) -> str:
    lines = [f"Moat Daily — {date}", ""]
    flagged = [r for r in results if r.get("flag")]
    stable = [r for r in results if not r.get("flag") and not r.get("error")]
    errored = [r for r in results if r.get("error")]

    for r in flagged:
        comment = r["parsed"]["comment"].strip() or "(한줄평 없음)"
        lines.append(f"[!] {r['ticker']} — {comment}")

    if stable:
        lines.append("")
        lines.append(f"안정: {', '.join(r['ticker'] for r in stable)}")

    if errored:
        lines.append("")
        lines.append(f"⚠️ 분석 실패: {', '.join(r['ticker'] for r in errored)}")

    return "\n".join(lines).strip() + "\n"


def build_detail(date: str, ticker: str, parsed: dict) -> str:
    bar = "━" * 16
    lines = [
        bar,
        f"  {ticker} — {date}",
        f"  Moat: {parsed['moat_status'] or '(미상)'}",
        bar,
        "",
    ]

    bull_items = _normalize_lines(parsed["bullish"])
    bull_items = [b for b in bull_items if b != "없음"]
    if bull_items:
        lines.append("🟢 호재")
        lines.extend(f"• {b}" for b in bull_items)
        lines.append("")

    bear_items = _normalize_lines(parsed["bearish"])
    bear_items = [b for b in bear_items if b != "없음"]
    if bear_items:
        lines.append("🔴 악재")
        lines.extend(f"• {b}" for b in bear_items)
        lines.append("")

    val = parsed["valuation"].strip()
    if val:
        lines.append(f"💰 {val}")
        lines.append("")

    comment = parsed["comment"].strip()
    if comment:
        lines.append(f"💬 {comment}")

    return "\n".join(lines).strip() + "\n"


def git_commit(date: str, paths: list[Path]) -> None:
    if not paths:
        return
    rel = [str(p.relative_to(ROOT)) for p in paths]
    try:
        subprocess.run(["git", "add", *rel], cwd=str(ROOT), check=True)
        status = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        if not status.stdout.strip():
            print("[daily_moat] no staged changes, skip commit", file=sys.stderr)
            return
        msg = f"daily moat: {date} 자동 분석 기록"
        subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT), check=True)
    except subprocess.CalledProcessError as e:
        print(f"[daily_moat] git commit 실패: {e}", file=sys.stderr)


def main() -> int:
    cfg = load_yaml_config()
    tickers: list[str] = cfg["tickers"]
    tz = cfg.get("schedule", {}).get("timezone", "Asia/Seoul")
    date = today_str(tz)

    prompt_path = ROOT / cfg["paths"]["prompts_dir"] / "daily.md"
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    results = []
    saved_paths: list[Path] = []

    for ticker in tickers:
        moat_path = ROOT / cfg["paths"]["companies_dir"] / ticker / "moat.md"
        if not moat_path.exists():
            print(f"[daily_moat] {ticker}: moat.md 없음, skip", file=sys.stderr)
            results.append({"ticker": ticker, "error": "moat.md 없음"})
            continue

        with open(moat_path, "r", encoding="utf-8") as f:
            moat_content = f.read()

        prompt = render_prompt(template, ticker, moat_content)

        try:
            raw = run_claude(prompt)
        except Exception as e:
            print(f"[daily_moat] {ticker}: claude 실행 실패: {e}", file=sys.stderr)
            results.append({"ticker": ticker, "error": str(e)})
            continue

        path = save_daily(ticker, date, raw)
        saved_paths.append(path)

        parsed = parse_output(raw)
        flag = not is_stable(parsed)
        results.append({"ticker": ticker, "parsed": parsed, "flag": flag})

    summary = build_summary(date, results)
    telegram_bot.send_message(summary)

    for r in results:
        if r.get("flag"):
            telegram_bot.send_message(build_detail(date, r["ticker"], r["parsed"]))

    git_commit(date, saved_paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
