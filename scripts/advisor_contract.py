from __future__ import annotations

import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ValidationError


class NewsItem(BaseModel):
    headline: str
    source: str
    timestamp: str
    channel: str
    url: Optional[str] = None
    symbol: Optional[str] = None
    summary: Optional[str] = None
    relevance_score: Optional[float] = None


class PortfolioOverlay(BaseModel):
    stance: Literal["OFFENSIVE", "BALANCED", "DEFENSIVE"]
    thesis: str
    rebalancing_watch: str


class MacroTheme(BaseModel):
    theme: str
    implication: str


class Suggestion(BaseModel):
    asset: str
    action: Literal["BUY", "SELL", "HOLD"]
    rationale: str
    thesis: str
    catalyst: str
    risk: str
    horizon: Literal["SHORT", "MEDIUM", "LONG"]
    confidence: Literal["LOW", "MEDIUM", "HIGH"]


class AdvisorBriefing(BaseModel):
    generated_at: str
    source: str = "AdvisorAgent"
    headline: str
    macro_summary: str
    verdict: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    portfolio_overlay: PortfolioOverlay
    macro_themes: List[MacroTheme]
    suggestions: List[Suggestion]
    risks: List[str]
    news_context: List[NewsItem]
    global_context: List[NewsItem]
    disclaimer: str = (
        "This briefing is auto-generated for informational purposes only and does not constitute financial advice."
    )


def validate_payload(data: dict[str, Any]) -> bool:
    try:
        AdvisorBriefing.model_validate(data)
        return True
    except ValidationError:
        return False


def generate_fallback() -> dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "generated_at": now,
        "source": "AdvisorAgent_Fallback",
        "headline": "Portfolio Sync Complete (Advisor Analysis Unavailable)",
        "macro_summary": (
            "Primary advisory analysis was unavailable, so the system produced a conservative "
            "portfolio-manager fallback based on current allocation and the latest synced holdings."
        ),
        "verdict": "NEUTRAL",
        "portfolio_overlay": {
            "stance": "BALANCED",
            "thesis": "Maintain core exposure, preserve liquidity, and wait for higher-conviction signals before changing risk materially.",
            "rebalancing_watch": "Reassess if a single risk asset becomes dominant or macro data materially shifts rates expectations.",
        },
        "macro_themes": [
            {
                "theme": "Rates and liquidity",
                "implication": "Avoid chasing duration-sensitive growth until policy and yields stabilize.",
            },
            {
                "theme": "Concentration discipline",
                "implication": "Keep single-name risk sized so one earnings cycle cannot define portfolio outcomes.",
            },
        ],
        "suggestions": [
            {
                "asset": "PORTFOLIO",
                "action": "HOLD",
                "rationale": "Default to capital preservation when the primary advisory layer is unavailable.",
                "thesis": "The synced portfolio should remain steady until higher-confidence evidence is available.",
                "catalyst": "Wait for fresh macro releases, earnings, or validated company-specific developments.",
                "risk": "Reacting without verified context can degrade entry quality and increase churn.",
                "horizon": "SHORT",
                "confidence": "LOW",
            }
        ],
        "risks": [
            "Advisory service timeout or schema validation failure.",
            "Fallback guidance is intentionally conservative and may miss fast-moving catalysts.",
        ],
        "news_context": [],
        "global_context": [],
        "disclaimer": "This briefing is a fallback message. It does not constitute financial advice.",
    }
