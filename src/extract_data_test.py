#!/usr/bin/env python3
"""
Local data extraction regression test.
Validates that src/extract_data.py produces a dashboard-compatible JSON payload.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "assets.xlsx"
OUTPUT_PATH = REPO_ROOT / "src" / "data.json"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def run_extract_data() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "src" / "extract_data.py")],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        fail("extract_data.py exited with non-zero status")


def validate_payload() -> None:
    assert_true(INPUT_PATH.exists(), "assets.xlsx is missing")
    assert_true(OUTPUT_PATH.exists(), "src/data.json was not generated")

    with OUTPUT_PATH.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    required_keys = {
        "assets",
        "holdings",
        "chart_data",
        "total_balance",
        "last_updated",
        "insights",
        "advisor_briefing",
        "performance",
    }
    missing = required_keys - payload.keys()
    assert_true(not missing, f"data.json missing keys: {sorted(missing)}")

    assets = payload["assets"]
    assert_true(isinstance(assets, list) and len(assets) == 3, "assets must be a 3-item list")
    expected_labels = {"Cash USD", "Gold USD", "US Stocks"}
    labels = {str(item.get("label")) for item in assets}
    assert_true(labels == expected_labels, f"unexpected asset labels: {sorted(labels)}")

    chart_data = payload["chart_data"]
    assert_true(isinstance(chart_data, list) and len(chart_data) > 0, "chart_data must be a non-empty list")
    first_point = chart_data[0]
    assert_true("date" in first_point and "value" in first_point, "chart_data point must include date/value")
    last_point = chart_data[-1]
    assert_true(isinstance(last_point.get("date"), str), "chart_data last date must be a string")
    assert_true(last_point["date"].count("-") == 2, "chart_data last date must be YYYY-MM-DD")

    try:
        float(str(payload["total_balance"]).replace(",", ""))
    except ValueError as exc:
        fail(f"total_balance is not numeric: {exc}")

    performance = payload["performance"]
    assert_true(isinstance(performance, dict) and "1d" in performance, "performance must include 1d")

    # Web UI should always reflect latest sync date on x-axis
    last_updated_date = datetime.strptime(payload["last_updated"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
    assert_true(
        chart_data[-1]["date"] == last_updated_date,
        f"chart_data latest date {chart_data[-1]['date']} != last_updated date {last_updated_date}",
    )

    briefing = payload["advisor_briefing"]
    assert_true(isinstance(briefing, dict), "advisor_briefing must be an object")
    for key in ["headline", "macro_summary", "verdict", "suggestions", "risks", "news_context", "source"]:
        assert_true(key in briefing, f"advisor_briefing missing key: {key}")
    assert_true(isinstance(briefing["suggestions"], list), "advisor_briefing.suggestions must be a list")
    assert_true(isinstance(briefing["risks"], list), "advisor_briefing.risks must be a list")


if __name__ == "__main__":
    run_extract_data()
    validate_payload()
    print("PASS: extract_data output schema is valid")
