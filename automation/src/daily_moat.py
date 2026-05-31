import csv
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


def render_prompt(
    template: str,
    ticker: str,
    moat_content: str,
    fundamentals_str: str = "펀더멘털 N/A",
    lane: str = "compounder",
) -> str:
    return (
        template
        .replace("{TICKER}", ticker)
        .replace("{MOAT_CONTENT}", moat_content)
        .replace("{FUNDAMENTALS}", fundamentals_str)
        .replace("{LANE}", lane)
    )


def load_lane(ticker: str) -> str:
    """profile.yaml에서 레인 결정(작업 I.4).

    우선순위: 명시적 `lane` 필드 > tracking_purpose에 dividend 포함 > dividend 블록 존재
    → dividend, 그 외 compounder.
    """
    prof_path = ROOT / "companies" / ticker / "profile.yaml"
    if not prof_path.exists():
        return "compounder"
    try:
        prof = yaml.safe_load(prof_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return "compounder"
    lane = prof.get("lane")
    if lane in ("compounder", "dividend"):
        return lane
    tp = prof.get("tracking_purpose") or []
    if isinstance(tp, list) and any("dividend" in str(x) for x in tp):
        return "dividend"
    if prof.get("dividend"):
        return "dividend"
    return "compounder"


def format_fundamentals_line(row) -> str:
    """프롬프트 주입용 1줄 펀더멘털 실값. None/error면 'N/A' 처리."""
    if not row or row.get("error"):
        return "펀더멘털 N/A"

    def fmt(v, suffix=""):
        return f"{v}{suffix}" if v is not None else "N/A"

    return (
        f"PER {fmt(row.get('per'))} / ROE {fmt(row.get('roe'), '%')} / "
        f"D/E {fmt(row.get('debt_equity'))} / Margin {fmt(row.get('profit_margin'), '%')} / "
        f"52주 고점대비 {fmt(row.get('drop_from_high_pct'), '%')} / 배당 {fmt(row.get('dividend_yield'), '%')}"
    )


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


def _extract_field(block: str, key: str) -> str:
    """`- key: value` 또는 `key value` 형태에서 value 추출."""
    for line in block.splitlines():
        s = line.strip().lstrip("•-*").strip()
        if s.startswith(key):
            return s[len(key):].lstrip(":： ").strip()
    return ""


def parse_output(text: str) -> dict:
    m = re.search(r"\n+(Sources?|References?|출처|참고문헌)\s*:", text, flags=re.IGNORECASE)
    if m:
        text = text[: m.start()].rstrip() + "\n"
    sections: dict[str, str] = {}
    for m in SECTION_RE.finditer(text):
        sections[m.group(1).strip()] = m.group(2).strip()
    attract = sections.get("매수 매력도", "")
    return {
        "moat_status": sections.get("Moat 상태", ""),
        "bullish": sections.get("호재", ""),
        "bearish": sections.get("악재", ""),
        "valuation": sections.get("Valuation", ""),
        "comment": sections.get("종합평가", "") or sections.get("한줄평", ""),
        # 매수 매력도(작업 I) — LLM 정성 판정 2축 + 레인 + 근거
        "moat_q": _extract_field(attract, "Moat질"),
        "valuation_bucket": _extract_field(attract, "밸류"),
        "rec_lane": _extract_field(attract, "레인"),
        "rec_rationale": _extract_field(attract, "근거"),
        "raw": text,
    }


# ---------------------------------------------------------------------------
# 매수 매력도 등급 (작업 I) — Python authoritative 매트릭스 + 자본보존 가드
# ---------------------------------------------------------------------------

GRADE_MATRIX = {
    ("견고", "저평가"): "신규매수 적기",
    ("견고", "적정"): "매수 고려",
    ("견고", "고평가"): "관망",
    ("좁음", "저평가"): "매수 고려",
    ("좁음", "적정"): "관망",
    ("좁음", "고평가"): "관망",
    ("약화", "저평가"): "관망",
    ("약화", "적정"): "회피",
    ("약화", "고평가"): "회피",
    ("훼손", "저평가"): "회피",
    ("훼손", "적정"): "회피",
    ("훼손", "고평가"): "회피",
}


def _norm_moat_q(s: str):
    s = s or ""
    for k in ("견고", "좁음", "약화", "훼손"):
        if k in s:
            return k
    return None


def _norm_valuation(s: str):
    s = s or ""
    for k in ("저평가", "적정", "고평가"):
        if k in s:
            return k
    return None


def compute_grade(moat_q: str, valuation_bucket: str) -> str:
    """I.3 매트릭스로 최종 등급을 결정론적으로 산정. 알 수 없으면 안전하게 '관망'.

    자본보존 가드: Moat질이 약화/훼손이면 신규매수 적기·매수 고려가 절대 안 나오도록 재강제.
    """
    mq = _norm_moat_q(moat_q)
    vb = _norm_valuation(valuation_bucket)
    if mq is None or vb is None:
        return "관망"
    grade = GRADE_MATRIX.get((mq, vb), "관망")
    if mq in ("약화", "훼손") and grade in ("신규매수 적기", "매수 고려"):
        grade = "회피" if mq == "훼손" else "관망"
    return grade


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


def append_monthly(ticker: str, date: str, raw: str, grade: str = None) -> Path:
    """일일 분석을 월간 누적 파일(companies/{TICKER}/{YYYY}/{YYYY-MM}.md)에 append.

    grade(작업 I 최종 등급)가 있으면 date 헤더에 부가: `## 2026-06-01 · 매수 고려`.
    """
    year_str, month_str, _ = date.split("-")
    year = int(year_str)
    month = int(month_str)

    monthly_dir = ROOT / "companies" / ticker / year_str
    os.makedirs(monthly_dir, exist_ok=True)
    out = monthly_dir / f"{year_str}-{month_str}.md"

    body = raw.rstrip("\n")
    date_header = f"## {date}" + (f" · {grade}" if grade else "")
    entry = f"{date_header}\n\n{body}\n\n---\n"

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
# 펀더멘털 시계열 CSV (작업 J)
# ---------------------------------------------------------------------------

FUND_CSV_HEADER = [
    "date", "per", "roe", "debt_equity", "profit_margin",
    "drop_from_high_pct", "dividend_yield", "source",
]


def append_fundamentals_csv(ticker: str, date: str, row: dict):
    """펀더멘털 1행을 companies/{ticker}/fundamentals.csv에 멱등 append.

    - 파일 없으면 헤더 먼저 기록.
    - 같은 date 행이 이미 있으면 덮어씀(수동 재실행 멱등).
    - row.get("error") 있으면 기록 안 함 → None 반환(빈 행 오염 방지).
    - 단위는 F.2 정규화 그대로(ROE/Margin/배당=%, D/E=비율). None 필드는 빈 칸.
    - source = 그 행을 채운 소스(예 'yfinance' / 'yfinance+stooq').
    반환: 기록한 CSV 경로(Path) 또는 None.
    """
    if row.get("error"):
        return None

    out = ROOT / "companies" / ticker / "fundamentals.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    def cell(key: str):
        v = row.get(key)
        return "" if v is None else v

    new_row = {
        "date": date,
        "per": cell("per"),
        "roe": cell("roe"),
        "debt_equity": cell("debt_equity"),
        "profit_margin": cell("profit_margin"),
        "drop_from_high_pct": cell("drop_from_high_pct"),
        "dividend_yield": cell("dividend_yield"),
        "source": "+".join(row.get("sources", [])),
    }

    # 기존 행 로드 → date 키로 멱등 갱신(순서 보존)
    rows_by_date: dict[str, dict] = {}
    order: list[str] = []
    if out.exists():
        with open(out, "r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                d = r.get("date")
                if not d:
                    continue
                if d not in rows_by_date:
                    order.append(d)
                rows_by_date[d] = r
    if date not in rows_by_date:
        order.append(date)
    rows_by_date[date] = new_row

    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FUND_CSV_HEADER)
        writer.writeheader()
        for d in order:
            writer.writerow({k: rows_by_date[d].get(k, "") for k in FUND_CSV_HEADER})
    return out


# ---------------------------------------------------------------------------
# 메시지 빌더
# ---------------------------------------------------------------------------

def _stable_label(r: dict) -> str:
    """안정 종목 라벨에 등급 부가: 'KO·관망'."""
    g = r.get("grade")
    return f"{r['ticker']}·{g}" if g else r["ticker"]


def build_summary_chunks(date: str, results: list[dict], chunk_size: int = 5) -> list[str]:
    """Moat Daily 요약 메시지. 종합평가만 송출, 호재/악재/Valuation은 월간 .md에만 보존.

    [!] 종목 헤더와 안정 종목 라인에 매수 매력도 등급(작업 I)을 가시화.
    """
    flagged = [r for r in results if r.get("flag")]
    stable = [r for r in results if not r.get("flag") and not r.get("error")]
    errored = [r for r in results if r.get("error")]

    # [!] 0개 — 전 종목 안정
    if not flagged:
        lines = [f"Moat Daily — {date}", ""]
        if stable:
            lines.append(f"안정: {', '.join(_stable_label(r) for r in stable)}")
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
            comment = r["parsed"]["comment"].strip()
            if not comment:
                continue
            grade = r.get("grade")
            header = f"━ {r['ticker']}" + (f" · {grade}" if grade else "") + " ━"
            lines.append(header)
            lines.append(comment)
            lines.append("")

        # 마지막 청크에만 안정/에러 라인
        if idx == total:
            if stable:
                lines.append(f"안정: {', '.join(_stable_label(r) for r in stable)}")
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

    saved_paths: list[Path] = []
    fund_rows: list[dict] = []

    # ── 1단계: 펀더멘탈 표 (daily 분석보다 먼저 도착) ──
    # yfinance 주 소스 + 무료 폴백 체인 — API 키 불필요, 항상 실행.
    try:
        fund_rows = fundamentals.fetch_all(tickers)

        # 시계열 CSV 적재(작업 J) — 텔레그램 전송과 독립(append 실패가 카드 전송을 막지 않음).
        for r in fund_rows:
            try:
                csv_path = append_fundamentals_csv(r["ticker"], date, r)
                if csv_path and csv_path not in saved_paths:
                    saved_paths.append(csv_path)
            except Exception as e:
                print(f"[daily_moat] fundamentals csv append 실패 {r['ticker']}: {e}", file=sys.stderr)

        fund_table = fundamentals.build_fundamentals_table(fund_rows)
        telegram_bot.send_message(fund_table)

        # 주 소스(yfinance) 외 폴백 소스가 실제로 필드를 채웠으면 알림.
        fallback = {
            r["ticker"]: [s for s in r.get("sources", []) if s != "yfinance"]
            for r in fund_rows
        }
        fallback = {t: srcs for t, srcs in fallback.items() if srcs}
        if fallback:
            notice = "ℹ️ 펀더멘털 폴백 소스 사용:\n" + "\n".join(
                f"  {t}: {', '.join(srcs)}" for t, srcs in fallback.items()
            )
            telegram_bot.send_message(notice)
    except Exception as e:
        telegram_bot.send_message(f"⚠️ 펀더멘탈 조회 실패 ({e})")
        print(f"[daily_moat] fundamentals 실패: {e}", file=sys.stderr)

    # 펀더멘털 실값 — 종목별 조회용 (프롬프트 주입, 작업 I)
    fund_by_ticker = {r["ticker"]: r for r in fund_rows}

    # ── 2단계: 종목별 claude --print 분석 ──
    prompt_path = ROOT / cfg["paths"]["prompts_dir"] / "daily.md"
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    results = []

    for ticker in tickers:
        moat_path = ROOT / cfg["paths"]["companies_dir"] / ticker / "moat.md"
        if not moat_path.exists():
            print(f"[daily_moat] {ticker}: moat.md 없음, skip", file=sys.stderr)
            results.append({"ticker": ticker, "error": "moat.md 없음"})
            continue

        with open(moat_path, "r", encoding="utf-8") as f:
            moat_content = f.read()

        fundamentals_str = format_fundamentals_line(fund_by_ticker.get(ticker))
        lane = load_lane(ticker)
        prompt = render_prompt(template, ticker, moat_content, fundamentals_str, lane)

        try:
            raw = run_claude(prompt)
        except Exception as e:
            print(f"[daily_moat] {ticker}: claude 실행 실패: {e}", file=sys.stderr)
            results.append({"ticker": ticker, "error": str(e)})
            continue

        parsed = parse_output(raw)
        # 최종 등급은 Python 매트릭스가 authoritative (작업 I.3)
        grade = compute_grade(parsed["moat_q"], parsed["valuation_bucket"])

        # 월간 .md date 헤더에 보정 후 최종 등급 부가
        path = append_monthly(ticker, date, raw, grade)
        if path not in saved_paths:
            saved_paths.append(path)

        flag = not is_stable(parsed)
        results.append({
            "ticker": ticker,
            "parsed": parsed,
            "flag": flag,
            "grade": grade,
            "rec_rationale": parsed["rec_rationale"],
        })

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
