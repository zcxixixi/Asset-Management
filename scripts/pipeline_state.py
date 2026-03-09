from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_WORKBOOK_PATH = REPO_ROOT / "assets.xlsx"
PRIVATE_WORKBOOK_PATH = REPO_ROOT / "assets.local.xlsx"

PUBLIC_DATA_OUTPUT_PATHS = [REPO_ROOT / "src" / "data.json", REPO_ROOT / "public" / "data.json"]
PRIVATE_DATA_OUTPUT_PATHS = [REPO_ROOT / "src" / "data.local.json", REPO_ROOT / "public" / "data.local.json"]

PUBLIC_ANALYSIS_CONTEXT_PATH = REPO_ROOT / "backups" / "latest_analysis_context.json"
PRIVATE_ANALYSIS_CONTEXT_PATH = REPO_ROOT / "backups" / "latest_analysis_context.local.json"


def resolve_workbook_path() -> Path:
    override = os.getenv("ASSET_WORKBOOK_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if PRIVATE_WORKBOOK_PATH.exists():
        return PRIVATE_WORKBOOK_PATH
    return PUBLIC_WORKBOOK_PATH


def using_private_workbook() -> bool:
    return resolve_workbook_path() != PUBLIC_WORKBOOK_PATH


def data_output_paths(*, private: bool | None = None) -> list[Path]:
    use_private = using_private_workbook() if private is None else private
    return PRIVATE_DATA_OUTPUT_PATHS if use_private else PUBLIC_DATA_OUTPUT_PATHS


def analysis_context_path(*, private: bool | None = None) -> Path:
    use_private = using_private_workbook() if private is None else private
    return PRIVATE_ANALYSIS_CONTEXT_PATH if use_private else PUBLIC_ANALYSIS_CONTEXT_PATH


def write_data_outputs(payload: dict[str, Any], *, private: bool | None = None) -> list[Path]:
    paths = data_output_paths(private=private)
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return paths


def load_dashboard_payload(*, private: bool | None = None) -> dict[str, Any]:
    preferred_paths = data_output_paths(private=private)
    fallback_paths = PUBLIC_DATA_OUTPUT_PATHS if preferred_paths != PUBLIC_DATA_OUTPUT_PATHS else []
    for path in [*reversed(preferred_paths), *reversed(fallback_paths)]:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("No dashboard data payload found")


def write_analysis_context(context: dict[str, Any], *, private: bool | None = None) -> Path:
    path = analysis_context_path(private=private)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_analysis_context(*, private: bool | None = None) -> dict[str, Any]:
    primary = analysis_context_path(private=private)
    fallbacks = [PUBLIC_ANALYSIS_CONTEXT_PATH] if primary != PUBLIC_ANALYSIS_CONTEXT_PATH else []
    for path in [primary, *fallbacks]:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Missing analysis context at {primary}")


def update_advisor_briefing(briefing: dict[str, Any], *, private: bool | None = None) -> dict[str, Any]:
    payload = load_dashboard_payload(private=private)
    payload["advisor_briefing"] = briefing
    write_data_outputs(payload, private=private)
    return payload
