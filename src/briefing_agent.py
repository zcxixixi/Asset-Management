import json
import os
from typing import Any

from advisor_contract import generate_fallback, validate_payload

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - handled safely in runtime fallback.
    OpenAI = None  # type: ignore[assignment]

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


def _call_llm(system_prompt: str, user_payload: str) -> str:
    if OpenAI is None:
        raise RuntimeError("openai package is not available")

    api_key = (os.getenv("GLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("Missing API key: set GLM_API_KEY or OPENAI_API_KEY")

    base_url = (os.getenv("GLM_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/").strip()
    model = (os.getenv("GLM_MODEL") or "glm-4-plus").strip()

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


def generate_briefing(holdings: list, news_context: list, global_context: list) -> dict:
    user_payload = {
        "holdings": holdings if isinstance(holdings, list) else [],
        "news_context": news_context if isinstance(news_context, list) else [],
        "global_context": global_context if isinstance(global_context, list) else [],
    }

    try:
        user_payload_json = json.dumps(user_payload, ensure_ascii=False)
        raw_output = _call_llm(SYSTEM_PROMPT, user_payload_json)
        parsed = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
        if not isinstance(parsed, dict):
            return generate_fallback()
        if not validate_payload(parsed):
            return generate_fallback()
    except Exception:
        return generate_fallback()

    return parsed
