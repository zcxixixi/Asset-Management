import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from advisor_contract import validate_payload
from briefing_agent import generate_briefing


class TestBriefingAgent(unittest.TestCase):
    @staticmethod
    def _valid_payload() -> dict:
        return {
            "generated_at": "2026-03-01T10:00:00Z",
            "source": "AdvisorAgent",
            "headline": "Portfolio Briefing",
            "macro_summary": "Macro conditions are mixed with stable inflation expectations.",
            "verdict": "NEUTRAL",
            "portfolio_overlay": {
                "stance": "BALANCED",
                "thesis": "Stay selective while macro and earnings remain mixed.",
                "rebalancing_watch": "Trim if one position dominates portfolio risk.",
            },
            "macro_themes": [
                {
                    "theme": "Rates and liquidity",
                    "implication": "Watch yields before adding duration-sensitive exposure.",
                }
            ],
            "suggestions": [
                {
                    "asset": "AAPL",
                    "action": "HOLD",
                    "rationale": "Wait for additional confirmation from upcoming earnings.",
                    "thesis": "The base case remains intact but does not justify pressing size today.",
                    "catalyst": "Upcoming earnings and product commentary.",
                    "risk": "Demand softness or margin pressure could weaken the thesis.",
                    "horizon": "MEDIUM",
                    "confidence": "MEDIUM",
                }
            ],
            "risks": ["Macro uncertainty remains elevated."],
            "news_context": [],
            "global_context": [],
            "disclaimer": "This briefing is auto-generated for informational purposes only and does not constitute financial advice.",
        }

    def test_generate_briefing_returns_schema_valid_payload(self):
        holdings = [{"symbol": "AAPL"}, {"asset": "MSFT"}]
        news_context = [
            {
                "headline": "Apple launches new AI features",
                "source": "Tech Daily",
                "timestamp": "2026-03-01T08:00:00Z",
                "channel": "company-ir",
            }
        ]
        global_context = [
            {
                "headline": "Global inflation cools in key regions",
                "source": "Macro Wire",
                "timestamp": "2026-03-01T09:00:00Z",
                "channel": "official-macro",
                "relevance_score": 0.71,
            }
        ]

        with patch("briefing_agent._run_analysis_agent", return_value=json.dumps(self._valid_payload(), ensure_ascii=False)):
            payload = generate_briefing(
                holdings,
                news_context,
                global_context,
                time_of_day="morning",
                thin_context=False,
                thin_context_reasons=[],
            )

        self.assertTrue(validate_payload(payload), "generate_briefing should always return schema-valid output")
        self.assertEqual(payload["source"], "AdvisorAgent")

    def test_generate_briefing_returns_fallback_on_invalid_llm_json(self):
        with patch("briefing_agent._run_analysis_agent", return_value="{not valid json"):
            payload = generate_briefing([], [], [])

        self.assertTrue(validate_payload(payload), "fallback payload must remain schema-valid")
        self.assertEqual(payload["source"], "AdvisorAgent_Fallback")

    def test_generate_briefing_returns_fallback_on_llm_exception(self):
        with patch("briefing_agent._run_analysis_agent", side_effect=TimeoutError("request timeout")):
            payload = generate_briefing(
                [{"symbol": "NVDA", "value": "10000"}],
                [{"headline": "NVIDIA update", "source": "Reuters", "timestamp": "2026-03-01T10:00:00Z", "channel": "market-news"}],
                [{"headline": "Fed update", "source": "Federal Reserve", "timestamp": "2026-03-01T09:00:00Z", "channel": "official-macro"}],
            )

        self.assertTrue(validate_payload(payload), "fallback payload must remain schema-valid")
        self.assertEqual(payload["source"], "AdvisorAgent_LocalFallback")
        self.assertIn("portfolio_overlay", payload)
        self.assertGreater(len(payload["suggestions"]), 0)


if __name__ == "__main__":
    unittest.main()
