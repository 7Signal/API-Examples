import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.time_series import numeric_agents  # adjust if your filename is different

# Test that the function 'fetch_numeric_metrics' exists
def test_fetch_numeric_metrics_function_exists():
    assert hasattr(numeric_agents, "fetch_numeric_metrics")

# Test that 'log_numeric_summary' exists
def test_log_numeric_summary_function_exists():
    assert hasattr(numeric_agents, "log_numeric_summary")

# Test that fetch_numeric_metrics handles a successful API call
@patch("examples.time_series.numeric_agents.requests.get")
def test_fetch_numeric_metrics_success(mock_get, caplog):
    # Sample API response
    sample_data = {
        "results": [
            {
                "locationId": "loc123",
                "metricAggregates": [
                    {
                        "metric": "EXPERIENCE_SCORE",
                        "avg": 95,
                        "threshold": 90,
                        "timeSeries": [
                            {"ts": 1700000000000, "avg": 95}
                        ]
                    }
                ]
            }
        ]
    }

    # Mock response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = sample_data
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    token = "fake-token"
    FROM = "1700000000000"
    TO = "1700003600000"

    with caplog.at_level("INFO"):
        numeric_agents.fetch_numeric_metrics(token, FROM, TO)

    assert "Total Result Groups: 1" in caplog.text
    assert "LocationId: loc123" in caplog.text
    assert "Metric: EXPERIENCE_SCORE | Avg: 95 | Threshold: 90" in caplog.text
    assert "Timestamp: 1700000000000 | Avg: 95" in caplog.text

# Test that log_numeric_summary runs without errors on empty results
def test_log_numeric_summary_empty_results(caplog):
    sample_data = {"results": []}

    with caplog.at_level("INFO"):
        numeric_agents.log_numeric_summary(sample_data)

    assert "No results found in response." in caplog.text
