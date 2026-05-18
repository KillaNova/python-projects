"""
API Health Checker
Pings a list of endpoints on a schedule, measures response time,
checks status codes, and alerts when something looks wrong.

Configure endpoints in endpoints.json (see endpoints.example.json).

Usage:
  python main.py --check         # one-shot check
  python main.py --watch         # continuous monitoring
  python main.py --report        # print last results from history.json
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    import sys
    sys.exit("Install dependencies:\n  pip install requests")

BASE = Path(__file__).parent
ENDPOINTS_PATH = BASE / "endpoints.json"
HISTORY_PATH = BASE / "history.json"

EXAMPLE_ENDPOINTS = [
    {
        "name": "JSONPlaceholder",
        "url": "https://jsonplaceholder.typicode.com/todos/1",
        "method": "GET",
        "expected_status": 200,
        "timeout_seconds": 5,
        "alert_on_slow_ms": 2000
    },
    {
        "name": "HTTPBin POST",
        "url": "https://httpbin.org/post",
        "method": "POST",
        "body": {"key": "value"},
        "headers": {"Content-Type": "application/json"},
        "expected_status": 200,
        "timeout_seconds": 5,
        "alert_on_slow_ms": 2000
    }
]


def load_endpoints() -> list[dict]:
    if not ENDPOINTS_PATH.exists():
        example_path = BASE / "endpoints.example.json"
        with open(example_path, "w") as f:
            json.dump(EXAMPLE_ENDPOINTS, f, indent=2)
        print(f"endpoints.json not found. Example written to {example_path}.")
        print("Rename it to endpoints.json and edit as needed.\n")
        print("Using built-in example endpoints for now…\n")
        return EXAMPLE_ENDPOINTS
    with open(ENDPOINTS_PATH) as f:
        return json.load(f)


def load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    with open(HISTORY_PATH) as f:
        return json.load(f)


def save_history(history: list[dict]) -> None:
    with open(HISTORY_PATH, "w") as f:
        json.dump(history[-500:], f, indent=2)  # keep last 500 records


def check_endpoint(ep: dict) -> dict:
    method = ep.get("method", "GET").upper()
    url = ep["url"]
    timeout = ep.get("timeout_seconds", 10)
    headers = ep.get("headers", {})
    body = ep.get("body", None)
    expected_status = ep.get("expected_status", 200)
    slow_threshold = ep.get("alert_on_slow_ms", 3000)

    result = {
        "name": ep["name"],
        "url": url,
        "method": method,
        "timestamp": datetime.now().isoformat(),
        "status": None,
        "response_ms": None,
        "ok": False,
        "alerts": [],
    }

    try:
        start = time.monotonic()
        resp = requests.request(
            method, url,
            headers=headers,
            json=body if body else None,
            timeout=timeout,
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        result["status"] = resp.status_code
        result["response_ms"] = round(elapsed_ms, 1)
        result["ok"] = resp.status_code == expected_status

        if resp.status_code != expected_status:
            result["alerts"].append(
                f"Status {resp.status_code} != expected {expected_status}"
            )
        if elapsed_ms > slow_threshold:
            result["alerts"].append(
                f"Slow response: {elapsed_ms:.0f}ms > {slow_threshold}ms"
            )

    except requests.exceptions.Timeout:
        result["alerts"].append(f"Timeout after {timeout}s")
    except requests.exceptions.ConnectionError as e:
        result["alerts"].append(f"Connection error: {e}")
    except Exception as e:
        result["alerts"].append(f"Unexpected error: {e}")

    return result


def print_result(r: dict) -> None:
    status_str = str(r["status"]) if r["status"] else "---"
    ms_str = f"{r['response_ms']}ms" if r["response_ms"] else "---"
    flag = "OK" if r["ok"] and not r["alerts"] else "WARN" if r["ok"] else "FAIL"
    color = {"OK": "\033[92m", "WARN": "\033[93m", "FAIL": "\033[91m"}[flag]
    reset = "\033[0m"
    print(f"  {color}[{flag}]{reset}  {r['name']:<30} {status_str:<8} {ms_str:<12} {r['url']}")
    for alert in r["alerts"]:
        print(f"         ⚠ {alert}")


def run_checks(endpoints: list[dict]) -> list[dict]:
    results = []
    print(f"\n{'─'*70}")
    print(f"  Health check — {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'─'*70}")
    for ep in endpoints:
        r = check_endpoint(ep)
        print_result(r)
        results.append(r)
    ok_count = sum(1 for r in results if r["ok"] and not r["alerts"])
    warn_count = sum(1 for r in results if r["ok"] and r["alerts"])
    fail_count = sum(1 for r in results if not r["ok"])
    print(f"{'─'*70}")
    print(f"  {ok_count} OK  |  {warn_count} WARN  |  {fail_count} FAIL\n")
    return results


def report(history: list[dict]) -> None:
    if not history:
        print("No history yet. Run --check first.")
        return
    last_run_ts = history[-1]["timestamp"]
    print(f"\nLast check: {last_run_ts}")
    names = {h["name"] for h in history}
    for name in sorted(names):
        records = [h for h in history if h["name"] == name][-10:]
        uptime = sum(1 for r in records if r["ok"]) / len(records) * 100
        avg_ms = sum(r["response_ms"] or 0 for r in records) / len(records)
        latest = records[-1]
        print(
            f"  {name:<30}  uptime={uptime:.0f}%  avg={avg_ms:.0f}ms  "
            f"last_status={latest['status']}  alerts={len(latest['alerts'])}"
        )


def main():
    parser = argparse.ArgumentParser(description="API health checker")
    parser.add_argument("--check", action="store_true", help="Run a one-shot check")
    parser.add_argument("--watch", action="store_true", help="Monitor continuously")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between checks (default 60)")
    parser.add_argument("--report", action="store_true", help="Print history summary")
    args = parser.parse_args()

    endpoints = load_endpoints()
    history = load_history()

    if args.report:
        report(history)
        return

    if args.check or args.watch:
        if args.watch:
            print(f"Watching {len(endpoints)} endpoint(s) every {args.interval}s. Ctrl+C to stop.")
            while True:
                results = run_checks(endpoints)
                history.extend(results)
                save_history(history)
                time.sleep(args.interval)
        else:
            results = run_checks(endpoints)
            history.extend(results)
            save_history(history)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
