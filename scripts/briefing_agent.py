from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from advisor_contract import generate_fallback, validate_payload

NANOBOT_ROOT = Path(__file__).resolve().parents[2]
if str(NANOBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(NANOBOT_ROOT))

ANALYSIS_WORKSPACE = Path(__file__).resolve().parent / "analysis_agent_workspace"

USER_PROMPT_TEMPLATE = """
You are preparing the structured advisor briefing for the current portfolio cycle.

Rules:
- Return only valid JSON matching the schema below.
- Give one suggestion per holding, ordered by portfolio weight descending.
- Tie each rationale to a concrete news item when possible.
- You may use web_search and web_fetch if the supplied context is stale or incomplete.
- Do not invent price targets or unsupported numbers.

Required JSON schema:
{{
  "generated_at": "ISO-8601 timestamp string",
  "source": "AdvisorAgent",
  "headline": "string",
  "macro_summary": "string",
  "verdict": "BULLISH | BEARISH | NEUTRAL",
  "suggestions": [
    {{
      "asset": "ticker symbol string",
      "action": "BUY | SELL | HOLD",
      "rationale": "string"
    }}
  ],
  "risks": ["string"],
  "news_context": [
    {{
      "headline": "string",
      "source": "string",
      "timestamp": "string",
      "relevance_score": "number (optional)"
    }}
  ],
  "global_context": [
    {{
      "headline": "string",
      "source": "string",
      "timestamp": "string",
      "relevance_score": "number (optional)"
    }}
  ],
  "disclaimer": "string"
}}

Time of day: {time_of_day}
Current UTC time: {generated_at}

Portfolio package:
{payload}
""".strip()


def _enrich_holdings(holdings: list[dict[str, Any]] | list[Any]) -> list[dict[str, Any]]:
    total_value = 0.0
    enriched: list[dict[str, Any]] = []

    for item in holdings or []:
        if not isinstance(item, dict):
            continue
        try:
            value = float(str(item.get("value", 0)).replace(",", "") or 0)
        except (TypeError, ValueError):
            value = 0.0
        total_value += value
        enriched.append({**item, "_value": value})

    if total_value <= 0:
        return [item for item in holdings if isinstance(item, dict)]

    result: list[dict[str, Any]] = []
    for item in enriched:
        entry = {key: value for key, value in item.items() if key != "_value"}
        entry["portfolio_weight_pct"] = round((item["_value"] / total_value) * 100, 1)
        result.append(entry)

    result.sort(key=lambda item: item.get("portfolio_weight_pct", 0), reverse=True)
    return result


def _strip_json_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
    if stripped.endswith("```"):
        stripped = stripped.rsplit("```", 1)[0]
    return stripped.strip()


def _generate_local_briefing(
    *,
    holdings: list[dict[str, Any]] | list[Any],
    news_context: list[dict[str, Any]] | list[Any],
    global_context: list[dict[str, Any]] | list[Any],
    generated_at: str,
    failure_reason: str,
) -> dict[str, Any]:
    ordered_holdings = _enrich_holdings(holdings if isinstance(holdings, list) else [])

    suggestions: list[dict[str, str]] = []
    for item in ordered_holdings:
        symbol = str(item.get("symbol") or item.get("name") or "").strip().upper()
        if not symbol:
            continue
        weight = float(item.get("portfolio_weight_pct") or 0)

        action = "HOLD"
        rationale = "Maintain current allocation while monitoring incoming market data."
        if weight >= 40:
            rationale = "Position is highly concentrated; avoid adding and monitor concentration risk."
        elif weight <= 8:
            rationale = "Position is relatively small; keep under observation for conviction and liquidity."
        elif 20 <= weight < 40:
            rationale = "Core allocation size is meaningful; keep exposure stable unless trend changes materially."

        suggestions.append(
            {
                "asset": symbol,
                "action": action,
                "rationale": rationale,
            }
        )

    if not suggestions:
        return generate_fallback()

    news_list = [item for item in news_context if isinstance(item, dict)]
    global_list = [item for item in global_context if isinstance(item, dict)]

    return {
        "generated_at": generated_at,
        "source": "AdvisorAgent_LocalFallback",
        "headline": "Portfolio Sync Complete (Local Advisory Fallback)",
        "macro_summary": "Automated local advisor generated risk-aware HOLD guidance while upstream AI analysis was unavailable.",
        "verdict": "NEUTRAL",
        "suggestions": suggestions,
        "risks": [f"Primary advisor unavailable: {failure_reason}"],
        "news_context": news_list,
        "global_context": global_list,
        "disclaimer": "This briefing is auto-generated for informational purposes only and does not constitute financial advice.",
    }


async def _run_analysis_agent(prompt: str, session_suffix: str) -> str:
    from nanobot.agent.loop import AgentLoop
    from nanobot.bus.queue import MessageBus
    from nanobot.cli.commands import _make_provider
    from nanobot.config.loader import load_config

    config = load_config()
    provider = _make_provider(config)
    bus = MessageBus()
    agent = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=ANALYSIS_WORKSPACE,
        model=config.agents.defaults.model,
        temperature=config.agents.defaults.temperature,
        max_tokens=config.agents.defaults.max_tokens,
        max_iterations=config.agents.defaults.max_tool_iterations,
        memory_window=max(8, min(config.agents.defaults.memory_window, 24)),
        reasoning_effort=config.agents.defaults.reasoning_effort,
        brave_api_key=config.tools.web.search.api_key or None,
        exec_config=config.tools.exec,
        restrict_to_workspace=True,
        session_manager=None,
        mcp_servers={},
        channels_config=config.channels,
    )

    for tool_name in list(agent.tools.tool_names):
        if tool_name not in {"web_search", "web_fetch"}:
            agent.tools.unregister(tool_name)

    try:
        return await agent.process_direct(
            prompt,
            session_key=f"asset-analysis:{session_suffix}",
            channel="cli",
            chat_id="asset-analysis",
        )
    finally:
        await agent.close_mcp()


def generate_briefing(
    holdings: list,
    news_context: list,
    global_context: list,
    *,
    time_of_day: str = "morning",
) -> dict:
    generated_at = datetime.now(timezone.utc).isoformat()
    safe_holdings = holdings if isinstance(holdings, list) else []
    safe_news_context = news_context if isinstance(news_context, list) else []
    safe_global_context = global_context if isinstance(global_context, list) else []
    payload = {
        "portfolio_holdings": _enrich_holdings(safe_holdings),
        "portfolio_news": safe_news_context,
        "global_macro_news": safe_global_context,
    }
    prompt = USER_PROMPT_TEMPLATE.format(
        time_of_day=time_of_day,
        generated_at=generated_at,
        payload=json.dumps(payload, ensure_ascii=False, indent=2),
    )

    try:
        raw_output = asyncio.run(
            _run_analysis_agent(
                prompt,
                session_suffix=f"{time_of_day}:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
            )
        )
        parsed = json.loads(_strip_json_fences(raw_output))
        if not isinstance(parsed, dict):
            return _generate_local_briefing(
                holdings=safe_holdings,
                news_context=safe_news_context,
                global_context=safe_global_context,
                generated_at=generated_at,
                failure_reason="advisor returned non-object JSON payload",
            )
        if not validate_payload(parsed):
            return _generate_local_briefing(
                holdings=safe_holdings,
                news_context=safe_news_context,
                global_context=safe_global_context,
                generated_at=generated_at,
                failure_reason="advisor JSON failed schema validation",
            )
        return parsed
    except Exception as exc:
        print(f"Briefing Agent Exception: {exc}")
        return _generate_local_briefing(
            holdings=safe_holdings,
            news_context=safe_news_context,
            global_context=safe_global_context,
            generated_at=generated_at,
            failure_reason=str(exc),
        )
