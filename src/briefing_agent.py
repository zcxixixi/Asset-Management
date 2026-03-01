import datetime
import json
from typing import Any

from advisor_contract import generate_fallback, validate_payload

SYSTEM_PROMPT = """
You are BriefingAgent, a strict JSON generator for investment briefings.
Return only one JSON object and nothing else.

The JSON MUST match this exact schema:
{
  "generated_at": "ISO-8601 timestamp string",
  "source": "AdvisorAgent",
  "headline": "string",
  "macro_summary": "string",
  "verdict": "BULLISH | BEARISH | NEUTRAL",
  "suggestions": [
    {
      "asset": "string",
      "action": "BUY | SELL | HOLD",
      "rationale": "string"
    }
  ],
  "risks": ["string"],
  "news_context": [
    {
      "headline": "string",
      "source": "string",
      "timestamp": "string",
      "relevance_score": "number (optional)"
    }
  ],
  "global_context": [
    {
      "headline": "string",
      "source": "string",
      "timestamp": "string",
      "relevance_score": "number (optional)"
    }
  ],
  "disclaimer": "string"
}

Hard constraints:
- Use exactly the keys above.
- Do not add extra keys.
- Do not output markdown or prose.
- Do not hallucinate numeric valuations or performance metrics.
- If valuation data is missing, keep rationale qualitative.
""".strip()


def _iso_utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _to_float_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_news_item(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        headline = str(item.get("headline") or item.get("title") or "Untitled update").strip()
        source = str(item.get("source") or item.get("publisher") or "Unknown Source").strip()
        timestamp = str(item.get("timestamp") or item.get("published_at") or _iso_utc_now()).strip()
        relevance_score = _to_float_or_none(item.get("relevance_score"))
        payload: dict[str, Any] = {
            "headline": headline or "Untitled update",
            "source": source or "Unknown Source",
            "timestamp": timestamp or _iso_utc_now(),
        }
        if relevance_score is not None:
            payload["relevance_score"] = relevance_score
        return payload

    return {
        "headline": str(item).strip() or "Untitled update",
        "source": "Unknown Source",
        "timestamp": _iso_utc_now(),
    }


def _normalize_news_list(items: list) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    return [_normalize_news_item(item) for item in items]


def _asset_label(holding: Any, index: int) -> str:
    if isinstance(holding, dict):
        for key in ("asset", "symbol", "ticker", "name"):
            value = holding.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
    if holding is not None and str(holding).strip():
        return str(holding).strip()
    return f"Asset {index + 1}"


def _infer_verdict(headlines: list[str]) -> str:
    text = " ".join(headlines).lower()
    bearish_tokens = ("selloff", "recession", "inflation", "downgrade", "risk", "war", "volatility")
    bullish_tokens = ("growth", "upgrade", "rally", "expansion", "breakthrough", "recovery")
    bearish_hits = sum(1 for token in bearish_tokens if token in text)
    bullish_hits = sum(1 for token in bullish_tokens if token in text)

    if bullish_hits > bearish_hits:
        return "BULLISH"
    if bearish_hits > bullish_hits:
        return "BEARISH"
    return "NEUTRAL"


def _build_mock_response(holdings: list, news_context: list, global_context: list) -> dict[str, Any]:
    normalized_news = _normalize_news_list(news_context)
    normalized_global = _normalize_news_list(global_context)
    all_headlines = [item["headline"] for item in normalized_news + normalized_global]

    suggestions = [
        {
            "asset": _asset_label(holding, idx),
            "action": "HOLD",
            "rationale": (
                "No verified valuation inputs were provided, so this suggestion remains qualitative "
                "and focuses on risk-aware position discipline."
            ),
        }
        for idx, holding in enumerate(holdings[:3])
    ]

    return {
        "generated_at": _iso_utc_now(),
        "source": "AdvisorAgent",
        "headline": "Portfolio Briefing: Qualitative Signal Review",
        "macro_summary": (
            "This briefing summarizes provided portfolio and macro news context without inferring "
            "unverified valuation or performance figures."
        ),
        "verdict": _infer_verdict(all_headlines),
        "suggestions": suggestions,
        "risks": [
            "Narrative risk can shift quickly as new headlines emerge.",
            "Missing valuation inputs limit conviction and sizing confidence.",
        ],
        "news_context": normalized_news,
        "global_context": normalized_global,
        "disclaimer": (
            "This briefing is auto-generated for informational purposes only and does not constitute "
            "financial advice."
        ),
    }


def _call_llm(system_prompt: str, user_payload: dict[str, Any]) -> str:
    _ = system_prompt
    response = _build_mock_response(
        holdings=user_payload.get("holdings", []),
        news_context=user_payload.get("news_context", []),
        global_context=user_payload.get("global_context", []),
    )
    return json.dumps(response, ensure_ascii=False)


def generate_briefing(holdings: list, news_context: list, global_context: list) -> dict:
    user_payload = {
        "holdings": holdings if isinstance(holdings, list) else [],
        "news_context": news_context if isinstance(news_context, list) else [],
        "global_context": global_context if isinstance(global_context, list) else [],
    }

    try:
        raw_output = _call_llm(SYSTEM_PROMPT, user_payload)
        parsed = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
        if not isinstance(parsed, dict):
            return generate_fallback()
    except Exception:
        return generate_fallback()

    if not validate_payload(parsed):
        return generate_fallback()

    return parsed
