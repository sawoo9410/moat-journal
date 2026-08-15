#!/usr/bin/env python3
"""QLD 라운드트립(극단 낙폭 진입 → 고점 회복 청산 → 손절) 백테스트.

QLD 전체 일별 히스토리(yfinance, 2006~)로 엔트리 낙폭 E × 손절 S를 스윕해
승률·평균수익·최악·기대값·평균보유일을 낸다. todo.md Task K.6의 파라미터 근거.
표본이 극소(20년간 깊은 낙폭 2~5회)라 확정값이 아닌 시작 규칙 — 라이브 데이터로 재보정.

사용:
    python automation/src/tools/qld_backtest.py
    python automation/src/tools/qld_backtest.py --detail 0.45 0.15   # 특정 (E,S) 개별 거래
"""
import argparse

import yfinance as yf


def _load_qld():
    px = yf.download("QLD", start="2006-01-01", auto_adjust=True, progress=False)["Close"]
    px = px.dropna()
    if hasattr(px, "columns"):
        px = px.iloc[:, 0]
    return px.index, px.astype(float).values


def _running_ath(vals):
    ath, cur = [], -1e18
    for v in vals:
        cur = max(cur, v)
        ath.append(cur)
    return ath


def backtest(dates, vals, ath, E, S):
    """진입: ATH 대비 낙폭 ≤ -E 최초. 청산: 진입가 -S 추가하락(손절) 또는 진입시점 고점 회복(익절).
    에피소드당 1회, 청산 후 새 ATH 갱신되어야 재진입."""
    n = len(vals)
    trades, i, armed = [], 0, True
    while i < n:
        peak = ath[i]
        if armed and vals[i] / peak - 1.0 <= -E:
            entry = vals[i]
            stop_px, target_px = entry * (1 - S), peak
            j, outcome = i + 1, None
            while j < n:
                if vals[j] <= stop_px:
                    outcome = ("손절", vals[j] / entry - 1.0, j); break
                if vals[j] >= target_px:
                    outcome = ("익절(회복)", vals[j] / entry - 1.0, j); break
                j += 1
            if outcome is None:
                outcome = ("미청산", vals[-1] / entry - 1.0, n - 1)
            trades.append((dates[i].date(), dates[outcome[2]].date(), outcome[0],
                           100 * outcome[1], (dates[outcome[2]] - dates[i]).days))
            armed, i = False, outcome[2] + 1
            continue
        if vals[i] >= peak:
            armed = True
        i += 1
    return trades


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", nargs=2, type=float, metavar=("E", "S"),
                    help="특정 (E,S)의 개별 거래 출력")
    args = ap.parse_args()

    dates, vals = _load_qld()
    ath = _running_ath(vals)
    print(f"QLD 일수: {len(vals)}  기간: {dates[0].date()} ~ {dates[-1].date()}")

    if args.detail:
        E, S = args.detail
        print(f"\n=== 상세: E={E:.0%}, S={S:.0%} ===")
        for t in backtest(dates, vals, ath, E, S):
            print(f"  {t[0]} → {t[1]} [{t[2]}] {t[3]:+.1f}% ({t[4]}일)")
        return

    print(f"\n{'E':>4} {'S':>4} | {'거래':>3} {'익절':>3} {'손절':>3} | {'승률':>5} {'평균%':>7} {'최악%':>7} {'평균보유일':>7}")
    for E in [0.25, 0.35, 0.45, 0.55]:
        for S in [0.08, 0.12, 0.15, 0.20, 0.25]:
            tr = backtest(dates, vals, ath, E, S)
            if not tr:
                print(f"{E:>4.0%} {S:>4.0%} | (거래 없음)"); continue
            rets = [t[3] for t in tr]
            wins = [t for t in tr if t[2].startswith("익절")]
            losses = [t for t in tr if t[2] == "손절"]
            wr = 100 * len(wins) / len(tr)
            avg = sum(rets) / len(rets)
            hold = sum(t[4] for t in tr) / len(tr)
            print(f"{E:>4.0%} {S:>4.0%} | {len(tr):>3} {len(wins):>3} {len(losses):>3} | "
                  f"{wr:>4.0f}% {avg:>6.1f} {min(rets):>6.1f} {hold:>7.0f}")


if __name__ == "__main__":
    main()
