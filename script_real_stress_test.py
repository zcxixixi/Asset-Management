#!/usr/bin/env python3
"""
Lightweight 24/7 heartbeat check for repository data health.
Designed for scheduled GitHub Actions runs.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent
EXCEL_PATH = REPO_ROOT / "assets.xlsx"
JSON_PATH = REPO_ROOT / "public" / "data.json"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def to_number(value) -> float:
    if pd.isna(value) or value is None:
        return 0.0
    text = str(value).replace(",", "").replace("$", "").strip()
    if text == "":
        return 0.0
    return float(text)


def check_excel() -> None:
    assert_true(EXCEL_PATH.exists(), "assets.xlsx not found")
    df = pd.read_excel(EXCEL_PATH, sheet_name="Daily")
    df.columns = [str(c).strip().lower() for c in df.columns]

    required = {"date", "cash_usd", "gold_usd", "stocks_usd", "total_usd", "nav"}
    missing = required - set(df.columns)
    assert_true(not missing, f"Daily missing columns: {sorted(missing)}")
    assert_true(len(df) > 0, "Daily sheet is empty")

    latest = df.iloc[-1]
    calc_total = to_number(latest["cash_usd"]) + to_number(latest["gold_usd"]) + to_number(latest["stocks_usd"])
    total_usd = to_number(latest["total_usd"])
    gap = round(abs(calc_total - total_usd), 4)
    assert_true(gap <= 0.02, f"Daily latest asset sum mismatch: gap={gap:.4f}")
    assert_true(to_number(latest["nav"]) > 0, "Daily latest nav must be positive")


def check_json() -> None:
    assert_true(JSON_PATH.exists(), "public/data.json not found")
    with JSON_PATH.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    required = {"assets", "holdings", "chart_data", "total_balance", "last_updated", "insights", "performance"}
    missing = required - set(payload.keys())
    assert_true(not missing, f"data.json missing keys: {sorted(missing)}")

    chart_data = payload["chart_data"]
    assert_true(isinstance(chart_data, list) and len(chart_data) > 0, "chart_data must be non-empty")

    latest_point = chart_data[-1]
    assert_true("date" in latest_point and "value" in latest_point, "latest chart point missing date/value")
    assert_true(to_number(latest_point["value"]) > 0, "latest chart value must be positive")

    last_updated = str(payload.get("last_updated", "")).strip()
    assert_true(last_updated != "", "last_updated is missing")
    last_updated_date = last_updated.split(" ")[0]
    assert_true(
        str(latest_point.get("date", "")) == last_updated_date,
        "latest chart date must match last_updated date",
    )


if __name__ == "__main__":
    now = datetime.now(timezone.utc).isoformat()
    print(f"[heartbeat] started_at={now}")
    check_excel()
    check_json()
    print("[heartbeat] status=ok")
