import unittest
from unittest.mock import patch

from advisor_contract import validate_payload
from briefing_agent import generate_briefing


class TestBriefingAgent(unittest.TestCase):
    def test_generate_briefing_returns_schema_valid_payload(self):
        holdings = [{"symbol": "AAPL"}, {"asset": "MSFT"}]
        news_context = [
            {
                "headline": "Apple launches new AI features",
                "source": "Tech Daily",
                "timestamp": "2026-03-01T08:00:00Z",
            }
        ]
        global_context = [
            {
                "headline": "Global inflation cools in key regions",
                "source": "Macro Wire",
                "timestamp": "2026-03-01T09:00:00Z",
                "relevance_score": 0.71,
            }
        ]

        payload = generate_briefing(holdings, news_context, global_context)

        self.assertTrue(validate_payload(payload), "generate_briefing should always return schema-valid output")
        self.assertEqual(payload["source"], "AdvisorAgent")

    def test_generate_briefing_returns_fallback_on_invalid_llm_json(self):
        with patch("briefing_agent._call_llm", return_value="{not valid json"):
            payload = generate_briefing([], [], [])

        self.assertTrue(validate_payload(payload), "fallback payload must remain schema-valid")
        self.assertEqual(payload["source"], "AdvisorAgent_Fallback")


if __name__ == "__main__":
    unittest.main()
