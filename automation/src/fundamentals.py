"""펀더멘탈 데이터 조회 + 텔레그램 표 빌드.

주 소스: yfinance (Yahoo Finance, API 키 불필요).
폴백 체인(전부 무료): yfinance → stooq(가격/52주) → Finnhub(선택 키) → FMP(선택 키).
필드 단위는 모든 소스에서 동일하게 정규화: ROE/Margin/배당=%, D/E=비율.
"""
import datetime
import os
import time

import requests

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


# 반환 dict 공통 키
_FIELDS = ("per", "roe", "debt_equity", "profit_margin", "drop_from_high_pct", "dividend_yield")


def _empty_row(ticker: str) -> dict:
    row = {"ticker": ticker, "name": ""}
    for f in _FIELDS:
        row[f] = None
    return row


def _need_more(row: dict) -> bool:
    """아직 None인 필드가 남았는지 — 폴백 소스 호출 여부 판단."""
    return any(row.get(f) is None for f in _FIELDS)


def _merge(row: dict, patch: dict) -> None:
    """None인 필드만 patch 값으로 보완(필드 단위 merge)."""
    if not patch:
        return
    if not row.get("name") and patch.get("name"):
        row["name"] = patch["name"]
    for f in _FIELDS:
        if row.get(f) is None and patch.get(f) is not None:
            row[f] = patch[f]


# ---------------------------------------------------------------------------
# 소스 1: yfinance (주 소스)
# ---------------------------------------------------------------------------

def _fetch_yfinance(ticker: str) -> dict:
    if yf is None:
        return {}
    info = yf.Ticker(ticker).info
    if not info or not (info.get("shortName") or info.get("longName")):
        return {}

    def f1(v, mult=1.0):
        if v is None:
            return None
        try:
            return round(float(v) * mult, 1)
        except (ValueError, TypeError):
            return None

    per = f1(info.get("trailingPE"))
    roe = f1(info.get("returnOnEquity"), 100.0)          # 소수 → %
    profit_margin = f1(info.get("profitMargins"), 100.0)  # 소수 → %
    dividend_yield = f1(info.get("dividendYield"))         # yfinance 이미 %

    # D/E: Yahoo는 퍼센트(예 168.7 → 1.69 비율)
    de = info.get("debtToEquity")
    debt_equity = None
    if de is not None:
        try:
            debt_equity = round(float(de) / 100.0, 2)
        except (ValueError, TypeError):
            debt_equity = None

    # 52주 고점 대비 — 현재가 사용(실값)
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    high = info.get("fiftyTwoWeekHigh")
    drop_pct = None
    try:
        if price and high and float(high) > 0:
            drop_pct = round((float(price) / float(high) - 1) * 100, 1)
    except (ValueError, TypeError):
        drop_pct = None

    return {
        "name": info.get("shortName") or info.get("longName") or "",
        "per": per,
        "roe": roe,
        "debt_equity": debt_equity,
        "profit_margin": profit_margin,
        "drop_from_high_pct": drop_pct,
        "dividend_yield": dividend_yield,
    }


# ---------------------------------------------------------------------------
# 소스 2: stooq (가격·52주 고점만; 키 불필요)
# ---------------------------------------------------------------------------

def _fetch_stooq(ticker: str) -> dict:
    """stooq 1년 일봉 CSV로 현재가·52주 고점 → drop_from_high_pct 보완."""
    sym = f"{ticker.lower()}.us"
    url = f"https://stooq.com/q/d/l/?s={sym}&i=d"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        lines = resp.text.strip().splitlines()
        if len(lines) < 2 or not lines[0].lower().startswith("date"):
            return {}
        highs = []
        last_close = None
        # 최근 ~252 거래일만
        for line in lines[1:][-252:]:
            cols = line.split(",")
            if len(cols) < 5:
                continue
            try:
                high = float(cols[2])
                close = float(cols[4])
            except (ValueError, IndexError):
                continue
            highs.append(high)
            last_close = close
        if not highs or last_close is None:
            return {}
        week52_high = max(highs)
        drop_pct = round((last_close / week52_high - 1) * 100, 1) if week52_high > 0 else None
        return {"drop_from_high_pct": drop_pct}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# 소스 3: Finnhub (선택 — .env에 FINNHUB_API_KEY 있을 때만)
# ---------------------------------------------------------------------------

def _fetch_finnhub(ticker: str) -> dict:
    key = os.environ.get("FINNHUB_API_KEY", "")
    if not key:
        return {}
    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/stock/metric",
            params={"symbol": ticker, "metric": "all", "token": key},
            timeout=15,
        )
        resp.raise_for_status()
        m = resp.json().get("metric", {}) or {}

        def num(v, ndigits=1):
            if v is None:
                return None
            try:
                return round(float(v), ndigits)
            except (ValueError, TypeError):
                return None

        out = {
            "per": num(m.get("peTTM")),
            "roe": num(m.get("roeTTM")),            # Finnhub는 이미 %
            "profit_margin": num(m.get("netProfitMarginTTM")),  # %
            "dividend_yield": num(m.get("currentDividendYieldTTM")),  # %
        }
        # 52주 고점 대비
        high = m.get("52WeekHigh")
        price = m.get("price") or m.get("lastPrice")
        if high and price:
            try:
                out["drop_from_high_pct"] = round((float(price) / float(high) - 1) * 100, 1)
            except (ValueError, TypeError):
                pass
        return out
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# 소스 4: Financial Modeling Prep (선택 — .env에 FMP_API_KEY 있을 때만)
# ---------------------------------------------------------------------------

def _fetch_fmp(ticker: str) -> dict:
    key = os.environ.get("FMP_API_KEY", "")
    if not key:
        return {}
    try:
        base = "https://financialmodelingprep.com/api/v3"
        ratios = requests.get(f"{base}/ratios-ttm/{ticker}", params={"apikey": key}, timeout=15).json()
        quote = requests.get(f"{base}/quote/{ticker}", params={"apikey": key}, timeout=15).json()
        r = ratios[0] if isinstance(ratios, list) and ratios else {}
        q = quote[0] if isinstance(quote, list) and quote else {}

        def num(v, mult=1.0, ndigits=1):
            if v is None:
                return None
            try:
                return round(float(v) * mult, ndigits)
            except (ValueError, TypeError):
                return None

        out = {
            "per": num(r.get("peRatioTTM")),
            "roe": num(r.get("returnOnEquityTTM"), 100.0),       # 소수 → %
            "debt_equity": num(r.get("debtEquityRatioTTM"), 1.0, 2),  # 이미 비율
            "profit_margin": num(r.get("netProfitMarginTTM"), 100.0),  # 소수 → %
            "dividend_yield": num(r.get("dividendYielTTM") or r.get("dividendYieldTTM"), 100.0),  # 소수 → %
        }
        high = q.get("yearHigh")
        price = q.get("price")
        if high and price:
            try:
                out["drop_from_high_pct"] = round((float(price) / float(high) - 1) * 100, 1)
            except (ValueError, TypeError):
                pass
        return out
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# 통합 fetch
# ---------------------------------------------------------------------------

def fetch_fundamentals(ticker: str) -> dict:
    """우선순위 소스를 순회하며 필드 단위 merge.

    반환: {ticker, name, per, roe, debt_equity, profit_margin, drop_from_high_pct,
           dividend_yield, sources}
    `sources`는 실제로 ≥1개 필드를 채운 소스명 리스트(우선순위 순).
    전 소스 실패 시 {ticker, error: str}.
    """
    row = _empty_row(ticker)
    errors = []
    sources: list = []

    def _apply(name: str, patch: dict) -> None:
        before = sum(1 for f in _FIELDS if row.get(f) is None)
        _merge(row, patch)
        after = sum(1 for f in _FIELDS if row.get(f) is None)
        if after < before:  # 이 소스가 최소 1개 필드를 채움
            sources.append(name)

    # 1) yfinance (주 소스) — 빈 응답/예외 시 1회 재시도
    for attempt in range(2):
        try:
            patch = _fetch_yfinance(ticker)
            if patch:
                _apply("yfinance", patch)
                break
        except Exception as e:
            errors.append(f"yfinance: {e}")
        if attempt == 0:
            time.sleep(2)

    # 2) stooq — 가격/52주 비었을 때만
    if row.get("drop_from_high_pct") is None:
        try:
            _apply("stooq", _fetch_stooq(ticker))
        except Exception as e:
            errors.append(f"stooq: {e}")

    # 3) Finnhub (선택 키)
    if _need_more(row):
        try:
            _apply("finnhub", _fetch_finnhub(ticker))
        except Exception as e:
            errors.append(f"finnhub: {e}")

    # 4) FMP (선택 키)
    if _need_more(row):
        try:
            _apply("fmp", _fetch_fmp(ticker))
        except Exception as e:
            errors.append(f"fmp: {e}")

    # 전 필드 None + 이름 없음 = 완전 실패
    if not row.get("name") and all(row.get(f) is None for f in _FIELDS):
        return {"ticker": ticker, "error": "; ".join(errors) or "no data"}
    row["sources"] = sources
    return row


def fetch_all(tickers: list) -> list:
    """여러 종목 순회. Yahoo 보호용 종목당 짧은 sleep."""
    rows = []
    for i, ticker in enumerate(tickers):
        rows.append(fetch_fundamentals(ticker))
        if i + 1 < len(tickers):
            time.sleep(0.4)
    return rows


# ---------------------------------------------------------------------------
# 지수/ETF 트랙 (index 레인) — Task K
#   주식 moat 함수(위)는 불변. 아래는 지수/ETF 전용 수집.
#   yfinance history 로 price/52주고점/MA/낙폭, .info 로 PER,
#   .dividends 로 분배율(TTM/ann) 직접 계산. KR 등은 PER=None → 상속.
# ---------------------------------------------------------------------------

# self 를 뜻하는 valuation_source 표기(프로필/표에서 다양하게 올 수 있음)
_SELF_MARKERS = ("", "self", "(self)", "none", "null")


def _is_self_source(vs) -> bool:
    """valuation_source 값이 self(상속 없음)를 뜻하는지."""
    if vs is None:
        return True
    try:
        return str(vs).strip().lower() in _SELF_MARKERS
    except Exception:
        return True


def _profile_ticker(profile: dict) -> str:
    """프로필의 안정적 식별자(ticker 우선, 없으면 yf_symbol)."""
    return profile.get("ticker") or profile.get("yf_symbol") or ""


def _dividends_in_window(divs, ref_date: "datetime.datetime", days: int) -> list:
    """분배 시계열에서 ref_date 기준 최근 `days`일 이내의 (날짜, 금액) 리스트.

    divs: yf.Ticker().dividends (pandas Series) 또는 items() 지원 매핑.
    양수 금액만, tz 정보는 제거하고 naive 비교.
    """
    out: list = []
    if divs is None:
        return out
    try:
        items = list(divs.items())
    except Exception:
        return out
    cutoff = ref_date - datetime.timedelta(days=days)
    upper = ref_date + datetime.timedelta(days=1)
    for dt, amt in items:
        try:
            d = dt.to_pydatetime() if hasattr(dt, "to_pydatetime") else dt
            if getattr(d, "tzinfo", None) is not None:
                d = d.replace(tzinfo=None)
            a = float(amt)
            if a > 0 and cutoff <= d <= upper:
                out.append((d, a))
        except Exception:
            continue
    return out


def fetch_index_instrument(profile: dict) -> dict:
    """지수/ETF 1종목 수집(모든 유형·KR 포함).

    반환 dict 키:
      ticker, price, per, dist_yield_ttm, dist_yield_ann,
      drop_from_high_pct, ma50_gap_pct, ma200_gap_pct, currency, sources

    - price: history(period="1y") 최근 종가
    - drop_from_high_pct: (price/52주고점 - 1)*100
    - ma50_gap_pct / ma200_gap_pct: (price/MA - 1)*100 (자기 종가 시계열)
    - per: .info trailingPE (US ETF). KR 등 없으면 None → 상위에서 상속
    - dist_yield_ttm: 최근 365일 분배금 합 / price * 100
    - dist_yield_ann: 최근 분배 × 최근 365일 지급횟수 / price * 100
    누락/예외는 None 처리 — 절대 예외로 중단하지 않는다.
    """
    sym = profile.get("yf_symbol")
    row = {
        "ticker": _profile_ticker(profile),
        "price": None,
        "per": None,
        "dist_yield_ttm": None,
        "dist_yield_ann": None,
        "drop_from_high_pct": None,
        "ma50_gap_pct": None,
        "ma200_gap_pct": None,
        "currency": profile.get("currency"),
        "sources": [],
    }
    if yf is None or not sym:
        return row

    try:
        tk = yf.Ticker(sym)
    except Exception:
        return row

    price = None
    ref_date = None

    # 1) 가격 히스토리 → price / 52주고점 / MA50 / MA200
    try:
        hist = tk.history(period="1y")
        if hist is not None and len(hist) > 0:
            closes = [float(c) for c in hist["Close"].tolist() if c == c]  # NaN 제거
            try:
                highs = [float(h) for h in hist["High"].tolist() if h == h]
            except Exception:
                highs = []
            if closes:
                price = closes[-1]
                row["price"] = round(price, 4)

                hi_source = highs if highs else closes
                week52_high = max(hi_source) if hi_source else None
                if week52_high and week52_high > 0:
                    row["drop_from_high_pct"] = round((price / week52_high - 1) * 100, 2)

                if len(closes) >= 50:
                    ma50 = sum(closes[-50:]) / 50.0
                    if ma50 > 0:
                        row["ma50_gap_pct"] = round((price / ma50 - 1) * 100, 2)
                if len(closes) >= 200:
                    ma200 = sum(closes[-200:]) / 200.0
                    if ma200 > 0:
                        row["ma200_gap_pct"] = round((price / ma200 - 1) * 100, 2)

                # 분배 윈도우 기준일 = 마지막 거래일
                try:
                    last_idx = hist.index[-1]
                    ref_date = (
                        last_idx.to_pydatetime()
                        if hasattr(last_idx, "to_pydatetime")
                        else last_idx
                    )
                    if getattr(ref_date, "tzinfo", None) is not None:
                        ref_date = ref_date.replace(tzinfo=None)
                except Exception:
                    ref_date = None

                if "yfinance" not in row["sources"]:
                    row["sources"].append("yfinance")
    except Exception:
        pass

    if ref_date is None:
        ref_date = datetime.datetime.now()

    # 2) PER — .info trailingPE (US ETF). KR 등은 None → 상속 대상
    try:
        info = tk.info or {}
        pe = info.get("trailingPE")
        if pe is not None:
            row["per"] = round(float(pe), 1)
    except Exception:
        pass

    # 3) 분배율 — .info["yield"] 금지, 실제 .dividends 로 직접 계산
    if price and price > 0:
        try:
            payments = _dividends_in_window(tk.dividends, ref_date, 365)
            if payments:
                ttm_sum = sum(a for _, a in payments)
                count = len(payments)
                latest_amt = max(payments, key=lambda x: x[0])[1]
                row["dist_yield_ttm"] = round(ttm_sum / price * 100, 2)
                row["dist_yield_ann"] = round(latest_amt * count / price * 100, 2)
                if "dividends" not in row["sources"]:
                    row["sources"].append("dividends")
        except Exception:
            pass

    return row


def _topo_order_indices(profiles: list) -> list:
    """valuation_source 위상 정렬 — self(상속 없음) 먼저, 상속 종목 나중.

    상속원(valuation_source)이 이번 유니버스에 있으면 그 종목을 먼저 수집해야
    같은 수집분의 PER 를 상속할 수 있다. 사이클/누락 상속원은 안전하게 뒤로.
    """
    tickers = {_profile_ticker(p) for p in profiles}
    remaining = list(profiles)
    done: set = set()
    ordered: list = []
    changed = True
    while remaining and changed:
        changed = False
        still: list = []
        for p in remaining:
            vs = p.get("valuation_source")
            # self 이거나, 상속원이 유니버스 밖이거나, 이미 수집됨 → 지금 수집 가능
            if _is_self_source(vs) or vs not in tickers or vs in done:
                ordered.append(p)
                done.add(_profile_ticker(p))
                changed = True
            else:
                still.append(p)
        remaining = still
    # 사이클 등 남은 것은 원순서 그대로 뒤에 붙임(중단 방지)
    ordered.extend(remaining)
    return ordered


def fetch_all_indices(profiles: list) -> list:
    """지수/ETF 유니버스 일괄 수집. 반환 순서는 입력 profiles 순서 유지.

    valuation_source 위상 정렬로 상속원을 먼저 수집한 뒤,
    per=None 인 종목은 상속원의 이번 수집 PER 를 상속하고
    sources 에 'per<-{SRC}' 를 남긴다.
    """
    ordered = _topo_order_indices(profiles)
    results: dict = {}
    for i, p in enumerate(ordered):
        row = fetch_index_instrument(p)
        vs = p.get("valuation_source")
        if row.get("per") is None and not _is_self_source(vs) and vs in results:
            src_per = results[vs].get("per")
            if src_per is not None:
                row["per"] = src_per
                label = f"per<-{vs}"
                if label not in row["sources"]:
                    row["sources"].append(label)
        results[_profile_ticker(p)] = row
        if i + 1 < len(ordered):
            time.sleep(0.4)  # Yahoo 보호용 짧은 sleep
    # 입력 순서로 재정렬해 반환
    return [results[_profile_ticker(p)] for p in profiles]


# ---------------------------------------------------------------------------
# 카드 빌더
# ---------------------------------------------------------------------------

def _signed(val, suffix: str = "%") -> str:
    """부호 포함 포맷. 양수면 +, 음수면 - 자동."""
    if val is None:
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val}{suffix}"


def build_fundamentals_table(rows: list) -> str:
    """카드형 텔레그램 메시지 생성 (종목당 블록)."""
    blocks: list = []

    for r in rows:
        ticker = r["ticker"]
        name = r.get("name", "")

        if r.get("error"):
            blocks.append(f"{ticker}  {name}\n  ⚠️ 조회 실패: {r['error']}")
            continue

        per_s = str(r["per"]) if r["per"] else "N/A"
        roe_s = _signed(r["roe"])
        de_s = str(r["debt_equity"]) if r["debt_equity"] is not None else "N/A"
        margin_s = _signed(r["profit_margin"])
        drop_s = f"{r['drop_from_high_pct']}%" if r["drop_from_high_pct"] is not None else "N/A"
        div_s = f"{r['dividend_yield']}%" if r["dividend_yield"] else "N/A"

        block = (
            f"{ticker}  {name}\n"
            f"  PER {per_s:>6}  ROE {roe_s:>8}\n"
            f"  D/E {de_s:>6}  Margin {margin_s:>8}\n"
            f"  52주 {drop_s:>6}  배당 {div_s:>6}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)
