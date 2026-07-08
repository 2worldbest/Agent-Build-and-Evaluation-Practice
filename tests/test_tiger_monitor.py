import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "skills" / "tiger-nasdaq-monitor" / "manage_tiger_monitor.py"
SPEC = importlib.util.spec_from_file_location("manage_tiger_monitor", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_resolve_symbol_adds_ks_suffix_for_korean_code():
    assert MODULE.resolve_symbol("133690") == "133690.KS"
    assert MODULE.resolve_symbol("133690.KS") == "133690.KS"
    assert MODULE.resolve_symbol("AAPL") == "AAPL"


def test_parse_yahoo_payload_extracts_price_metrics():
    payload = {
        "chart": {
            "result": [
                {
                    "meta": {"symbol": "133690.KS", "previousClose": 100.0, "regularMarketPrice": 108.0},
                    "timestamp": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                    "indicators": {"quote": [{"close": [90.0, 91.0, 92.0, 93.0, 94.0, 95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]}]},
                }
            ],
            "error": None,
        }
    }
    snapshot = MODULE.parse_yahoo_payload(payload)
    assert snapshot["price"] == 108.0
    assert snapshot["previous_close"] == 100.0
    assert snapshot["ma20"] == 99.5
