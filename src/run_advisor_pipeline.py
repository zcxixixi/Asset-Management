import json
import logging
import os
import sys

from news_collector import get_portfolio_context
from briefing_agent import generate_briefing
from advisor_contract import generate_fallback

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Paths corresponding to Web UI data files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DATA_PATH = os.path.join(BASE_DIR, "src", "data.json")
PUBLIC_DATA_PATH = os.path.join(BASE_DIR, "public", "data.json")


def load_data(filepath: str) -> dict:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load user data from {filepath}: {e}")
        return {}


def save_data(filepath: str, data: dict) -> None:
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully updated {filepath}")
    except Exception as e:
        logging.error(f"Failed to save data to {filepath}: {e}")


def main():
    logging.info("Starting Advisor Pipeline Orchestrator...")

    # 1. Load existing portfolio data to get current holdings
    logging.info(f"Reading holdings from {SRC_DATA_PATH}...")
    ui_data = load_data(SRC_DATA_PATH)
    holdings = ui_data.get("holdings", [])
    
    if not holdings:
        logging.warning("No holdings found in data.json. Will proceed with fallback behavior.")

    # 2. Agent 1: Run News Collector
    logging.info("Executing News Collector Agent...")
    try:
        context_result = get_portfolio_context(holdings)
        news_context = context_result.get("news_context", [])
        global_context = context_result.get("global_context", [])
        logging.info(f"News collection success: {len(news_context)} portfolio items, {len(global_context)} global items.")
    except Exception as e:
        logging.error(f"News Collector failed: {e}. Generating empty context.")
        news_context, global_context = [], []

    # 3. Agent 2: Run Briefing LLM & Guardrail Validator
    logging.info("Executing Briefing Agent & Guardrail Validator...")
    try:
        final_briefing = generate_briefing(
            holdings=holdings,
            news_context=news_context,
            global_context=global_context
        )
        logging.info(f"Briefing Agent returned valid payload with verdict: {final_briefing.get('verdict')}")
    except Exception as e:
        logging.error(f"Briefing Agent pipeline completely failed: {e}. Firing absolute minimum fallback.")
        final_briefing = generate_fallback()

    # 4. Patch back to both UI endpoints
    logging.info("Syncing advisor payload securely to Web UI destinations...")
    ui_data["advisor_briefing"] = final_briefing
    
    save_data(SRC_DATA_PATH, ui_data)
    save_data(PUBLIC_DATA_PATH, ui_data)
    
    logging.info("Advisor Pipeline execution complete.")

if __name__ == "__main__":
    main()
