#!/usr/bin/env python3
"""
Regression test for Feb 24-27 autofill window.
Validates that:
1) Daily sheet contains the expected dates.
2) Per-day asset sum matches total_usd.
3) src/data.json chart_data contains all expected dates.
"""
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "assets.xlsx"
OUTPUT_PATH = REPO_ROOT / "src" / "data.json"
EXPECTED_DATES = ["2026-02-24", "2026-02-25", "2026-02-26", "2026-02-27"]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def _safe_num(value) -> float:
    if pd.isna(value) or value is None:
        return 0.0
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except Exception:
        return 0.0


def validate_daily_sheet() -> None:
    assert_true(INPUT_PATH.exists(), "assets.xlsx is missing")

    df = pd.read_excel(INPUT_PATH, sheet_name="Daily")
    df.columns = [str(c).strip().lower() for c in df.columns]
    required_columns = {"date", "cash_usd", "gold_usd", "stocks_usd", "total_usd", "nav"}
    missing = required_columns - set(df.columns)
    assert_true(not missing, f"Daily sheet missing columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    window = df[df["date"].isin(EXPECTED_DATES)].copy()
    assert_true(len(window) == len(EXPECTED_DATES), "Daily sheet does not contain all expected Feb 24-27 rows")

    for col in ["cash_usd", "gold_usd", "stocks_usd", "total_usd", "nav"]:
        window[col] = window[col].apply(_safe_num)

    for row in window.itertuples(index=False):
        calc_total = row.cash_usd + row.gold_usd + row.stocks_usd
        gap = abs(calc_total - row.total_usd)
        assert_true(gap <= 0.01, f"Asset sum mismatch on {row.date}: gap={gap:.4f}")
        assert_true(row.nav > 0, f"nav must be positive on {row.date}")


def validate_chart_data() -> None:
    assert_true(OUTPUT_PATH.exists(), "src/data.json is missing")

    with OUTPUT_PATH.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    chart_data = payload.get("chart_data")
    assert_true(isinstance(chart_data, list) and len(chart_data) > 0, "chart_data must be a non-empty list")

    chart_dates = {str(point.get("date")) for point in chart_data}
    missing_dates = [d for d in EXPECTED_DATES if d not in chart_dates]
    assert_true(not missing_dates, f"chart_data missing expected dates: {missing_dates}")

    date_to_value = {str(point.get("date")): _safe_num(point.get("value")) for point in chart_data}
    for day in EXPECTED_DATES:
        assert_true(date_to_value.get(day, 0.0) > 0, f"chart_data value must be positive on {day}")


if __name__ == "__main__":
    validate_daily_sheet()
    validate_chart_data()
    print("PASS: Feb 24-27 autofill regression checks are valid")
