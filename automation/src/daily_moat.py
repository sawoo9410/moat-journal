import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fundamentals
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
    try:
        proc = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env={**os.environ},
            timeout=300,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"claude --print 타임아웃 (300s): {e}")

    if proc.returncode != 0:
        raise RuntimeError(
            f"claude --print 실패 (rc={proc.returncode})\n"
            f"  HOME={os.environ.get('HOME')!r} cwd={ROOT}\n"
            f"  stderr: {proc.stderr.strip() or '(empty)'}\n"
            f"  stdout(first 500): {proc.stdout.strip()[:500] or '(empty)'}"
        )
    return proc.stdout


SECTION_RE = re.compile(r"###\s+(.+?)\n(.*?)(?=\n###\s|\Z)", re.DOTALL)


def parse_output(text: str) -> dict:
    m = re.search(r"\n+(Sources?|References?|출처|참고문헌)\s*:", text, flags=re.IGNORECASE)
    if m:
        text = text[: m.start()].rstrip() + "\n"
    sections: dict[str, str] = {}
    for m in SECTION_RE.finditer(text):
        sections[m.group(1).strip()] = m.group(2).strip()
    return {
        "moat_status": sections.get("Moat 상태", ""),
        "bullish": sections.get("호재", ""),
        "bearish": sections.get("악재", ""),
        "valuation": sections.get("Valuation", ""),
        "comment": sections.get("종합평가", "") or sections.get("한줄평", ""),
        "raw": text,
    }


def _normalize_lines(block: str) -> list[str]:
    out: list[str] = []
    for line in block.splitlines():
        s = line.strip().lstrip("•-*").strip()
        if s:
            out.append(s)
    return out


def _top_n(items: list[str], n: int = 3) -> list[str]:
    """LLM이 n개 이상 출력해도 강제 컷. 첫 n개만 보존(우선순위 순서 가정)."""
    return items[:n]


def is_empty_or_none(block: str) -> bool:
    lines = _normalize_lines(block)
    if not lines:
        return True
    return all(l == "없음" for l in lines)


def is_stable(parsed: dict) -> bool:
    return is_empty_or_none(parsed["bullish"]) and is_empty_or_none(parsed["bearish"])


def append_monthly(ticker: str, date: str, raw: str) -> Path:
    """일일 분석을 월간 누적 파일(companies/{TICKER}/{YYYY}/{YYYY-MM}.md)에 append."""
    year_str, month_str, _ = date.split("-")
    year = int(year_str)
    month = int(month_str)

    monthly_dir = ROOT / "companies" / ticker / year_str
    os.makedirs(monthly_dir, exist_ok=True)
    out = monthly_dir / f"{year_str}-{month_str}.md"

    body = raw.rstrip("\n")
    entry = f"## {date}\n\n{body}\n\n---\n"

    if out.exists():
        with open(out, "r", encoding="utf-8") as f:
            existing = f.read()
        if not existing.endswith("\n"):
            existing += "\n"
        content = existing + "\n" + entry
    else:
        header = f"# {ticker} — {year}년 {month}월\n\n"
        content = header + entry

    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    return out


# ---------------------------------------------------------------------------
# 메시지 빌더
# ---------------------------------------------------------------------------

def _build_ticker_block(ticker: str, parsed: dict, max_bullets: int = 3) -> str:
    """종목 하나의 개조식 블록 생성. build_summary / build_detail 공용."""
    lines = [f"━ {ticker} ━"]

    bull_items = [b for b in _normalize_lines(parsed["bullish"]) if b != "없음"]
    bull_items = _top_n(bull_items, max_bullets)
    if bull_items:
        lines.append("호재")
        lines.extend(f"• {b}" for b in bull_items)

    bear_items = [b for b in _normalize_lines(parsed["bearish"]) if b != "없음"]
    bear_items = _top_n(bear_items, max_bullets)
    if bear_items:
        lines.append("악재")
        lines.extend(f"• {b}" for b in bear_items)

    comment = parsed["comment"].strip()
    if comment:
        lines.append(f"종합평가: {comment}")

    return "\n".join(lines)


def build_summary_chunks(date: str, results: list[dict], chunk_size: int = 5) -> list[str]:
    """Moat Daily 요약 메시지. [!] 종목을 chunk_size개씩 묶어 N개 메시지 반환."""
    flagged = [r for r in results if r.get("flag")]
    stable = [r for r in results if not r.get("flag") and not r.get("error")]
    errored = [r for r in results if r.get("error")]

    # [!] 0개 — 전 종목 안정
    if not flagged:
        lines = [f"Moat Daily — {date}", ""]
        if stable:
            lines.append(f"안정: {', '.join(r['ticker'] for r in stable)}")
        if errored:
            lines.append(f"⚠️ 분석 실패: {', '.join(r['ticker'] for r in errored)}")
        return ["\n".join(lines).strip() + "\n"]

    # 청크 분할
    chunks: list[list[dict]] = []
    for i in range(0, len(flagged), chunk_size):
        chunks.append(flagged[i : i + chunk_size])

    messages = []
    total = len(chunks)
    for idx, chunk in enumerate(chunks, 1):
        lines = [f"Moat Daily — {date} ({idx}/{total})", ""]
        for r in chunk:
            lines.append(_build_ticker_block(r["ticker"], r["parsed"], max_bullets=3))
            lines.append("")

        # 마지막 청크에만 안정/에러 라인
        if idx == total:
            if stable:
                lines.append(f"안정: {', '.join(r['ticker'] for r in stable)}")
            if errored:
                lines.append(f"⚠️ 분석 실패: {', '.join(r['ticker'] for r in errored)}")

        messages.append("\n".join(lines).strip() + "\n")

    return messages


def build_detail(date: str, ticker: str, parsed: dict) -> str:
    """주간 detail 메시지 (일요일). 종목당 1메시지."""
    lines = [
        f"━━ {ticker} — {date} ━━",
        f"Moat: {parsed['moat_status'] or '(미상)'}",
        "",
    ]

    bull_items = [b for b in _normalize_lines(parsed["bullish"]) if b != "없음"]
    bull_items = _top_n(bull_items, 5)
    if bull_items:
        lines.append("호재")
        lines.extend(f"• {b}" for b in bull_items)
        lines.append("")

    bear_items = [b for b in _normalize_lines(parsed["bearish"]) if b != "없음"]
    bear_items = _top_n(bear_items, 5)
    if bear_items:
        lines.append("악재")
        lines.extend(f"• {b}" for b in bear_items)
        lines.append("")

    val = parsed["valuation"].strip()
    if val:
        val_one_line = " / ".join(_normalize_lines(val)[:3])
        lines.append(f"💰 {val_one_line}")
        lines.append("")

    comment = parsed["comment"].strip()
    if comment:
        lines.append(f"종합평가: {comment}")

    return "\n".join(lines).strip() + "\n"


# ---------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    cfg = load_yaml_config()
    tickers: list[str] = cfg["tickers"]
    tz = cfg.get("schedule", {}).get("timezone", "Asia/Seoul")
    detail_weekday = cfg.get("schedule", {}).get("detail_weekday", 6)  # 6=일요일
    chunk_size = cfg.get("schedule", {}).get("summary_chunk_size", 5)
    date = today_str(tz)

    now = datetime.now(ZoneInfo(tz))
    is_weekly_detail_day = now.weekday() == detail_weekday

    # ── 1단계: 펀더멘탈 표 (daily 분석보다 먼저 도착) ──
    av_key = os.environ.get("ALPHAVANTAGE_API_KEY", "")
    if av_key:
        try:
            fund_rows = fundamentals.fetch_all(tickers, av_key)
            fund_table = fundamentals.build_fundamentals_table(fund_rows)
            telegram_bot.send_message(fund_table)
        except Exception as e:
            telegram_bot.send_message(f"⚠️ 펀더멘탈 조회 실패 ({e})")
            print(f"[daily_moat] fundamentals 실패: {e}", file=sys.stderr)
    else:
        print("[daily_moat] ALPHAVANTAGE_API_KEY 미설정, 펀더멘탈 스킵", file=sys.stderr)

    # ── 2단계: 종목별 claude --print 분석 ──
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

        path = append_monthly(ticker, date, raw)
        if path not in saved_paths:
            saved_paths.append(path)

        parsed = parse_output(raw)
        flag = not is_stable(parsed)
        results.append({"ticker": ticker, "parsed": parsed, "flag": flag})

    # 매일: Moat Daily 청크 메시지
    for msg in build_summary_chunks(date, results, chunk_size):
        telegram_bot.send_message(msg)

    # 일요일만: 전 종목 detail
    if is_weekly_detail_day:
        for r in results:
            if r.get("parsed"):
                telegram_bot.send_message(build_detail(date, r["ticker"], r["parsed"]))

    git_commit(date, saved_paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
