"""공용 등급/게이트/유틸 모듈.

주식 moat 트랙(daily_moat.py)과 지수/ETF 트랙(index_daily.py)이 공유하는
등급 매트릭스·수치 게이트·캘리브레이션 로드·claude 실행·월간 append를 담는다.
주식 로직 동작 불변 — daily_moat.py는 여기서 import한다.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CALIB_PATH = ROOT / "automation" / "calibration.yaml"


def load_calibration() -> dict:
    """buy-timing 수치 게이트 임계값(history fit). 없거나 손상되면 {} — 매트릭스만 동작(하위호환)."""
    if not CALIB_PATH.exists():
        return {}
    try:
        return yaml.safe_load(CALIB_PATH.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"[daily_moat] calibration.yaml 로드 실패 → 게이트 미적용: {e}", file=sys.stderr)
        return {}


def ticker_calibration(calibration: dict, ticker: str) -> dict:
    return (calibration.get("tickers") or {}).get(ticker) or {}


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


# 등급 강도 순서(강한 매수 → 회피). 수치 게이트의 강등 계산에 사용.
GRADE_NOTCHES = ["신규매수 적기", "매수 고려", "관망", "회피"]

# 뉴스가 조용해도 [!]로 승격할 actionable 등급(이슈 2).
STRONG_GRADES = {"신규매수 적기", "회피"}


def _downgrade(grade: str, steps: int = 1) -> str:
    try:
        i = GRADE_NOTCHES.index(grade)
    except ValueError:
        return grade
    return GRADE_NOTCHES[min(i + steps, len(GRADE_NOTCHES) - 1)]


def _norm_pick(s: str, keys: tuple, axis: str):
    """값 문자열에서 정의된 키를 찾되, 리스트 순서가 아니라 **문자열 등장 위치**로 선택.

    헤지성 다중 매칭('고평가에서 적정으로')이면 선행 키를 채택하고 경고를 남긴다(이슈 4).
    """
    s = s or ""
    found = sorted((s.find(k), k) for k in keys if k in s)
    if not found:
        return None
    if len(found) > 1:
        print(
            f"[daily_moat] {axis} 다중 매칭 {[k for _, k in found]} → 선행 '{found[0][1]}' 채택 "
            f"(원문={s!r})",
            file=sys.stderr,
        )
    return found[0][1]


def _norm_moat_q(s: str):
    return _norm_pick(s, ("견고", "좁음", "약화", "훼손"), "Moat질")


def _norm_valuation(s: str):
    return _norm_pick(s, ("저평가", "적정", "고평가"), "밸류")


def apply_numeric_gates(grade: str, per, drop, cal: dict) -> str:
    """history 캘리브레이션 수치로 등급을 타이트하게 보정(이슈 1·6).

    cal(티커별): per_reliable, per_cheap, per_rich, dd_typical, dd_shallow (일부 None 허용).
    drop = drop_from_high_pct(음수, 0에 가까울수록 고점), per = 현재 PER.

    - Gate A (dip 확인): '신규매수 적기'는 실제 dip(낙폭 ≤ dd_typical)이고 PER froth가 아닐 때만 유지.
      아니면 1노치 강등 → 고점 근처/고평가에서 남발되던 '적기'를 억제.
    - Gate B (froth 가드): 매수 등급인데 고점 근처(낙폭 ≥ dd_shallow) + PER rich면 추가 1노치 강등.
    캘리브레이션이 없으면(cal 비어있음) 원 등급을 그대로 반환(하위호환).
    """
    if not cal:
        return grade
    dd_typ = cal.get("dd_typical")
    dd_shal = cal.get("dd_shallow")
    per_rich = cal.get("per_rich") if cal.get("per_reliable") else None

    if grade == "신규매수 적기":
        dip_ok = True
        if drop is not None and dd_typ is not None and drop > dd_typ:
            dip_ok = False  # 낙폭이 typical보다 얕음(고점 근처) → dip 아님
        if per_rich is not None and per is not None and per > per_rich:
            dip_ok = False  # 밸류 froth
        if not dip_ok:
            grade = _downgrade(grade, 1)

    if grade in ("신규매수 적기", "매수 고려"):
        near_high = drop is not None and dd_shal is not None and drop >= dd_shal
        rich = per_rich is not None and per is not None and per > per_rich
        if near_high and rich:
            grade = _downgrade(grade, 1)

    return grade


def compute_grade(moat_q: str, valuation_bucket: str, per=None, drop=None, cal: dict = None) -> str:
    """I.3 매트릭스로 최종 등급을 결정론적으로 산정 후, history 수치 게이트로 타이트하게 보정.

    자본보존 백스톱: Moat질이 약화/훼손이면 매수 등급이 절대 안 나오도록 재강제.
    파싱 실패(축 미상)는 무경고 폴백 대신 경고를 남기고 안전하게 '관망'(이슈 3·5).
    """
    mq = _norm_moat_q(moat_q)
    vb = _norm_valuation(valuation_bucket)
    if mq is None or vb is None:
        print(
            f"[daily_moat] 등급 축 파싱 실패 → 관망 폴백 (Moat질={moat_q!r}, 밸류={valuation_bucket!r})",
            file=sys.stderr,
        )
        return "관망"
    grade = GRADE_MATRIX.get((mq, vb), "관망")
    # 자본보존 백스톱 — 매트릭스가 향후 수정돼도 약화/훼손은 매수 등급 불가(현재는 매트릭스상 inert).
    if mq in ("약화", "훼손") and grade in ("신규매수 적기", "매수 고려"):
        grade = "회피" if mq == "훼손" else "관망"
    grade = apply_numeric_gates(grade, per, drop, cal or {})
    return grade


def append_monthly(ticker: str, date: str, raw: str, grade: str = None, base_dir=None) -> Path:
    """일일 분석을 월간 누적 파일({base_dir}/{TICKER}/{YYYY}/{YYYY-MM}.md)에 append.

    grade(작업 I 최종 등급)가 있으면 date 헤더에 부가: `## 2026-06-01 · 매수 고려`.
    base_dir가 None이면 기존과 동일하게 ROOT/'companies' 사용(지수 트랙은 ROOT/'indices' 전달).
    """
    if base_dir is None:
        base_dir = ROOT / "companies"
    base_dir = Path(base_dir)

    year_str, month_str, _ = date.split("-")
    year = int(year_str)
    month = int(month_str)

    monthly_dir = base_dir / ticker / year_str
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
