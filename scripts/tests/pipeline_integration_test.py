import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from asset_pipeline import run_cycle

class TestPipelineIntegration(unittest.TestCase):
    @patch("asset_pipeline.publish_data")
    @patch("asset_pipeline.send_briefing")
    @patch("asset_pipeline.apply_fallback_briefing")
    @patch("asset_pipeline.analyze_portfolio", side_effect=RuntimeError("analysis boom"))
    @patch("asset_pipeline.update_data")
    def test_run_cycle_continues_with_fallback_when_analysis_fails(
        self,
        mock_update,
        mock_analyze,
        mock_fallback,
        mock_send,
        mock_publish,
    ):
        exit_code = run_cycle(time_of_day="morning", send_telegram=True, publish=True)

        self.assertEqual(exit_code, 0)
        mock_update.assert_called_once()
        mock_analyze.assert_called_once_with(time_of_day="morning")
        mock_fallback.assert_called_once()
        mock_send.assert_called_once_with(time_of_day="morning")
        mock_publish.assert_called_once()

    @patch("asset_pipeline.publish_data")
    @patch("asset_pipeline.send_briefing", side_effect=RuntimeError("telegram down"))
    @patch("asset_pipeline.analyze_portfolio")
    @patch("asset_pipeline.update_data")
    def test_run_cycle_stops_before_publish_when_send_fails(
        self,
        mock_update,
        mock_analyze,
        mock_send,
        mock_publish,
    ):
        exit_code = run_cycle(time_of_day="evening", send_telegram=True, publish=True)

        self.assertEqual(exit_code, 1)
        mock_publish.assert_not_called()

if __name__ == '__main__':
    unittest.main()
