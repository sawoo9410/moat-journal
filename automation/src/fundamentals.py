"""펀더멘탈 데이터 조회 + 텔레그램 표 빌드.

AlphaVantage OVERVIEW endpoint 사용. Free tier: 25 req/day, 5 req/min.
"""
import os
import sys
import time

import requests


OVERVIEW_URL = "https://www.alphavantage.co/query"


def fetch_fundamentals(ticker: str, api_key: str) -> dict:
    """AlphaVantage OVERVIEW endpoint에서 펀더멘탈 데이터 조회.

    반환: {ticker, per, roe, debt_equity, profit_margin, drop_from_high_pct, dividend_yield}
    실패 시 {ticker, error: str} 반환.
    """
    try:
        resp = requests.get(
            OVERVIEW_URL,
            params={
                "function": "OVERVIEW",
                "symbol": ticker,
                "apikey": api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if "Symbol" not in data:
            return {"ticker": ticker, "error": data.get("Note", data.get("Information", "no data"))}

        def safe_float(key: str):
            v = data.get(key, "None")
            if v in ("None", "-", "", None):
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        per = safe_float("TrailingPE")
        roe = safe_float("ReturnOnEquityTTM")
        de = safe_float("DebtToEquityRatio") if "DebtToEquityRatio" not in data else None
        # AV 필드명 변형 대응
        if de is None:
            # AV doesn't have a clean D/E; approximate from balance sheet if needed
            de_raw = data.get("DebtToEquityRatio") or data.get("DebtEquityRatio")
            if de_raw and de_raw not in ("None", "-", ""):
                try:
                    de = float(de_raw)
                except (ValueError, TypeError):
                    de = None

        profit_margin = safe_float("ProfitMargin")
        dividend_yield = safe_float("DividendYield")
        week52_high = safe_float("52WeekHigh")
        price = safe_float("AnalystTargetPrice")  # 근사 — 실시간 가격은 별도 API

        # 52주 고점 대비 하락률
        drop_pct = None
        if week52_high and price and week52_high > 0:
            drop_pct = round((price / week52_high - 1) * 100, 1)

        return {
            "ticker": ticker,
            "per": round(per, 1) if per else None,
            "roe": round(roe * 100, 1) if roe else None,
            "debt_equity": round(de, 2) if de else None,
            "profit_margin": round(profit_margin * 100, 1) if profit_margin else None,
            "drop_from_high_pct": drop_pct,
            "dividend_yield": round(dividend_yield * 100, 1) if dividend_yield else None,
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def fetch_all(tickers: list, api_key: str) -> list:
    """여러 종목 순회. 5 req/min 제한 대응으로 3종목마다 sleep."""
    rows = []
    for i, ticker in enumerate(tickers):
        rows.append(fetch_fundamentals(ticker, api_key))
        # rate limit: 5 req/min → 3종목 후 15초 대기
        if (i + 1) % 3 == 0 and (i + 1) < len(tickers):
            time.sleep(15)
    return rows


def _fmt(val, suffix: str = "", multiplier: float = 1.0) -> str:
    if val is None:
        return "-"
    return f"{val * multiplier}{suffix}"


def build_fundamentals_table(rows: list) -> str:
    """monospace 텔레그램 표 메시지 생성."""
    header = f"{'티커':<6} {'PER':>5} {'ROE':>5} {'D/E':>5} {'Margin':>7} {'52W%':>5} {'Div':>5}"
    lines = ["```", header, "-" * len(header)]

    for r in rows:
        if r.get("error"):
            lines.append(f"{r['ticker']:<6} {'-':>5} {'-':>5} {'-':>5} {'-':>7} {'-':>5} {'-':>5}")
            continue

        per_s = f"{r['per']}×" if r['per'] else "-"
        roe_s = f"{r['roe']}%" if r['roe'] else "-"
        de_s = f"{r['debt_equity']}" if r['debt_equity'] is not None else "-"
        margin_s = f"{r['profit_margin']}%" if r['profit_margin'] else "-"
        drop_s = f"{r['drop_from_high_pct']}%" if r['drop_from_high_pct'] is not None else "-"
        div_s = f"{r['dividend_yield']}%" if r['dividend_yield'] else "-"

        lines.append(f"{r['ticker']:<6} {per_s:>5} {roe_s:>5} {de_s:>5} {margin_s:>7} {drop_s:>5} {div_s:>5}")

    lines.append("```")
    return "\n".join(lines)
