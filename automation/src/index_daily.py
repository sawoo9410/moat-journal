"""지수/ETF 트랙 오케스트레이터 (Task K — index 레인).

주식 moat 트랙(daily_moat.py)과 **분리된** 지수/ETF 일일 파이프라인.
moat 프레임(ROE·D/E·해자 서사) 대신 **추세 × 밸류** 매트릭스를 쓰고,
레버리지(QLD)는 매트릭스 대신 라운드트립 신호(K.6)로 대체한다.

흐름 (K.10):
  instruments.yaml 로드
    → fundamentals.fetch_all_indices (valuation_source 위상정렬 + PER 상속, K.4)
    → indices/{ID}/fundamentals.csv 멱등 append (K.3 컬럼)
    → 종목별 index.md 프롬프트 렌더 → grading.run_claude
    → 유형별 등급 (leveraged=QLD 라운드트립 신호)
    → grading.append_monthly(base_dir=ROOT/'indices') 월간 md
    → telegram_bot.send_message(target='index')
    → git 커밋(코드는 있으나 기본 비활성 — 실제 커밋은 사람이)

주식 로직은 건드리지 않는다 — 공용 유틸은 grading/daily_moat에서 import만 한다.
"""

import math
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fundamentals
import telegram_bot
from grading import (
    STRONG_GRADES,
    _norm_pick,
    _norm_valuation,
    append_monthly,
    apply_numeric_gates,
    load_calibration,
    run_claude,
    ticker_calibration,
)
# 파싱 헬퍼는 주식 트랙과 공유(모듈 import 시 부작용 없음 — main은 __main__ 가드).
from daily_moat import (
    SECTION_RE,
    _extract_field,
    _normalize_lines,
)


ROOT = Path(__file__).resolve().parents[2]
INSTRUMENTS_PATH = ROOT / "automation" / "instruments.yaml"
INDICES_DIR = ROOT / "indices"
PROMPT_PATH = ROOT / "automation" / "prompts" / "index.md"
TZ = "Asia/Seoul"

# 지수 트랙 CSV 컬럼 (K.3)
INDEX_CSV_HEADER = [
    "date", "price", "per", "dist_yield_ttm", "dist_yield_ann",
    "drop_from_high_pct", "ma50_gap_pct", "ma200_gap_pct", "currency", "source",
]

# 밸류 분위 판정에 필요한 최소 history 표본 (미만이면 '적정' 기본, K.5)
MIN_PER_HISTORY = 10


# ---------------------------------------------------------------------------
# 등급 매트릭스 (추세 × 밸류) — 지수/ETF 전용 (K.5)
#   주식의 GRADE_MATRIX(Moat질 × 밸류)와 라벨 체계(GRADE_NOTCHES)는 동일하게 재사용해
#   grading.apply_numeric_gates(낙폭 게이트)가 그대로 동작하도록 맞춘다.
# ---------------------------------------------------------------------------

GRADE_MATRIX_INDEX = {
    ("상승", "저평가"): "신규매수 적기",
    ("상승", "적정"): "매수 고려",
    ("상승", "고평가"): "관망",
    ("횡보", "저평가"): "매수 고려",
    ("횡보", "적정"): "관망",
    ("횡보", "고평가"): "관망",
    ("하락", "저평가"): "매수 고려",   # 지수 낙폭은 순환적 — cheap dip 매집 후보
    ("하락", "적정"): "관망",
    ("하락", "고평가"): "회피",
}


def _norm_trend(s):
    return _norm_pick(s, ("상승", "횡보", "하락"), "추세")


def compute_trend(ma200_gap, ma50_gap):
    """추세 축 산정 (K.5) — MA200 기준 상승/횡보/하락, MA50 보조.

    ma200_gap > +2% → 상승, < -2% → 하락, ±2% 근접 → 횡보(단 MA50로 편향 보조).
    MA200 데이터가 없으면 MA50만으로 판정. 둘 다 없으면 None(상위 폴백).
    """
    if ma200_gap is None:
        if ma50_gap is None:
            return None
        if ma50_gap > 2:
            return "상승"
        if ma50_gap < -2:
            return "하락"
        return "횡보"
    if ma200_gap > 2:
        return "상승"
    if ma200_gap < -2:
        return "하락"
    # MA200 ±2% 근접 → 횡보이되 MA50로 미세 편향
    if ma50_gap is not None:
        if ma50_gap > 1:
            return "상승"
        if ma50_gap < -1:
            return "하락"
    return "횡보"


def _percentile(sorted_vals, pct):
    """정렬된 리스트의 백분위(선형 보간)."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_vals[int(k)]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def compute_valuation_bucket(per, per_history, cal):
    """밸류 축 산정 (K.5) — PER를 자기 history 분위수와 비교.

    - 캘리브레이션(cal)에 per_reliable + per_cheap/per_rich가 있으면 그 임계값 우선.
    - 없으면 자기 history 분위(p33/p66): per ≤ p33 저평가 / per ≥ p66 고평가 / 그 외 적정.
    - PER가 None이거나 history 표본이 부족(<MIN_PER_HISTORY)하면 '적정' 기본(데이터 부족).
    """
    if per is None:
        return "적정"
    cal = cal or {}
    if cal.get("per_reliable"):
        pc = cal.get("per_cheap")
        pr = cal.get("per_rich")
        if pc is not None and per <= pc:
            return "저평가"
        if pr is not None and per >= pr:
            return "고평가"
        if pc is not None or pr is not None:
            return "적정"
    vals = sorted(v for v in (per_history or []) if v is not None)
    if len(vals) < MIN_PER_HISTORY:
        return "적정"  # 데이터 부족 → 기본 적정
    p33 = _percentile(vals, 33)
    p66 = _percentile(vals, 66)
    if p33 is not None and per <= p33:
        return "저평가"
    if p66 is not None and per >= p66:
        return "고평가"
    return "적정"


def grade_index(row, cal, per_history, parsed=None):
    """추세 × 밸류 매트릭스 등급 산정 후 낙폭 수치 게이트 적용.

    반환: (grade, trend, valuation_bucket).
    trend는 MA gap 기반. MA 데이터가 전무하면 LLM이 출력한 추세로 폴백.
    valuation은 항상 결정론적(history/cal) — LLM 폴백 없음(K.5 '적정' 기본).
    cal이 비어 있으면 apply_numeric_gates는 무변경(하위호환).
    """
    per = row.get("per")
    drop = row.get("drop_from_high_pct")

    trend = compute_trend(row.get("ma200_gap_pct"), row.get("ma50_gap_pct"))
    if trend is None and parsed:
        trend = _norm_trend(parsed.get("rec_trend") or parsed.get("trend") or "")

    val = compute_valuation_bucket(per, per_history, cal)

    if trend is None or val is None:
        # 축 미상 → 자본보존 폴백
        return "관망", trend, val

    grade = GRADE_MATRIX_INDEX.get((trend, val), "관망")
    grade = apply_numeric_gates(grade, per, drop, cal or {})
    return grade, trend, val


# ---------------------------------------------------------------------------
# QLD 라운드트립 신호 (K.6) — 유일한 매도 신호
#   진입: ATH 대비 -35% 알림, -40~-45 분할 / 손절: 진입가 -18% / 청산: 진입고점 회복 or MA50 상향
#   상태는 indices/QLD/state.yaml에 보존(라운드트립 추적).
# ---------------------------------------------------------------------------

QLD_ENTRY_DROP = -35.0     # ATH 대비 진입 알림 시작
QLD_SPLIT_DROP = -40.0     # -40~-45 분할 매수 구간
QLD_STOP_LOSS_PCT = -18.0  # 진입가 대비 손절선(존 -15~-20)


def _default_qld_state():
    return {
        "position": "none",   # none | holding
        "ath": None,          # 관측된 전고점(런 누적)
        "entry_price": None,
        "entry_ath": None,    # 진입 시점의 전고점(청산 회복선)
        "stop_price": None,
    }


def qld_signal(row, state, core_drop=None):
    """QLD 라운드트립 신호 (K.6).

    row: fetch_index_instrument 결과(price, ma50_gap_pct, drop_from_high_pct).
    state: 이전 indices/QLD/state.yaml(dict) 또는 None.
    core_drop: 코어 지수(QQQM) 고점대비 낙폭 — 동반 극단낙폭 가점 판단용.

    반환: (label, new_state, info)
      label ∈ {진입(극단낙폭), 보유, 청산(회복), 손절, 관망}
      info: {eff_drop, drop_ath, note} — 텔레그램/월간 md 표기용.
    """
    st = _default_qld_state()
    if state:
        st.update({k: state.get(k, st[k]) for k in st})

    price = row.get("price")
    ma50_gap = row.get("ma50_gap_pct")
    drop_52w = row.get("drop_from_high_pct")

    # 런 누적 전고점 유지(자기 시계열 기반).
    # 콜드 스타트에선 관측 ATH가 현재가와 같아 낙폭이 0으로 가려지므로,
    # drop_from_high_pct(52주 고점대비)로 역산한 함축 고점을 함께 반영한다.
    implied_high = None
    if price is not None and drop_52w is not None:
        denom = 1 + drop_52w / 100.0
        if denom > 0:
            implied_high = price / denom
    candidates = [v for v in (st.get("ath"), implied_high, price) if v is not None]
    ath = max(candidates) if candidates else None
    st["ath"] = round(ath, 4) if ath is not None else None

    drop_ath = None
    if price and ath and ath > 0:
        drop_ath = round((price / ath - 1) * 100, 2)
    eff_drop = drop_ath if drop_ath is not None else drop_52w

    note = ""
    position = st.get("position", "none")

    if position == "holding":
        entry_price = st.get("entry_price")
        entry_ath = st.get("entry_ath")
        stop_price = st.get("stop_price")

        # 손절: 손절가 이탈 or 진입가 대비 -18% 이상 추가 하락
        if entry_price and price is not None:
            loss_pct = (price / entry_price - 1) * 100
            hit_stop = (stop_price is not None and price <= stop_price) or (loss_pct <= QLD_STOP_LOSS_PCT)
            if hit_stop:
                note = f"진입가 대비 {round(loss_pct, 1)}% → 손절 실행(자본보존)"
                st.update(_default_qld_state())
                st["ath"] = ath
                return "손절", st, {"eff_drop": eff_drop, "drop_ath": drop_ath, "note": note}

        # 청산: 진입 시점 전고점 회복 or MA50 상향 돌파
        recovered_ath = entry_ath is not None and price is not None and price >= entry_ath
        broke_ma50 = ma50_gap is not None and ma50_gap > 0
        if recovered_ath or broke_ma50:
            reason = "진입 전고점 회복" if recovered_ath else "MA50(50일선) 상향 돌파"
            note = f"{reason} → 청산"
            st.update(_default_qld_state())
            st["ath"] = ath
            return "청산(회복)", st, {"eff_drop": eff_drop, "drop_ath": drop_ath, "note": note}

        note = "진입선~회복선 사이 — 보유 유지"
        return "보유", st, {"eff_drop": eff_drop, "drop_ath": drop_ath, "note": note}

    # position == none — 진입 여부 판단
    if eff_drop is not None and eff_drop <= QLD_ENTRY_DROP:
        note = f"ATH 대비 {eff_drop}% 극단낙폭 — 소액 진입"
        if eff_drop <= QLD_SPLIT_DROP:
            note += " · 분할 매수 구간(-40~-45)"
        if core_drop is not None and core_drop <= QLD_ENTRY_DROP:
            note += " · 코어 QQQM 동반 극단낙폭 가점"
        st.update(
            position="holding",
            entry_price=price,
            entry_ath=ath,
            stop_price=(round(price * (1 + QLD_STOP_LOSS_PCT / 100.0), 4) if price else None),
        )
        return "진입(극단낙폭)", st, {"eff_drop": eff_drop, "drop_ath": drop_ath, "note": note}

    note = "극단낙폭 아님 — 진입 대기(적립 아님)"
    return "관망", st, {"eff_drop": eff_drop, "drop_ath": drop_ath, "note": note}


# ---------------------------------------------------------------------------
# 프롬프트 출력 파싱 (index.md 출력 섹션)
# ---------------------------------------------------------------------------

def parse_index_output(text: str) -> dict:
    """index.md 출력 파싱 (K.10).

    섹션: 밸류 / 추세 / 매크로 / 호재 / 악재 / 매수 매력도(추세·밸류·유형·근거) / 종합평가.
    출처/References 트레일러는 잘라낸다.
    """
    import re
    m = re.search(r"\n+(Sources?|References?|출처|참고문헌)\s*:", text, flags=re.IGNORECASE)
    if m:
        text = text[: m.start()].rstrip() + "\n"

    sections: dict = {}
    for mm in SECTION_RE.finditer(text):
        sections[mm.group(1).strip()] = mm.group(2).strip()

    attract = sections.get("매수 매력도", "")
    return {
        "valuation": sections.get("밸류", ""),
        "trend": sections.get("추세", ""),
        "macro": sections.get("매크로", ""),
        "bullish": sections.get("호재", ""),
        "bearish": sections.get("악재", ""),
        "comment": sections.get("종합평가", ""),
        "rec_trend": _extract_field(attract, "추세"),
        "rec_valuation": _extract_field(attract, "밸류"),
        "rec_type": _extract_field(attract, "유형"),
        "rec_rationale": _extract_field(attract, "근거"),
        "raw": text,
    }


# ---------------------------------------------------------------------------
# 로더 / 렌더
# ---------------------------------------------------------------------------

def today_str(tz_name: str = TZ) -> str:
    return datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")


def load_instruments() -> list:
    """instruments.yaml 로드 → fetch_all_indices/프로필용 dict 리스트.

    각 항목에 `ticker`=id를 세팅(fundamentals._profile_ticker가 ticker 우선 사용,
    valuation_source도 id로 매칭되므로 KR 심볼(.KS)과 무관하게 상속이 동작).
    """
    data = yaml.safe_load(INSTRUMENTS_PATH.read_text(encoding="utf-8")) or {}
    out = []
    for inst in data.get("instruments", []) or []:
        d = dict(inst)
        d["ticker"] = inst.get("id") or inst.get("yf_symbol")
        out.append(d)
    return out


def load_index_profile(inst_id: str) -> dict:
    """indices/{ID}/profile.yaml 로드(name/notes 등 프롬프트 컨텍스트)."""
    p = INDICES_DIR / inst_id / "profile.yaml"
    if not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def format_index_fundamentals(row: dict) -> str:
    """프롬프트 주입용 1줄 펀더멘털 실값."""
    if not row:
        return "펀더멘털 N/A"

    def fmt(v, suffix=""):
        return f"{v}{suffix}" if v is not None else "N/A"

    src = "+".join(row.get("sources", []) or [])
    return (
        f"PER {fmt(row.get('per'))} / 분배율TTM {fmt(row.get('dist_yield_ttm'), '%')} / "
        f"분배율연환산 {fmt(row.get('dist_yield_ann'), '%')} / "
        f"고점대비 낙폭 {fmt(row.get('drop_from_high_pct'), '%')} / "
        f"MA50 gap {fmt(row.get('ma50_gap_pct'), '%')} / MA200 gap {fmt(row.get('ma200_gap_pct'), '%')} / "
        f"통화 {row.get('currency') or 'N/A'}"
        + (f" / 소스 {src}" if src else "")
    )


def render_index_prompt(template: str, inst: dict, profile: dict, fundamentals_str: str) -> str:
    name = profile.get("name") or inst.get("ticker") or inst.get("yf_symbol") or ""
    hedged = inst.get("hedged")
    hedged_s = "예" if hedged else "아니오"
    profile_notes = str(profile.get("notes") or "").strip() or "(프로필 메모 없음)"
    return (
        template
        .replace("{TICKER}", str(inst.get("ticker") or ""))
        .replace("{NAME}", str(name))
        .replace("{STRUCTURE}", str(inst.get("structure") or ""))
        .replace("{TRACKS}", str(inst.get("tracks") or ""))
        .replace("{CURRENCY}", str(inst.get("currency") or ""))
        .replace("{HEDGED}", hedged_s)
        .replace("{PROFILE}", profile_notes)
        .replace("{FUNDAMENTALS}", fundamentals_str)
    )


# ---------------------------------------------------------------------------
# CSV / state 영속
# ---------------------------------------------------------------------------

def append_index_csv(inst_id: str, date: str, row: dict):
    """지수 펀더멘털 1행을 indices/{ID}/fundamentals.csv에 멱등 append (K.3 컬럼).

    daily_moat.append_fundamentals_csv 패턴 재사용(같은 date 덮어씀, 순서 보존).
    price가 없으면(수집 완전 실패) 기록하지 않음(빈 행 오염 방지).
    반환: CSV 경로(Path) 또는 None.
    """
    import csv

    if row.get("price") is None:
        return None

    out = INDICES_DIR / inst_id / "fundamentals.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    def cell(key):
        v = row.get(key)
        return "" if v is None else v

    new_row = {
        "date": date,
        "price": cell("price"),
        "per": cell("per"),
        "dist_yield_ttm": cell("dist_yield_ttm"),
        "dist_yield_ann": cell("dist_yield_ann"),
        "drop_from_high_pct": cell("drop_from_high_pct"),
        "ma50_gap_pct": cell("ma50_gap_pct"),
        "ma200_gap_pct": cell("ma200_gap_pct"),
        "currency": cell("currency"),
        "source": "+".join(row.get("sources", []) or []),
    }

    rows_by_date: dict = {}
    order: list = []
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
        writer = csv.DictWriter(f, fieldnames=INDEX_CSV_HEADER)
        writer.writeheader()
        for d in order:
            writer.writerow({k: rows_by_date[d].get(k, "") for k in INDEX_CSV_HEADER})
    return out


def read_per_history(inst_id: str) -> list:
    """indices/{ID}/fundamentals.csv에서 과거 PER 값(float) 리스트."""
    import csv

    out = INDICES_DIR / inst_id / "fundamentals.csv"
    if not out.exists():
        return []
    vals = []
    try:
        with open(out, "r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                v = r.get("per")
                if v in (None, ""):
                    continue
                try:
                    vals.append(float(v))
                except (ValueError, TypeError):
                    continue
    except Exception:
        return []
    return vals


def _state_path(inst_id: str) -> Path:
    return INDICES_DIR / inst_id / "state.yaml"


def load_state(inst_id: str) -> dict:
    p = _state_path(inst_id)
    if not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def save_state(inst_id: str, state: dict) -> None:
    p = _state_path(inst_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# 텔레그램 메시지 빌더
# ---------------------------------------------------------------------------

# 액션 필요(요약 상단 승격) 등급 — 주식과 동일 STRONG_GRADES 재사용 + QLD 신호.
STRONG_GRADES_INDEX = set(STRONG_GRADES)
QLD_ACTION_LABELS = {"진입(극단낙폭)", "청산(회복)", "손절"}


def _is_flagged(r: dict) -> bool:
    if r.get("error"):
        return False
    if r.get("structure") == "leveraged":
        return r.get("grade") in QLD_ACTION_LABELS
    return r.get("grade") in STRONG_GRADES_INDEX


def _structure_rank(structure: str) -> int:
    """메시지 정렬 순서: 순수지수/배당 → 레버리지 → 커버드콜."""
    return {"tracker": 0, "dividend": 0, "leveraged": 1, "covered_call": 2}.get(structure, 3)


def _index_metrics_line(row: dict) -> str:
    """요약 카드용 💰 주요 지표 1줄(간결). 판단(💬)보다 먼저 표시."""
    if not row:
        return ""

    def fmt(v, suffix=""):
        return f"{v}{suffix}" if v is not None else "N/A"

    parts = [
        f"PER {fmt(row.get('per'))}",
        f"낙폭 {fmt(row.get('drop_from_high_pct'), '%')}",
        f"MA200 {fmt(row.get('ma200_gap_pct'), '%')}",
    ]
    dist = row.get("dist_yield_ttm")
    if dist:  # 분배율 있는 종목(배당/커버드콜)만
        parts.append(f"분배 {fmt(dist, '%')}")
    cur = row.get("currency")
    if cur and cur != "USD":
        parts.append(cur)
    return "💰 " + " · ".join(parts)


def build_index_summary(date: str, results: list, chunk_size: int = 5) -> list:
    """Index Daily 요약. 종목마다 💰 주요 지표 → 💬 판단(등급+종합평가)을 표시(주식 moat 밀도).

    액션 종목([!], QLD 신호/강한 등급)을 상단으로 정렬하고 chunk_size개씩 메시지 분할.
    """
    ok = [r for r in results if not r.get("error")]
    errored = [r for r in results if r.get("error")]
    # 유형 순: 순수지수/배당 → 레버리지 → 커버드콜, 그룹 내 액션 종목 먼저
    ok.sort(key=lambda r: (_structure_rank(r.get("structure")), 0 if _is_flagged(r) else 1))

    msgs: list = []
    total = max(1, (len(ok) + chunk_size - 1) // chunk_size)
    for i in range(0, len(ok), chunk_size):
        chunk = ok[i:i + chunk_size]
        idx = i // chunk_size + 1
        suffix = f" ({idx}/{total})" if total > 1 else ""
        lines = [f"Index Daily — {date}{suffix}", ""]
        for r in chunk:
            mark = "[!] " if _is_flagged(r) else ""
            nm = r.get("name")
            head = r["ticker"] if not nm or nm == r["ticker"] else f"{nm} ({r['ticker']})"
            lines.append(f"{mark}{head} · {r.get('grade', '')}")
            metrics = _index_metrics_line(r.get("row") or {})
            if metrics:
                lines.append(f"  {metrics}")
            if r.get("structure") == "leveraged":
                info = r.get("qld_info") or {}
                if info.get("note"):
                    lines.append(f"  · {info['note']}")
            comment = (r.get("parsed", {}) or {}).get("comment", "").strip()
            if comment:
                lines.append(f"  💬 {comment}")
            lines.append("")
        if idx == total and errored:
            lines.append("⚠️ 분석 실패: " + ", ".join(r["ticker"] for r in errored))
        msgs.append("\n".join(lines).strip() + "\n")

    if not ok:  # 전부 실패한 예외 케이스
        body = "⚠️ 분석 실패: " + ", ".join(r["ticker"] for r in errored) if errored else "(결과 없음)"
        msgs = [f"Index Daily — {date}\n\n{body}\n"]
    return msgs


def build_index_detail(date: str, r: dict) -> str:
    """[!] 종목 상세 메시지 — 밸류/추세/매크로/종합 요약."""
    parsed = r.get("parsed", {}) or {}
    lines = [f"━━ {r['ticker']} — {date} ━━", f"{r.get('grade', '')}", ""]

    if r.get("structure") == "leveraged":
        info = r.get("qld_info") or {}
        if info.get("note"):
            lines.append(info["note"])
            lines.append("")

    for label, key in (("밸류", "valuation"), ("추세", "trend"), ("매크로", "macro")):
        block = parsed.get(key, "").strip()
        if block:
            one = " / ".join(_normalize_lines(block)[:3])
            lines.append(f"{label}: {one}")

    comment = parsed.get("comment", "").strip()
    if comment:
        lines.append("")
        lines.append(f"종합평가: {comment}")

    return "\n".join(lines).strip() + "\n"


# ---------------------------------------------------------------------------
# git (코드는 두되 기본 비활성 — 실제 커밋은 사람이. K Step C)
# ---------------------------------------------------------------------------

def git_commit(date: str, paths: list) -> None:
    """지수 트랙 산출물 커밋. main에서는 기본 호출 안 함(INDEX_AUTOCOMMIT=1일 때만)."""
    if not paths:
        return
    rel = [str(Path(p).relative_to(ROOT)) for p in paths]
    try:
        subprocess.run(["git", "add", *rel], cwd=str(ROOT), check=True)
        status = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(ROOT), capture_output=True, text=True, check=True,
        )
        if not status.stdout.strip():
            print("[index_daily] no staged changes, skip commit", file=sys.stderr)
            return
        msg = f"index daily: {date} 자동 분석 기록"
        subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT), check=True)
    except subprocess.CalledProcessError as e:
        print(f"[index_daily] git commit 실패: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    date = today_str(TZ)
    instruments = load_instruments()
    calibration = load_calibration()

    # 1) 수집 (valuation_source 위상정렬 + PER 상속) — K.4
    try:
        rows = fundamentals.fetch_all_indices(instruments)
    except Exception as e:
        telegram_bot.send_message(f"⚠️ index 펀더멘털 수집 실패 ({e})", target="index")
        print(f"[index_daily] fetch_all_indices 실패: {e}", file=sys.stderr)
        return 1
    row_by_id = {r.get("ticker"): r for r in rows}

    saved_paths: list = []

    # 2) CSV 멱등 append (K.3)
    for r in rows:
        try:
            p = append_index_csv(r.get("ticker"), date, r)
            if p and p not in saved_paths:
                saved_paths.append(p)
        except Exception as e:
            print(f"[index_daily] csv append 실패 {r.get('ticker')}: {e}", file=sys.stderr)

    # 3) 프롬프트 템플릿
    template = PROMPT_PATH.read_text(encoding="utf-8")

    results = []
    for inst in instruments:
        inst_id = inst.get("ticker")
        structure = inst.get("structure")
        row = row_by_id.get(inst_id) or {}
        profile = load_index_profile(inst_id)
        cal = ticker_calibration(calibration, inst_id)

        fundamentals_str = format_index_fundamentals(row)
        prompt = render_index_prompt(template, inst, profile, fundamentals_str)

        try:
            raw = run_claude(prompt)
        except Exception as e:
            print(f"[index_daily] {inst_id}: claude 실행 실패: {e}", file=sys.stderr)
            results.append({"ticker": inst_id, "structure": structure, "error": str(e)})
            continue

        parsed = parse_index_output(raw)

        qld_info = None
        if structure == "leveraged":
            state = load_state(inst_id)
            core_id = inst.get("valuation_source")
            core_drop = (row_by_id.get(core_id) or {}).get("drop_from_high_pct")
            grade, new_state, qld_info = qld_signal(row, state, core_drop)
            try:
                save_state(inst_id, new_state)
            except Exception as e:
                print(f"[index_daily] {inst_id}: state 저장 실패: {e}", file=sys.stderr)
            trend = None
            val = None
        else:
            per_history = read_per_history(inst_id)
            grade, trend, val = grade_index(row, cal, per_history, parsed)

        try:
            path = append_monthly(inst_id, date, raw, grade, base_dir=INDICES_DIR)
            if path not in saved_paths:
                saved_paths.append(path)
        except Exception as e:
            print(f"[index_daily] {inst_id}: 월간 md append 실패: {e}", file=sys.stderr)

        results.append({
            "ticker": inst_id,
            "name": profile.get("name"),
            "structure": structure,
            "parsed": parsed,
            "grade": grade,
            "trend": trend,
            "valuation": val,
            "qld_info": qld_info,
            "row": row,
        })

    # 4) 텔레그램 (target='index')
    for msg in build_index_summary(date, results):
        telegram_bot.send_message(msg, target="index")
    for r in results:
        if _is_flagged(r):
            telegram_bot.send_message(build_index_detail(date, r), target="index")

    # 5) git 커밋 — 기본 비활성(실제 커밋은 사람이). INDEX_AUTOCOMMIT=1이면 자동.
    if os.environ.get("INDEX_AUTOCOMMIT") == "1":
        git_commit(date, saved_paths)
    else:
        print(
            f"[index_daily] 자동 커밋 비활성 — 산출물 {len(saved_paths)}건은 사람이 커밋 "
            f"(INDEX_AUTOCOMMIT=1로 활성화 가능)",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
