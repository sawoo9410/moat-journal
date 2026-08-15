#!/usr/bin/env python3
"""낙폭 트리거 — 전월 말 거래일 종가 대비 -3/-5/-7/-10% 하향 돌파 시 텔레그램 경보.

- 대상: 순수 지수/배당 트래커만(structure=tracker|dividend). 커버드콜·레버리지 제외(규칙 별도).
- 기준: 전월 마지막 거래일 종가. 현재가는 fast_info 최신값(15:15 KST 실행 시 KR은 라이브, US는 전일 종가).
- de-dup: 이번 달에 이미 알린 임계보다 더 깊어질 때만 1회 알림. 매달 초 리셋. state=indices/trigger_state.yaml.
- 07:00 index_daily(매수권장)와 분리된 별도 잡(15:15 KST). LLM 미사용 — 빠르고 저렴.

사용:
    python automation/src/index_trigger.py            # 판정 + 신규 돌파 시 전송 + state 갱신
    python automation/src/index_trigger.py --dry      # 전 종목 낙폭 출력만, 전송/저장 안 함
"""
import sys
from datetime import datetime
from pathlib import Path
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
    """(전월 말 거래일 종가, 현재가) 반환. 실패 시 (None, None)."""
    tk = yf.Ticker(yf_symbol)
    try:
        hist = tk.history(period="3mo")
    except Exception:
        return None, None
    if hist is None or hist.empty:
        return None, None
    first_of_month = now.date().replace(day=1)
    prev = hist[[d.date() < first_of_month for d in hist.index]]
    if prev.empty:
        return None, None
    prev_close = float(prev["Close"].iloc[-1])
    # 현재가: fast_info 최신 → 실패 시 히스토리 마지막 종가
    cur = None
    try:
        cur = float(tk.fast_info["last_price"])
    except Exception:
        cur = None
    if not cur:
        cur = float(hist["Close"].iloc[-1])
    return prev_close, cur


def deepest_breached(drop):
    """drop(음수)이 돌파한 가장 깊은 임계. 없으면 None."""
    br = [t for t in THRESHOLDS if drop <= t]
    return min(br) if br else None


def main() -> int:
    dry = "--dry" in sys.argv
    now = datetime.now(ZoneInfo(TZ))
    month_key = now.strftime("%Y-%m")

    state = load_state()
    if state.get("month") != month_key:   # 매달 리셋
        state = {"month": month_key, "alerted": {}}
    alerted = state.setdefault("alerted", {})

    insts = [i for i in load_instruments() if i.get("structure") in TRIGGER_STRUCTURES]
    fired = []   # (rank, drop, id, name, level)
    for inst in insts:
        iid = inst.get("id") or inst.get("ticker")
        prof = load_profile(iid)
        prev_close, cur = prev_month_end_and_price(inst.get("yf_symbol", iid), now)
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
            fired.append((drop, iid, name, level))
            alerted[iid] = level

    if dry:
        return 0

    if fired:
        fired.sort(key=lambda x: x[0])   # 낙폭 깊은 순
        lines = ["⚠️ 낙폭 트리거 — 전월말 대비", ""]
        for drop, iid, name, level in fired:
            lines.append(f"{name} ({iid})  {drop*100:+.1f}% · 트리거 {int(level*100)}%")
        telegram_bot.send_message("\n".join(lines), target="index")
        print(f"[trigger] {len(fired)}건 알림 전송")
        save_state(state)
    else:
        print("[trigger] 신규 돌파 없음")
        save_state(state)   # 월 리셋 반영 위해 저장
    return 0


if __name__ == "__main__":
    sys.exit(main())
