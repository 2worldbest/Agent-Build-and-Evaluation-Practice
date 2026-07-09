# TIGER 미국나스닥 100 모니터링

## 안정적인 실행 방식

이 모니터링은 다음 두 가지 방식으로 운영할 수 있습니다.

1. 개발/테스트용: `python3 workspace/skills/tiger-nasdaq-monitor/manage_tiger_monitor.py`
2. 안정적인 운영용: systemd 서비스

## systemd 서비스 등록

```bash
sudo cp workspace/skills/tiger-nasdaq-monitor/tiger_monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tiger_monitor.service
sudo systemctl status tiger_monitor.service
```

## 로그 확인

```bash
sudo journalctl -u tiger_monitor.service -f
```

## 실행 중단

```bash
sudo systemctl stop tiger_monitor.service
```

## 텔레그램 봇 설정 검증

텔레그램 봇 토큰으로 알림 전송이 가능한지 확인하려면 다음을 실행합니다.

```bash
python3 workspace/skills/tiger-nasdaq-monitor/verify_telegram_config.py
```

이 스크립트는 `.env`의 텔레그램 관련 값을 읽어 누락된 항목이 있는지 확인하고, 설정이 완료되면 봇 API 연결까지 검증합니다.
