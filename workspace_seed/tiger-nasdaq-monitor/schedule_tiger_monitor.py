#!/usr/bin/env python3
"""TIGER 미국나스닥 100 모니터링 스케줄러.

매일 영업일 오전 10시, 오후 3시에 주가 조회 및 알림을 실행한다.
주말/공휴일에는 실행하지 않는다.
"""

import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "workspace" / "skills" / "tiger-nasdaq-monitor" / "manage_tiger_monitor.py"
KOREA_HOLIDAYS = {
    "0101", "0301", "0505", "0606", "0815", "1003", "1009", "1225",
}


def is_weekend_or_holiday(now: Optional[datetime] = None) -> bool:
    if now is None:
        now = datetime.now()

    if now.weekday() >= 5:
        return True

    today_str = now.strftime("%m%d")
    if today_str in KOREA_HOLIDAYS:
        return True

    return False


def should_run(now: Optional[datetime] = None) -> bool:
    if now is None:
        now = datetime.now()

    if is_weekend_or_holiday(now):
        return False

    return now.hour in {10, 15} and now.minute in {0}


def run_once() -> None:
    if not SCRIPT.exists():
        raise FileNotFoundError(f"모니터링 스크립트가 없습니다: {SCRIPT}")

    command = [sys.executable, str(SCRIPT), "--symbol", "133690", "--threshold", "5.0", "--force-send"]
    completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)
    print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"모니터링 스크립트가 실패했습니다. exit={completed.returncode}")


def main() -> None:
    print("TIGER 모니터링 스케줄러 시작")
    while True:
        now = datetime.now()
        if should_run(now):
            print(f"[{now}] 실행")
            run_once()
            time.sleep(70)
        else:
            time.sleep(30)


if __name__ == "__main__":
    main()
