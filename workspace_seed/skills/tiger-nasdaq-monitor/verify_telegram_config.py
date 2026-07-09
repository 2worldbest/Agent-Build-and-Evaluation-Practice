#!/usr/bin/env python3
"""텔레그램 봇 설정 검증 스크립트.

.env 또는 환경변수에서 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 를 읽어 검증한다.
"""

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / ".env"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    load_dotenv(ENV_PATH)

    required = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("다음 설정이 필요합니다:")
        for name in missing:
            print(f"- {name}")
        print("\n.env 파일에 실제 값을 입력한 뒤 다시 실행하세요.")
        sys.exit(1)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/getMe"

    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="GET")
        with urlopen(request, timeout=15) as response:
            payload = json.load(response)
        if payload.get("ok"):
            print("텔레그램 봇 인증 성공")
            print(f"chat_id={chat_id}")
        else:
            print(f"텔레그램 봇 인증 실패: {payload}")
            sys.exit(2)
    except Exception as exc:
        print(f"텔레그램 API 호출 실패: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()
