#!/usr/bin/env python3
"""낙폭 트리거 — 전월 말 거래일 종가 대비 -3/-5/-7/-10% 하향 돌파 시 텔레그램 경보.

- 대상: 순수 지수/배당 트래커만(structure=tracker|dividend). 커버드콜·레버리지 제외(규칙 별도).
- 기준: 전월 마지막 거래일 종가. 현재가는 fast_info 최신값(15:15 KST 실행 시 KR은 라이브, US는 전일 종가).
- de-dup: 이번 달에 이미 알린 임계보다 더 깊어질 때만 1회 알림. 매달 초 리셋. state=indices/trigger_state.yaml.
- 07:00 index_daily(매수권장)와 분리된 별도 잡(15:15 KST).
- 전송: target="alert" (경보 전용 채팅 @drop_trigger_alert_bot). 개별주 등 향후 트리거도 같은 방으로
  모으고, 헤더 "⚠️ {종류} · {대상}" 으로 출처를 구분한다.
- 메시지는 **종목당 하나씩** 따로 전송하고, 전월말 종가 → 현재가와 하락 사유 한 줄을 담는다.
- LLM은 돌파가 있을 때만, 그것도 tracks(벤치마크)당 1회만 호출한다. 같은 지수를 추종하는
  ETF는 하락 원인이 동일하므로 사유를 공유한다(8종목 동시 돌파여도 호출은 최대 3회).
  사유 생성이 실패해도 가격 정보만으로 경보는 그대로 나간다.

사용:
    python automation/src/index_trigger.py            # 판정 + 신규 돌파 시 전송 + state 갱신
    python automation/src/index_trigger.py --dry      # 전 종목 낙폭 출력만, 전송/저장 안 함
"""
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from zoneinfo import ZoneInfo

import yaml
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import telegram_bot

ROOT = Path(__file__).resolve().parents[2]
INSTRUMENTS = ROOT / "automation" / "instruments.yaml"
STATE_PATH = ROOT / "indices" / "trigger_state.yaml"
TZ = "Asia/Seoul"

THRESHOLDS = [-0.03, -0.05, -0.07, -0.10]   # 하향 돌파 임계(음수)
TRIGGER_STRUCTURES = {"tracker", "dividend"}

ALERT_HEADER = "⚠️ 낙폭 · 지수"   # "⚠️ {종류} · {대상}" 포맷 — 경보 채널에 여러 트리거가 섞이므로 출처 표기

# 하락 사유 LLM 호출은 tracks(벤치마크) 단위로 1회만 — 같은 지수를 추종하는 ETF는 원인이 동일하다.
TRACKS_LABEL = {
    "SP500": "S&P500",
    "NDX100": "나스닥100",
    "US_DIV_DJ100": "미국 배당주(Dow Jones U.S. Dividend 100)",
}

REASON_PROMPT = """{label}을(를) 추종하는 ETF가 {prev_date} 종가 대비 {drop:.1f}% 하락했다. 오늘은 {today}다.

이 하락률은 실제 시세 데이터로 계산된 확정값이다. 반박하거나 되묻지 말고 사실로 전제하라.

웹 검색으로 이 기간 하락의 주된 원인을 파악해 한국어 한 문장으로만 답하라.

규칙:
- 출처·링크·뉴스 제목·기관명 인용을 쓰지 말 것
- 정확히 한 문장, 80자 이내
- 원인만 서술 (예: "고용지표 부진에 금리 인하 기대가 후퇴하며 조정")
- 원인을 특정하지 못하면 "뚜렷한 단일 원인 없이 전반적 조정"이라고만 답하라
- 서론·설명·마크다운 없이 위 두 형식 중 하나의 한 문장만 출력하라"""


def load_instruments() -> list:
    data = yaml.safe_load(INSTRUMENTS.read_text(encoding="utf-8")) or {}
    return data.get("instruments", []) if isinstance(data, dict) else (data or [])


def load_profile(inst_id: str) -> dict:
    p = ROOT / "indices" / inst_id / "profile.yaml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def load_state() -> dict:
    if STATE_PATH.exists():
        return yaml.safe_load(STATE_PATH.read_text(encoding="utf-8")) or {}
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def prev_month_end_and_price(yf_symbol: str, now: datetime):
    """(전월 말 거래일 날짜, 그 종가, 현재가) 반환. 실패 시 (None, None, None)."""
    tk = yf.Ticker(yf_symbol)
    try:
        hist = tk.history(period="3mo")
    except Exception:
        return None, None, None
    if hist is None or hist.empty:
        return None, None, None
    first_of_month = now.date().replace(day=1)
    prev = hist[[d.date() < first_of_month for d in hist.index]]
    if prev.empty:
        return None, None, None
    prev_date = prev.index[-1].date()
    prev_close = float(prev["Close"].iloc[-1])
    # 현재가: fast_info 최신 → 실패 시 히스토리 마지막 종가
    cur = None
    try:
        cur = float(tk.fast_info["last_price"])
    except Exception:
        cur = None
    if not cur:
        cur = float(hist["Close"].iloc[-1])
    return prev_date, prev_close, cur


def deepest_breached(drop):
    """drop(음수)이 돌파한 가장 깊은 임계. 없으면 None."""
    br = [t for t in THRESHOLDS if drop <= t]
    return min(br) if br else None


def fmt_price(v: float, currency: str) -> str:
    return f"{v:,.0f}" if currency == "KRW" else f"{v:,.2f}"


def currency_note(inst: dict) -> str:
    """원화 상품의 낙폭 해석 주석. 달러 상품은 주석 없음."""
    if inst.get("currency") != "KRW":
        return "USD"
    return "KRW 환헤지(지수+헤지비용)" if inst.get("hedged") else "KRW 환노출(지수±환)"


def fetch_reason(tracks: str, drop: float, prev_date, now: datetime) -> Optional[str]:
    """tracks(벤치마크) 단위 하락 사유 한 줄. 실패 시 None — 경보 자체는 사유 없이도 나간다."""
    from grading import run_claude

    prompt = REASON_PROMPT.format(
        label=TRACKS_LABEL.get(tracks, tracks),
        prev_date=prev_date.strftime("%Y-%m-%d"),
        drop=drop * 100,
        today=now.strftime("%Y-%m-%d"),
    )
    try:
        raw = run_claude(prompt)
    except Exception as e:
        print(f"[trigger] 사유 생성 실패({tracks}): {e}", file=sys.stderr)
        return None
    line = next((ln.strip() for ln in raw.strip().splitlines() if ln.strip()), "")
    line = line.lstrip("-*> ").strip().strip('"').strip("'")
    return line[:120] or None


def build_message(hit: dict, reason: Optional[str]) -> str:
    lines = [
        ALERT_HEADER,
        "━━━━━━━━━━━━━━━━",
        f"  {hit['name']} ({hit['id']})",
        f"  트리거 {int(hit['level'] * 100)}% 돌파",
        "━━━━━━━━━━━━━━━━",
        "",
        f"📉 {fmt_price(hit['prev_close'], hit['currency'])} → {fmt_price(hit['cur'], hit['currency'])}"
        f"  ({hit['drop'] * 100:+.1f}%)",
        f"   {hit['prev_date']:%-m/%-d} 종가 대비 · {hit['note']}",
    ]
    if reason:
        lines += ["", f"💬 {reason}"]
    return "\n".join(lines)


def main() -> int:
    dry = "--dry" in sys.argv
    now = datetime.now(ZoneInfo(TZ))
    month_key = now.strftime("%Y-%m")

    state = load_state()
    if state.get("month") != month_key:   # 매달 리셋
        state = {"month": month_key, "alerted": {}}
    alerted = state.setdefault("alerted", {})

    insts = [i for i in load_instruments() if i.get("structure") in TRIGGER_STRUCTURES]
    fired = []   # dict 목록 — 종목당 개별 메시지로 전송
    for inst in insts:
        iid = inst.get("id") or inst.get("ticker")
        prof = load_profile(iid)
        prev_date, prev_close, cur = prev_month_end_and_price(inst.get("yf_symbol", iid), now)
        if not prev_close or not cur:
            print(f"[trigger] {iid}: 가격 조회 실패", file=sys.stderr)
            continue
        drop = cur / prev_close - 1.0
        level = deepest_breached(drop)
        name = prof.get("name") or iid
        if dry:
            print(f"  {name} ({iid}): 전월말 {prev_close:.2f} → 현재 {cur:.2f} = {drop*100:+.2f}% "
                  f"| 돌파 {int(level*100) if level else '-'}%")
            continue
        if level is None:
            continue
        prev_level = alerted.get(iid)   # 이번 달 이미 알린 최심 임계(음수) 또는 None
        if prev_level is None or level < prev_level:   # 더 깊어졌을 때만
            fired.append({
                "id": iid, "name": name, "drop": drop, "level": level,
                "prev_date": prev_date, "prev_close": prev_close, "cur": cur,
                "currency": inst.get("currency", "USD"),
                "note": currency_note(inst),
                "tracks": inst.get("tracks") or "",
            })
            alerted[iid] = level

    if dry:
        return 0

    if not fired:
        print("[trigger] 신규 돌파 없음")
        save_state(state)   # 월 리셋 반영 위해 저장
        return 0

    fired.sort(key=lambda h: h["drop"])   # 낙폭 깊은 순

    # 사유는 벤치마크(tracks)당 1회만 생성해 같은 지수 추종 종목끼리 공유 — LLM 호출 최소화
    reasons: Dict[str, Optional[str]] = {}
    for hit in fired:
        tk = hit["tracks"]
        if tk not in reasons:
            reasons[tk] = fetch_reason(tk, hit["drop"], hit["prev_date"], now)

    for hit in fired:
        ok = telegram_bot.send_message(build_message(hit, reasons.get(hit["tracks"])), target="alert")
        print(f"[trigger] {hit['id']} 전송 {'성공' if ok else '실패'} ({hit['drop']*100:+.1f}%)")

    print(f"[trigger] {len(fired)}건 알림 전송 (사유 {len(reasons)}회 생성)")
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
