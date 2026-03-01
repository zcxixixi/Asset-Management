import json
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError

class NewsItem(BaseModel):
    headline: str
    source: str
    timestamp: str
    url: Optional[str] = None
    relevance_score: Optional[float] = None

class Suggestion(BaseModel):
    asset: str
    action: Literal["BUY", "SELL", "HOLD"]
    rationale: str

class AdvisorBriefing(BaseModel):
    generated_at: str
    source: str = "AdvisorAgent"
    headline: str
    macro_summary: str
    verdict: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    suggestions: List[Suggestion]
    risks: List[str]
    news_context: List[NewsItem]
    global_context: List[NewsItem]
    disclaimer: str = "This briefing is auto-generated for informational purposes only and does not constitute financial advice."

def validate_payload(data: dict) -> bool:
    """Returns True if the data conforms to the AdvisorBriefing schema, False otherwise."""
    try:
        AdvisorBriefing.model_validate(data)
        return True
    except ValidationError:
        return False

def generate_fallback() -> dict:
    """Returns a safe, deterministic payload that matches the schema when LLM output fails."""
    import datetime
    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": "AdvisorAgent_Fallback",
        "headline": "Portfolio Sync Complete (Advisor Analysis Unavailable)",
        "macro_summary": "The automated advisory service is currently unavailable. Portfolio holdings have been synced successfully based on the latest market data.",
        "verdict": "NEUTRAL",
        "suggestions": [],
        "risks": ["Advisory service timeout or validation failure."],
        "news_context": [],
        "global_context": [],
        "disclaimer": "This briefing is a fallback message. It does not constitute financial advice."
    }
