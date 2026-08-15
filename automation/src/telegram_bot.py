import os
import sys
import time
from typing import Optional

import requests


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4096


def load_config(target: str = "moat") -> dict:
    if target == "moat":
        token = os.environ.get("MOAT_TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("MOAT_TELEGRAM_CHAT_ID")
        missing = [
            k for k, v in (
                ("MOAT_TELEGRAM_BOT_TOKEN", token),
                ("MOAT_TELEGRAM_CHAT_ID", chat_id),
            ) if not v
        ]
        if missing:
            raise RuntimeError(
                f"환경변수 누락: {', '.join(missing)}. "
                f".env 파일에 설정 후 source .env 또는 cron wrapper에서 로드해주세요."
            )
        return {"token": token, "chat_id": chat_id}

    if target == "index":
        # 토큰: index 전용 미설정 시 moat 봇 토큰으로 폴백. chat_id는 반드시 index 것 사용.
        token = os.environ.get("MOAT_INDEX_TELEGRAM_BOT_TOKEN") or os.environ.get("MOAT_TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("MOAT_INDEX_TELEGRAM_CHAT_ID")
        missing = []
        if not token:
            missing.append("MOAT_INDEX_TELEGRAM_BOT_TOKEN(또는 폴백용 MOAT_TELEGRAM_BOT_TOKEN)")
        if not chat_id:
            missing.append("MOAT_INDEX_TELEGRAM_CHAT_ID")
        if missing:
            raise RuntimeError(
                f"환경변수 누락: {', '.join(missing)}. "
                f".env 파일에 설정 후 source .env 또는 cron wrapper에서 로드해주세요."
            )
        return {"token": token, "chat_id": chat_id}

    if target == "alert":
        # 트리거 경보 전용 채널(@drop_trigger_alert_bot). 지수·개별주 등 모든 트리거가 여기로 모인다.
        # 토큰: 전용 미설정 시 moat 봇 토큰으로 폴백. chat_id는 반드시 alert 것 사용.
        token = os.environ.get("MOAT_ALERT_TELEGRAM_BOT_TOKEN") or os.environ.get("MOAT_TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("MOAT_ALERT_TELEGRAM_CHAT_ID")
        missing = []
        if not token:
            missing.append("MOAT_ALERT_TELEGRAM_BOT_TOKEN(또는 폴백용 MOAT_TELEGRAM_BOT_TOKEN)")
        if not chat_id:
            missing.append("MOAT_ALERT_TELEGRAM_CHAT_ID")
        if missing:
            raise RuntimeError(
                f"환경변수 누락: {', '.join(missing)}. "
                f".env 파일에 설정 후 source .env 또는 cron wrapper에서 로드해주세요."
            )
        return {"token": token, "chat_id": chat_id}

    raise RuntimeError(f"알 수 없는 target: {target!r} (moat|index|alert 중 하나여야 함)")


def _split_message(text: str, limit: int = MAX_LEN) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")
    if remaining:
        parts.append(remaining)
    return parts


def send_message(text: str, parse_mode: Optional[str] = None, target: str = "moat") -> bool:
    try:
        cfg = load_config(target)
    except RuntimeError as e:
        print(f"[telegram_bot] {e}", file=sys.stderr)
        return False

    url = TELEGRAM_API.format(token=cfg["token"])
    ok = True
    for chunk in _split_message(text):
        try:
            payload = {"chat_id": cfg["chat_id"], "text": chunk, "disable_web_page_preview": True}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            resp = requests.post(
                url,
                data=payload,
                timeout=15,
            )
            if resp.status_code != 200:
                print(f"[telegram_bot] send failed: {resp.status_code} {resp.text}", file=sys.stderr)
                ok = False
        except requests.RequestException as e:
            print(f"[telegram_bot] request error: {e}", file=sys.stderr)
            ok = False
        time.sleep(0.3)
    return ok


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "moat-journal telegram_bot 테스트 메시지"
    success = send_message(msg)
    sys.exit(0 if success else 1)
