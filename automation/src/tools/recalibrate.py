#!/usr/bin/env python3
"""buy-timing 수치 게이트 재보정 도구.

낙폭(drop_from_high) 임계값은 fundamentals.csv에서 **결정론적으로 재계산**하고,
PER 정성판정(per_reliable/cheap/rich/looseness)은 기존 calibration.yaml에서 **보존**한다.
PER 신뢰도는 실적 재작성/일회성 이익에 민감하므로 주기적으로 하네스(종목별 LLM)로 재판정이 필요 —
이 도구는 신뢰도를 스스로 바꾸지 않고, 재검토가 필요한 종목을 알려준다.

사용:
    python automation/src/tools/recalibrate.py             # 전체 히스토리로 재계산
    python automation/src/tools/recalibrate.py --days 90   # 최근 90일 윈도우
    python automation/src/tools/recalibrate.py --dry-run   # 파일 안 쓰고 출력만

첫 PER 판정은 하네스로 수행 후 calibration.yaml에 반영한다(자동화 아님, 의도적).
"""
import argparse
import csv
import sys
from datetime import date as _date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
CSV_DIR = ROOT / "companies"
CALIB_PATH = ROOT / "automation" / "calibration.yaml"


def _percentile(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    i = (len(xs) - 1) * q
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 2)


def _load_drops(ticker, days=None):
    p = CSV_DIR / ticker / "fundamentals.csv"
    if not p.exists():
        return [], (None, None)
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    if days:
        rows = rows[-days:]
    drops = []
    for r in rows:
        s = (r.get("drop_from_high_pct") or "").strip()
        if s in ("", "N/A", "None"):
            continue
        try:
            drops.append(float(s))
        except ValueError:
            pass
    rng = (rows[0]["date"], rows[-1]["date"]) if rows else (None, None)
    return drops, rng


def recalibrate(days=None, today=None):
    if not CALIB_PATH.exists():
        raise SystemExit(f"기존 calibration.yaml 없음: {CALIB_PATH} — 최초 판정은 하네스로 생성 필요")
    calib = yaml.safe_load(CALIB_PATH.read_text(encoding="utf-8")) or {}
    tickers = calib.get("tickers") or {}

    updated = {}
    to_review = []
    n_window = 0
    window = (None, None)
    for t, tk in tickers.items():
        drops, rng = _load_drops(t, days)
        if not drops:
            updated[t] = tk
            continue
        n_window = max(n_window, len(drops))
        window = rng
        median = _percentile(drops, 0.5)
        p25 = _percentile(drops, 0.25)
        p75 = _percentile(drops, 0.75)
        loose = tk.get("looseness", "ok")
        dd_typical = p25 if loose == "too_loose" else median  # too_loose는 더 깊은 dip 요구
        new = dict(tk)
        new["dd_typical"] = dd_typical
        new["dd_shallow"] = p75
        updated[t] = new
        if tk.get("per_reliable"):
            to_review.append(t)

    calib["tickers"] = updated
    calib.setdefault("meta", {})
    calib["meta"]["generated"] = (today or _date.today().isoformat())
    calib["meta"]["window"] = {"start": window[0], "end": window[1], "n": n_window}
    return calib, to_review


def _dump(calib):
    return yaml.safe_dump(calib, allow_unicode=True, sort_keys=False, default_flow_style=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=None, help="최근 N일 윈도우(기본: 전체)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--today", default=None, help="generated 날짜 오버라이드(YYYY-MM-DD)")
    args = ap.parse_args()

    calib, to_review = recalibrate(days=args.days, today=args.today)
    out = _dump(calib)
    if args.dry_run:
        print(out)  # stdout: YAML만 (파이프 검증용)
    else:
        CALIB_PATH.write_text(out, encoding="utf-8")
        print(f"[recalibrate] {CALIB_PATH} 갱신 (window n={calib['meta']['window']['n']})", file=sys.stderr)
    if to_review:
        print(
            "[recalibrate] PER 신뢰도 재검토 권장(하네스 재실행) — 실적 재작성 가능: "
            + ", ".join(to_review),
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
