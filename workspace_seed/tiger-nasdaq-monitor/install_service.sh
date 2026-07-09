#!/usr/bin/env bash
set -euo pipefail

ROOT="/workspaces/Agent-Build-and-Evaluation-Practice"
SERVICE_SRC="$ROOT/workspace/skills/tiger-nasdaq-monitor/tiger_monitor.service"
SERVICE_DEST="/etc/systemd/system/tiger_monitor.service"

if [ ! -f "$SERVICE_SRC" ]; then
  echo "서비스 파일이 없습니다: $SERVICE_SRC"
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl 이 설치되어 있지 않습니다."
  exit 2
fi

if ! systemctl is-system-running >/dev/null 2>&1; then
  echo "현재 환경에서는 systemd가 실행 중이지 않아 서비스 등록을 완료할 수 없습니다."
  exit 3
fi

sudo install -m 0644 "$SERVICE_SRC" "$SERVICE_DEST"
sudo systemctl daemon-reload
sudo systemctl enable --now tiger_monitor.service
sudo systemctl status tiger_monitor.service --no-pager
