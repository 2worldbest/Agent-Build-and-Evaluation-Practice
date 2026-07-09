#!/usr/bin/env python3
"""SMTP 메일 설정 검증 스크립트.

.env 또는 환경변수에서 SMTP 설정을 읽어, 필수값 누락 여부와 SMTP 연결/로그인 가능 여부를 확인한다.
"""

import os
import smtplib
import sys
from pathlib import Path

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

    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "ALERT_TO_EMAIL"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("다음 설정이 필요합니다:")
        for name in missing:
            print(f"- {name}")
        print("\n.env 파일에 실제 값을 입력한 뒤 다시 실행하세요.")
        sys.exit(1)

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    to_addr = os.getenv("ALERT_TO_EMAIL")

    print(f"SMTP_HOST={host}")
    print(f"SMTP_PORT={port}")
    print(f"SMTP_USER={user}")
    print(f"ALERT_TO_EMAIL={to_addr}")

    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            print("SMTP 연결 및 로그인 성공")
    except Exception as exc:
        print(f"SMTP 연결/로그인 실패: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()
