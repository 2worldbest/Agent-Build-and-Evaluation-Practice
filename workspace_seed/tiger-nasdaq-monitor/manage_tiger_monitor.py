#!/usr/bin/env python3
"""TIGER 미국나스닥 100 모니터링용 스크립트.

실시간 주가 조회는 Yahoo Finance chart API 를 사용한다.
한국 증권 코드인 133690 은 Yahoo 쿼리에서 133690.KS 로 자동 변환한다.
"""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_SYMBOL = "133690"
DEFAULT_NAME = "TIGER 미국나스닥 100"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "tiger_monitor_result.json"
DEFAULT_API_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
DEFAULT_API_TIMEOUT = 10
ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / ".env"


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_dotenv()


def _load_env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, default)


def resolve_symbol(symbol: str) -> str:
    symbol = (symbol or "").strip()
    if not symbol:
        return symbol
    if symbol.isdigit() and len(symbol) == 6:
        return f"{symbol}.KS"
    return symbol


def fetch_yahoo_chart(symbol: str, base_url: str = DEFAULT_API_BASE_URL, timeout: int = DEFAULT_API_TIMEOUT) -> dict:
    resolved_symbol = resolve_symbol(symbol)
    url = f"{base_url.rstrip('/')}/{resolved_symbol}?interval=1d&range=2mo"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def parse_yahoo_payload(payload: dict) -> dict:
    chart = payload.get("chart", {})
    error = chart.get("error")
    if error:
        raise RuntimeError(f"Yahoo API error: {error}")

    results = chart.get("result") or []
    if not results:
        raise RuntimeError("주가 데이터를 받지 못했습니다.")

    first_result = results[0]
    meta = first_result.get("meta", {})
    indicators = first_result.get("indicators", {})
    quotes = indicators.get("quote", [{}]) or [{}]
    quote = quotes[0]
    closes = [float(value) for value in quote.get("close", []) if value is not None]
    if not closes:
        raise RuntimeError("종가 데이터가 없습니다.")

    price = meta.get("regularMarketPrice")
    if price is None:
        price = closes[-1]

    previous_close = meta.get("previousClose")
    if previous_close is None and len(closes) >= 2:
        previous_close = closes[-2]

    window = closes[-20:]
    ma20 = sum(window) / len(window) if window else None

    return {
        "symbol": meta.get("symbol"),
        "name": DEFAULT_NAME,
        "price": price,
        "previous_close": previous_close,
        "ma20": ma20,
        "source": "yahoo-finance-chart",
    }


def _get_price_snapshot(symbol: str, base_url: str = DEFAULT_API_BASE_URL, timeout: int = DEFAULT_API_TIMEOUT) -> dict:
    resolved_symbol = resolve_symbol(symbol)
    try:
        payload = fetch_yahoo_chart(resolved_symbol, base_url=base_url, timeout=timeout)
        snapshot = parse_yahoo_payload(payload)
        snapshot["symbol"] = resolved_symbol
        snapshot["name"] = DEFAULT_NAME
        return snapshot
    except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
        return {
            "symbol": resolved_symbol,
            "name": DEFAULT_NAME,
            "price": None,
            "previous_close": None,
            "ma20": None,
            "source": "yahoo-finance-chart",
            "error": str(exc),
        }


def _calculate_diff(price: float, base_price: float) -> float:
    if base_price in (None, 0):
        return 0.0
    return ((price - base_price) / base_price) * 100


def should_send_notification(diff_vs_prev: Optional[float], diff_vs_ma20: Optional[float], threshold: float, force_send: bool = False) -> bool:
    if force_send:
        return True
    if diff_vs_prev is not None and abs(diff_vs_prev) >= threshold:
        return True
    if diff_vs_ma20 is not None and abs(diff_vs_ma20) >= threshold:
        return True
    return False


def _send_telegram_message(body: str, retries: int = 3, delay_seconds: int = 10) -> None:
    bot_token = _load_env("TELEGRAM_BOT_TOKEN")
    chat_id = _load_env("TELEGRAM_CHAT_ID")

    if not all([bot_token, chat_id]):
        raise RuntimeError("텔레그램 설정이 완료되지 않았습니다. TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 를 확인하세요.")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": body, "disable_web_page_preview": True}).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            request = Request(url, data=payload, headers=headers, method="POST")
            with urlopen(request, timeout=15) as response:
                response_body = json.load(response)
            if not response_body.get("ok"):
                raise RuntimeError(response_body.get("description", "텔레그램 메시지 전송 실패"))
            return
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error


def cmd_check(args) -> None:
    snapshot = _get_price_snapshot(args.symbol, base_url=args.api_base_url, timeout=args.api_timeout)
    price = snapshot.get("price")
    previous_close = snapshot.get("previous_close")
    ma20 = snapshot.get("ma20")

    if price is None:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": snapshot.get("error", "주가 데이터를 가져오지 못했습니다."),
                    "symbol": snapshot.get("symbol"),
                },
                ensure_ascii=False,
            )
        )
        return

    diff_vs_prev = _calculate_diff(price, previous_close) if previous_close else None
    diff_vs_ma20 = _calculate_diff(price, ma20) if ma20 else None

    result = {
        "symbol": snapshot["symbol"],
        "name": snapshot["name"],
        "price": price,
        "previous_close": previous_close,
        "ma20": ma20,
        "diff_vs_previous_close": diff_vs_prev,
        "diff_vs_ma20": diff_vs_ma20,
    }

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    trigger = should_send_notification(diff_vs_prev, diff_vs_ma20, args.threshold, force_send=args.force_send)

    if trigger:
        subject = f"[{DEFAULT_NAME} ({args.symbol})] 일일 주가 알림"
        body = (
            f"{subject}\n\n"
            f"심볼: {snapshot['symbol']}\n"
            f"현재가: {price:,.0f}\n"
            f"전일 종가: {previous_close:,.0f}\n"
            f"20일선: {ma20:,.0f}\n"
            f"전일 대비: {diff_vs_prev:.2f}%\n"
            f"20일선 대비: {diff_vs_ma20:.2f}%"
        )
        try:
            _send_telegram_message(body, retries=args.email_retries, delay_seconds=args.email_retry_delay)
            result["notification"] = {
                "status": "sent",
                "subject": subject,
                "retries": args.email_retries,
                "forced": args.force_send,
            }
        except Exception as exc:
            result["notification"] = {
                "status": "failed",
                "error": str(exc),
                "retries": args.email_retries,
                "forced": args.force_send,
            }
    else:
        result["notification"] = {"status": "not_triggered"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="TIGER 미국나스닥 100 모니터링")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--threshold", type=float, default=5.0)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--api-base-url", default=os.getenv("YAHOO_API_BASE_URL", DEFAULT_API_BASE_URL))
    parser.add_argument("--api-timeout", type=int, default=int(os.getenv("YAHOO_API_TIMEOUT", str(DEFAULT_API_TIMEOUT))))
    parser.add_argument("--email-retries", type=int, default=int(os.getenv("EMAIL_RETRIES", "3")))
    parser.add_argument("--email-retry-delay", type=int, default=int(os.getenv("EMAIL_RETRY_DELAY", "10")))
    parser.add_argument("--force-send", action="store_true", help="스케줄 실행 시 기준치와 무관하게 항상 알림을 보낸다")
    parser.set_defaults(func=cmd_check)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
