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
You are preparing a structured institutional-quality portfolio manager briefing for the current portfolio cycle.

Rules:
- Return only valid JSON matching the schema below.
- Keep the tone concise, professional, and evidence-based.
- Use first-principles reasoning: connect macro regime -> asset-specific thesis -> action.
- Give one suggestion per holding, ordered by portfolio weight descending.
- Every suggestion must include asymmetric risk/reward framing through thesis, catalyst, and risk.
- Tie each rationale to a concrete news item when possible.
- Do not invent price targets, valuation figures, or unsupported numbers.
- Use web_search and web_fetch only if thin_context is true. If context is already sufficient, do not browse.

Required JSON schema:
{{
  "generated_at": "ISO-8601 timestamp string",
  "source": "AdvisorAgent",
  "headline": "string",
  "macro_summary": "string",
  "verdict": "BULLISH | BEARISH | NEUTRAL",
  "portfolio_overlay": {{
    "stance": "OFFENSIVE | BALANCED | DEFENSIVE",
    "thesis": "string",
    "rebalancing_watch": "string"
  }},
  "macro_themes": [
    {{
      "theme": "string",
      "implication": "string"
    }}
  ],
  "suggestions": [
    {{
      "asset": "ticker symbol string",
      "action": "BUY | SELL | HOLD",
      "rationale": "string",
      "thesis": "string",
      "catalyst": "string",
      "risk": "string",
      "horizon": "SHORT | MEDIUM | LONG",
      "confidence": "LOW | MEDIUM | HIGH"
    }}
  ],
  "risks": ["string"],
  "news_context": [
    {{
      "headline": "string",
      "source": "string",
      "timestamp": "string",
      "channel": "string",
      "url": "string (optional)",
      "symbol": "string (optional)",
      "summary": "string (optional)",
      "relevance_score": "number (optional)"
    }}
  ],
  "global_context": [
    {{
      "headline": "string",
      "source": "string",
      "timestamp": "string",
      "channel": "string",
      "url": "string (optional)",
      "symbol": "string (optional)",
      "summary": "string (optional)",
      "relevance_score": "number (optional)"
    }}
  ],
  "disclaimer": "string"
}}

Time of day: {time_of_day}
Current UTC time: {generated_at}
thin_context: {thin_context}
thin_context_reasons: {thin_context_reasons}

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


def _portfolio_overlay_for_holdings(ordered_holdings: list[dict[str, Any]]) -> dict[str, str]:
    top_weight = float(ordered_holdings[0].get("portfolio_weight_pct") or 0) if ordered_holdings else 0.0
    if top_weight >= 45:
        stance = "DEFENSIVE"
        thesis = "Concentration is elevated, so preserve optionality and avoid increasing gross risk until diversification improves."
        watch = "Reduce exposure if the largest position becomes the dominant driver of weekly PnL."
    elif top_weight >= 25:
        stance = "BALANCED"
        thesis = "Core exposures are meaningful but still manageable, so keep risk balanced between conviction and liquidity."
        watch = "Rebalance if the leading position outruns the rest of the book after a catalyst."
    else:
        stance = "OFFENSIVE"
        thesis = "Concentration is controlled, which supports selective risk-taking when catalysts and macro conditions align."
        watch = "Deploy cash only into names with improving catalyst quality, not just price weakness."
    return {
        "stance": stance,
        "thesis": thesis,
        "rebalancing_watch": watch,
    }


def _macro_themes_for_context(global_context: list[dict[str, Any]]) -> list[dict[str, str]]:
    themes: list[dict[str, str]] = []
    headlines = " ".join(str(item.get("headline") or "") for item in global_context).upper()

    if any(token in headlines for token in ("RATE", "FED", "INFLATION", "YIELD", "TREASURY")):
        themes.append(
            {
                "theme": "Rates and liquidity",
                "implication": "Duration-sensitive assets should be sized against the direction of yields rather than pure narrative momentum.",
            }
        )
    if any(token in headlines for token in ("LABOR", "EMPLOYMENT", "PAYROLL", "CPI", "PPI")):
        themes.append(
            {
                "theme": "Macro data sensitivity",
                "implication": "Near-term entries should leave room for volatility around official data releases.",
            }
        )
    themes.append(
        {
            "theme": "Concentration discipline",
            "implication": "The portfolio should only add risk where catalysts are specific and downside is identifiable.",
        }
    )
    return themes[:3]


def _generate_local_briefing(
    *,
    holdings: list[dict[str, Any]] | list[Any],
    news_context: list[dict[str, Any]] | list[Any],
    global_context: list[dict[str, Any]] | list[Any],
    generated_at: str,
    failure_reason: str,
) -> dict[str, Any]:
    ordered_holdings = _enrich_holdings(holdings if isinstance(holdings, list) else [])
    if not ordered_holdings:
        fallback = generate_fallback()
        fallback["generated_at"] = generated_at
        return fallback

    suggestions: list[dict[str, str]] = []
    for item in ordered_holdings:
        symbol = str(item.get("symbol") or item.get("name") or "").strip().upper()
        if not symbol:
            continue
        weight = float(item.get("portfolio_weight_pct") or 0)

        rationale = "Maintain the current line while waiting for higher-confidence catalysts."
        thesis = "The position remains investable, but current evidence favors disciplined sizing over aggressive change."
        catalyst = "Watch for earnings, official company updates, or macro conditions that improve the payoff asymmetry."
        risk = "Position-level drawdown risk increases if new information fails to confirm the current thesis."
        horizon = "MEDIUM"
        confidence = "MEDIUM"

        if weight >= 35:
            rationale = "The position is already large enough that risk management matters more than pressing the trade."
            thesis = "A concentrated winner should earn the right to stay large through durable execution, not just narrative strength."
            catalyst = "Sustained operating momentum or official company disclosures that reinforce the existing thesis."
            risk = "Any earnings or policy disappointment can hit portfolio-level PnL disproportionally."
            horizon = "SHORT"
            confidence = "HIGH"
        elif weight <= 10:
            rationale = "The position is small, so there is no need to force action before conviction improves."
            thesis = "Smaller lines should graduate through evidence, not through averaging into uncertainty."
            catalyst = "A clearer earnings, macro, or company-specific trigger that improves expected payoff."
            risk = "Low-conviction averaging can turn a watchlist position into clutter."
            horizon = "LONG"
            confidence = "MEDIUM"

        suggestions.append(
            {
                "asset": symbol,
                "action": "HOLD",
                "rationale": rationale,
                "thesis": thesis,
                "catalyst": catalyst,
                "risk": risk,
                "horizon": horizon,
                "confidence": confidence,
            }
        )

    return {
        "generated_at": generated_at,
        "source": "AdvisorAgent_LocalFallback",
        "headline": "Portfolio Sync Complete (Local PM Fallback)",
        "macro_summary": "The local advisory fallback kept the portfolio in review mode while the upstream research agent was unavailable.",
        "verdict": "NEUTRAL",
        "portfolio_overlay": _portfolio_overlay_for_holdings(ordered_holdings),
        "macro_themes": _macro_themes_for_context([item for item in global_context if isinstance(item, dict)]),
        "suggestions": suggestions,
        "risks": [
            f"Primary advisor unavailable: {failure_reason}",
            "Fallback output is intentionally conservative and may underreact to fresh catalysts.",
        ],
        "news_context": [item for item in news_context if isinstance(item, dict)],
        "global_context": [item for item in global_context if isinstance(item, dict)],
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
    thin_context: bool = False,
    thin_context_reasons: list[str] | None = None,
) -> dict:
    generated_at = datetime.now(timezone.utc).isoformat()
    safe_holdings = holdings if isinstance(holdings, list) else []
    safe_news_context = news_context if isinstance(news_context, list) else []
    safe_global_context = global_context if isinstance(global_context, list) else []
    safe_reasons = thin_context_reasons if isinstance(thin_context_reasons, list) else []

    payload = {
        "portfolio_holdings": _enrich_holdings(safe_holdings),
        "portfolio_news": safe_news_context,
        "global_macro_news": safe_global_context,
    }
    prompt = USER_PROMPT_TEMPLATE.format(
        time_of_day=time_of_day,
        generated_at=generated_at,
        thin_context=str(bool(thin_context)).lower(),
        thin_context_reasons=json.dumps(safe_reasons, ensure_ascii=False),
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
