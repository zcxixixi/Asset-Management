import json
import os
from typing import Any

from advisor_contract import generate_fallback, validate_payload

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - handled safely in runtime fallback.
    OpenAI = None  # type: ignore[assignment]

SYSTEM_PROMPT = """
You are a veteran Wall Street chief investment strategist with 25 years of experience.
You manage a private client's personal portfolio. The client trusts you to be brutally honest.
Return ONLY one valid JSON object and nothing else.

## YOUR IDENTITY
- You are NOT an AI, chatbot, or assistant. You are a named human strategist: "James Chen, CIO".
- You speak with the confidence and authority of someone who has survived 2008, COVID crash, and the 2022 bear.
- You have strong, specific opinions. You never say "it depends" or "consider your risk tolerance."

## ANALYSIS METHODOLOGY
1. PORTFOLIO WEIGHT MATTERS: The user will provide each holding's weight (%). 
   - A 30% position deserves 3x more analysis depth than a 2% position.
   - Order your suggestions by portfolio weight, largest first.
   - For tiny positions (<5%), one sentence is enough. For core positions (>15%), write a detailed thesis.
2. NEWS CROSS-REFERENCING: Connect specific news headlines to specific holdings.
   - BAD: "Market conditions suggest caution"
   - GOOD: "Buffett dumping $187B in cash while you hold 29% in SGOV means your defensive posture is validated — but the 19% QQQ leg is exposed to the same tech repricing he's warning about."
3. INTER-ASSET CORRELATION: Analyze how your holdings interact.
   - Example: "Your SGOV + GOLD combo (57% of portfolio) is a textbook stagflation hedge, but your QQQ + NVDA exposure (22%) directly contradicts this thesis."
4. RISK-WEIGHTED VERDICT: Your BULLISH/BEARISH/NEUTRAL verdict must reflect the WEIGHTED portfolio, not individual stocks.

## BANNED PHRASES (immediate disqualification)
"confluence of", "mixed messages", "navigating", "dynamic landscape", "delving into",
"it's worth noting", "investors should consider", "market participants", "going forward",
"amid uncertainty", "remains to be seen", "cautiously optimistic", "prudent approach"

## OUTPUT QUALITY
- headline: A punchy Bloomberg-terminal style alert, max 8 words. Think ticker-tape urgency.
- macro_summary: Exactly 2-3 sentences. Be a storyteller, not a summarizer. Connect the dots between seemingly unrelated news items. End with a provocative insight.
- suggestions: One per holding. Rationale must reference a SPECIFIC news item provided.
- risks: Name 2-3 SPECIFIC, non-obvious risks. Not generic "market volatility" — name the exact trigger.
- disclaimer: Keep it short and professional.

The JSON MUST match this exact schema:
{
  "generated_at": "ISO-8601 timestamp string",
  "source": "AdvisorAgent",
  "headline": "string",
  "macro_summary": "string",
  "verdict": "BULLISH | BEARISH | NEUTRAL",
  "suggestions": [
    {
      "asset": "string (use the ticker symbol)",
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
- Use exactly the keys above. Do not add extra keys.
- Do not output markdown or prose — pure JSON only.
- Do not hallucinate numeric price targets or performance metrics.
""".strip()


def _call_llm(system_prompt: str, user_payload: str) -> str:
    if OpenAI is None:
        raise RuntimeError("openai package is not available")

    api_key = (os.getenv("GLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("Missing API key: set GLM_API_KEY or OPENAI_API_KEY")

    base_url = (os.getenv("GLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/").strip()
    model = (os.getenv("GLM_MODEL") or os.getenv("OPENAI_MODEL") or "glm-4-plus").strip()

    client = OpenAI(api_key=api_key, base_url=base_url)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ],
        response_format={"type": "json_object"},
    )

    if not completion.choices:
        raise RuntimeError("Empty model response choices")

    content: Any = completion.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Empty model response content")

    return content


def _enrich_holdings(holdings: list) -> list:
    """Add portfolio weight (%) to each holding for the LLM to reason about."""
    total_value = 0.0
    enriched = []

    for h in holdings:
        if not isinstance(h, dict):
            continue
        try:
            value = float(h.get("value", 0) or 0)
        except (TypeError, ValueError):
            value = 0.0
        total_value += value
        enriched.append({**h, "_value": value})

    if total_value <= 0:
        return holdings

    result = []
    for h in enriched:
        weight_pct = round((h["_value"] / total_value) * 100, 1)
        entry = {k: v for k, v in h.items() if k != "_value"}
        entry["portfolio_weight_pct"] = weight_pct
        result.append(entry)

    # Sort by weight descending so LLM sees biggest positions first
    result.sort(key=lambda x: x.get("portfolio_weight_pct", 0), reverse=True)
    return result


def generate_briefing(holdings: list, news_context: list, global_context: list) -> dict:
    enriched_holdings = _enrich_holdings(holdings if isinstance(holdings, list) else [])

    user_payload = {
        "portfolio_holdings": enriched_holdings,
        "portfolio_news": news_context if isinstance(news_context, list) else [],
        "global_macro_news": global_context if isinstance(global_context, list) else [],
        "instruction": (
            "Analyze this portfolio. Holdings are sorted by weight — prioritize the largest positions. "
            "Cross-reference each holding against the provided news. "
            "Give ONE suggestion per holding. Be brutally specific."
        ),
    }

    try:
        user_payload_json = json.dumps(user_payload, ensure_ascii=False)
        raw_output = _call_llm(SYSTEM_PROMPT, user_payload_json)
        print("RAW LLM OUTPUT:", raw_output)
        parsed = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
        if not isinstance(parsed, dict):
            print("Parsed output is not a dict")
            return generate_fallback()
        if not validate_payload(parsed):
            print("Payload validation failed!")
            return generate_fallback()
    except Exception as e:
        print(f"Briefing Agent Exception: {e}")
        return generate_fallback()

    return parsed
