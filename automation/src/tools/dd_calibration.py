#!/usr/bin/env python3
"""낙폭 트리거 임계 캘리브레이션 — 구조(structure)별 근거 산출.

`automation/trigger_rules.yaml`의 임계값 근거. 표본이 짧으므로(커버드콜 2~4년)
확정값이 아니라 재보정 출발점이며, 이 스크립트를 주기적으로 재실행해 갱신한다.

측정 기준을 라이브 트리거(index_trigger.py)와 일치시킨다:
  - baseline = 전월 마지막 거래일 종가
  - 낙폭 = 당월 종가가 baseline 대비 최대 얼마나 빠졌나
  - de-dup 규칙상 알림 단위가 '월'이므로 이벤트도 월 단위로 센다
  - auto_adjust=True (yf history() 기본값과 동일 = 분배금 재투자 반영)

사용:
    python automation/src/tools/dd_calibration.py            # 전체
    python automation/src/tools/dd_calibration.py freq       # 임계별 알림 빈도(기간 정합)
    python automation/src/tools/dd_calibration.py capture    # 상/하방 캡처율
    python automation/src/tools/dd_calibration.py recovery   # 낙폭 회복률(조정가 vs NAV)
    python automation/src/tools/dd_calibration.py ath        # QLD ATH 에피소드·조건부 심화확률
    python automation/src/tools/dd_calibration.py match      # 트래커와 빈도가 같아지는 등가 임계
"""
import sys
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

THRESHOLDS = [-0.03, -0.05, -0.07, -0.10]
ATH_LEVELS = [-0.20, -0.25, -0.30, -0.35, -0.40, -0.45, -0.50]

# 트래커 기준 빈도의 레퍼런스(장기 히스토리 보유 종목)
REFERENCE = ["SPY", "QQQ", "SCHD"]

# (구조 종목, 언더라잉) — 구조 효과를 언더라잉 대비로 분리하기 위한 쌍
PAIRS = [
    ("JEPQ", "QQQ"), ("QQQI", "QQQ"), ("GPIQ", "QQQ"),
    ("SPYI", "SPY"), ("GPIX", "SPY"),
    ("458760.KS", "SCHD"), ("0008S0.KS", "SCHD"),
    ("QLD", "QQQ"),
]

_cache = {}


def load(ticker: str, adjusted: bool = True):
    key = (ticker, adjusted)
    if key not in _cache:
        px = yf.download(ticker, start="1990-01-01", auto_adjust=adjusted,
                         progress=False)["Close"].dropna()
        if hasattr(px, "columns"):
            px = px.iloc[:, 0]
        _cache[key] = px.astype(float)
    return _cache[key]


def month_frames(px, start=None, end=None):
    """월별 (baseline, 당월 시계열). baseline=전월 마지막 거래일 종가."""
    if start is not None:
        px = px[(px.index >= start) & (px.index <= end)]
    key = px.index.to_period("M")
    months = list(dict.fromkeys(key))
    out = []
    for i in range(1, len(months)):
        prev, cur = px[key == months[i - 1]], px[key == months[i]]
        if prev.empty or cur.empty:
            continue
        out.append((float(prev.iloc[-1]), cur))
    return out


def month_mins(px, start=None, end=None):
    return np.array([float((cur / base - 1.0).min()) for base, cur in month_frames(px, start, end)])


def capture(px, ux):
    """월간 수익률 기준 상/하방 캡처율 — 언더라잉이 오른/내린 달만 각각."""
    a = px.resample("ME").last().pct_change().dropna()
    b = ux.resample("ME").last().pct_change().dropna()
    j = pd.concat([a, b], axis=1, join="inner").dropna()
    j.columns = ["x", "u"]
    up, dn = j[j["u"] > 0], j[j["u"] < 0]
    uc = up["x"].sum() / up["u"].sum() if len(up) >= 6 and up["u"].sum() else None
    dc = dn["x"].sum() / dn["u"].sum() if len(dn) >= 6 and dn["u"].sum() else None
    return uc, dc, len(up), len(dn)


def cmd_freq():
    print("=" * 84)
    print("임계별 알림 빈도 — 구조/언더라잉을 '같은 개월'로만 비교 (연 알림 횟수)")
    print("=" * 84)
    print(f"{'페어':<20}{'공통기간':<18}" + "".join(f"{int(t*100):>13}%" for t in THRESHOLDS) + f"{'빈도비':>9}")
    for a, u in PAIRS:
        pa, pu = load(a), load(u)
        s, e = max(pa.index[0], pu.index[0]), min(pa.index[-1], pu.index[-1])
        ma, mu = month_mins(pa, s, e), month_mins(pu, s, e)
        n = min(len(ma), len(mu))
        if n < 12:
            print(f"{a+' vs '+u:<20}표본 부족({n}개월)")
            continue
        ma, mu = ma[:n], mu[:n]
        cells, rr = [], []
        for t in THRESHOLDS:
            fa, fu = (ma <= t).sum() / n * 12, (mu <= t).sum() / n * 12
            cells.append(f"{fa:>5.1f}/{fu:<5.1f}")
            if fu > 0:
                rr.append(fa / fu)
        span = f"{s.strftime('%Y-%m')}~{e.strftime('%Y-%m')}"
        print(f"{a+' vs '+u:<20}{span:<18}" + "".join(f"{c:>14}" for c in cells)
              + f"{np.median(rr) if rr else float('nan'):>8.2f}x")


def cmd_capture():
    print("=" * 84)
    print("상/하방 캡처율 — 언더라잉이 오른 달 / 내린 달의 참여율")
    print("=" * 84)
    for a, u in PAIRS:
        uc, dc, nu, nd = capture(load(a), load(u))
        if uc is None or dc is None:
            print(f"{a:<12} vs {u:<6} 표본 부족(상승 {nu}/하락 {nd})")
            continue
        verdict = "유리" if uc > dc else "불리"
        print(f"{a:<12} vs {u:<6} 상승 {uc:.2f}x  하락 {dc:.2f}x  비대칭 {uc/dc:.2f} ({verdict})"
              f"   상승월 {nu}/하락월 {nd}")
        print(f"{'':21}→ 하락캡처 환산 등가 임계: "
              + "  ".join(f"{int(t*100)}%→{t*dc*100:.1f}%" for t in THRESHOLDS))


def _events(px, t):
    """임계 t 최초 돌파 (인덱스, baseline) 목록."""
    pos = {d: i for i, d in enumerate(px.index)}
    out = []
    for base, cur in month_frames(px):
        dd = cur / base - 1.0
        br = dd[dd <= t]
        if not br.empty:
            out.append((pos[br.index[0]], base))
    return out


def _recovery(px, events, horizon=252):
    vals = px.values
    res = []
    for i0, base in events:
        seg = vals[i0:i0 + horizon]
        res.append(int(np.argmax(seg >= base)) if (seg >= base).any() else None)
    return res


def cmd_recovery():
    print("=" * 84)
    print("낙폭 회복 — 1년 내 baseline 복귀율. 조정가(분배 포함) vs 원가격(NAV)")
    print("=" * 84)
    print("조정가만 회복하고 NAV는 못 오면 '분배금이 가린 침식' — 그 경우 낙폭은 매수 기회가 아니다.")
    tickers = REFERENCE + [a for a, _ in PAIRS]
    for t in (-0.03, -0.05):
        print(f"\n[전월말 대비 {int(t*100)}% 돌파 후]")
        print(f"{'종목':<12}{'건수':>6}{'조정가 복귀':>13}{'중앙일':>8}{'NAV 복귀':>11}{'중앙일':>8}")
        for tk in tickers:
            try:
                a, r = load(tk, True), load(tk, False)
            except Exception:
                continue
            ea, er = _events(a, t), _events(r, t)
            if len(ea) < 3:
                continue
            ra, rr = _recovery(a, ea), _recovery(r, er)
            oa = [x for x in ra if x is not None]
            orr = [x for x in rr if x is not None]
            print(f"{tk:<12}{len(ea):>6}{100*len(oa)/len(ra):>12.0f}%"
                  f"{np.median(oa) if oa else float('nan'):>8.0f}"
                  f"{100*len(orr)/len(rr) if rr else float('nan'):>10.0f}%"
                  f"{np.median(orr) if orr else float('nan'):>8.0f}")


def cmd_ath(ticker="QLD"):
    px = load(ticker)
    vals, idx = px.values, px.index
    ath = np.maximum.accumulate(vals)
    dd = vals / ath - 1.0
    yrs = (idx[-1] - idx[0]).days / 365.25

    eps, i, n = [], 0, len(vals)
    while i < n:
        if dd[i] <= ATH_LEVELS[0]:
            peak = ath[i]
            j = i
            while j < n and vals[j] < peak:
                j += 1
            eps.append({"start": idx[i], "trough": float(vals[i:j].min() / peak - 1.0),
                        "rec": (j - i) if j < n else None})
            i = j
        else:
            i += 1

    print("=" * 84)
    print(f"{ticker} ATH 기준 낙폭 에피소드 — {idx[0].date()}~{idx[-1].date()} ({yrs:.1f}년)")
    print("=" * 84)
    print(f"{'시작일':<14}{'최심낙폭':>10}{'ATH 회복':>14}")
    for e in eps:
        print(f"{str(e['start'].date()):<14}{e['trough']*100:>9.1f}%"
              f"{(str(e['rec'])+'일') if e['rec'] else '미회복':>14}")

    print(f"\n{'레벨':<8}{'도달':>6}{'주기':>10}{'회복 중앙':>11}{'추가 5%p 심화':>16}")
    for L in ATH_LEVELS[:-1]:
        reach = [e for e in eps if e["trough"] <= L]
        deeper = [e for e in eps if e["trough"] <= L - 0.05]
        if not reach:
            continue
        recs = [e["rec"] for e in reach if e["rec"]]
        print(f"{int(L*100):>4}%{len(reach):>8}건{yrs/len(reach):>8.1f}년"
              f"{np.median(recs) if recs else float('nan'):>9.0f}일"
              f"{len(deeper):>10}건 ({100*len(deeper)/len(reach):>5.1f}%)")


def cmd_match():
    print("=" * 84)
    print("빈도 정합 등가 임계 — 트래커와 같은 알림 빈도를 주는 값")
    print("=" * 84)
    ref = {}
    for t in THRESHOLDS:
        fs = []
        for tk in REFERENCE:
            m = month_mins(load(tk))
            fs.append((m <= t).sum() / len(m) * 12)
        ref[t] = float(np.mean(fs))
    print("기준(" + "/".join(REFERENCE) + " 평균, 연 알림 횟수): "
          + ", ".join(f"{int(t*100)}%={ref[t]:.1f}" for t in THRESHOLDS))
    print()
    grid = [round(-0.01 * i, 2) for i in range(1, 41)]
    for a, _u in PAIRS:
        m = month_mins(load(a))
        n = len(m)
        if n < 12:
            continue
        cells = []
        for t in THRESHOLDS:
            best = min(grid, key=lambda g: abs((m <= g).sum() / n * 12 - ref[t]))
            cells.append(f"{int(t*100):>3}%→{int(best*100):>4}%")
        print(f"{a:<12}({n:>3}개월)  " + "  ".join(cells))


def cmd_deepen(ticker="QLD", thresholds=None):
    """'지금 살까 더 기다릴까' — 알림 후 baseline 복귀 전까지 더 깊이 간 비율.

    trigger_rules.yaml의 `deepening` 블록 근거. 구간 중간지점을 포함해 센다.
    """
    ths = thresholds or [-0.07, -0.12, -0.16, -0.21]
    # 관찰 지점 = 임계 + 인접 임계 사이의 중간지점 전부
    mids = [round((ths[i] + ths[i + 1]) / 2, 4) for i in range(len(ths) - 1)]
    points = sorted(set(ths + mids), reverse=True)
    nxt = {t: [p for p in points if p < t] for t in ths[:-1]}

    px = load(ticker)
    vals, idx = px.values, px.index
    pos = {d: i for i, d in enumerate(idx)}
    evs = []
    for base, cur in month_frames(px):
        done = None
        for d, p in zip(cur.index, cur.values):
            br = [t for t in ths if p / base - 1.0 <= t]
            if not br:
                continue
            lv = min(br)
            if done is not None and lv >= done:
                continue
            done = lv
            i0 = pos[d]
            seg = vals[i0:i0 + 504]
            hit = np.argmax(seg >= base) if (seg >= base).any() else None
            win = seg[:hit + 1] if hit is not None else seg
            evs.append({"level": lv, "min_dd": float(win.min() / base - 1.0)})

    print("=" * 84)
    print(f"{ticker} — 알림 후 어디까지 더 빠졌나 (baseline 복귀 전까지)")
    print("=" * 84)
    for lv in ths[:-1]:
        sub = [e for e in evs if e["level"] == lv]
        if len(sub) < 5:
            continue
        print(f"\n[{int(lv*100)}% 알림 {len(sub)}건]")
        for t in nxt[lv]:
            p = 100.0 * np.mean([e["min_dd"] <= t for e in sub])
            tag = " ← 구간 중간" if t not in ths else ""
            print(f"   {t*100:>6.1f}% 도달 {p:>5.0f}%{tag}")
        ri = 100.0 * np.mean([e["min_dd"] > lv - 0.005 for e in sub])
        print(f"   추가 하락 없이 회복 {ri:>5.0f}%")


CMDS = {"freq": cmd_freq, "capture": cmd_capture, "recovery": cmd_recovery,
        "ath": cmd_ath, "match": cmd_match, "deepen": cmd_deepen}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "all":
        for name, fn in CMDS.items():
            fn()
            print()
        return 0
    if arg not in CMDS:
        print(f"알 수 없는 명령: {arg} ({'|'.join(CMDS)}|all)", file=sys.stderr)
        return 1
    CMDS[arg]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
