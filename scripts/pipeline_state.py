from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUTPUT_PATHS = [REPO_ROOT / "src" / "data.json", REPO_ROOT / "public" / "data.json"]
ANALYSIS_CONTEXT_PATH = REPO_ROOT / "backups" / "latest_analysis_context.json"


def write_data_outputs(payload: dict[str, Any]) -> None:
    for path in DATA_OUTPUT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_dashboard_payload() -> dict[str, Any]:
    for path in reversed(DATA_OUTPUT_PATHS):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("No dashboard data.json found in src/ or public/")


def write_analysis_context(context: dict[str, Any]) -> None:
    ANALYSIS_CONTEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ANALYSIS_CONTEXT_PATH.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")


def load_analysis_context() -> dict[str, Any]:
    if not ANALYSIS_CONTEXT_PATH.exists():
        raise FileNotFoundError(f"Missing analysis context at {ANALYSIS_CONTEXT_PATH}")
    return json.loads(ANALYSIS_CONTEXT_PATH.read_text(encoding="utf-8"))


def update_advisor_briefing(briefing: dict[str, Any]) -> dict[str, Any]:
    payload = load_dashboard_payload()
    payload["advisor_briefing"] = briefing
    write_data_outputs(payload)
    return payload
