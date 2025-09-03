import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.eyes import fetch_agents

# Test that the function 'fetch_agent_by_id' exists in the module
def test_fetch_agent_by_id_function_exists():
    assert hasattr(fetch_agents, "fetch_agent_by_id")


# Test that fetch_agent_by_id correctly handles a successful API call
@patch("examples.eyes.fetch_agents.requests.get")
def test_fetch_agent_by_id_success(mock_get, caplog):
    # Sample data returned from mocked API call
    sample_data = {
        "id": "1234",
        "name": "Test Agent",
        "status": "active"
    }

    # Mock response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = sample_data
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    # Provide a fake token
    token = "fake-token"

    # Call the function under test
    with caplog.at_level("INFO"):
        fetch_agents.fetch_agent_by_id(token, "1234")

    # Assert that expected logs appear
    assert "===== Agent Summary =====" in caplog.text
    assert "id: 1234" in caplog.text
    assert "name: Test Agent" in caplog.text
    assert "status: active" in caplog.text


# Test that log_agent_summary runs without throwing errors
def test_log_agent_summary_runs(caplog):
    sample_data = {
        "id": "1234",
        "name": "Agent X",
        "status": "inactive"
    }

    with caplog.at_level("INFO"):
        fetch_agents.log_agent_summary(sample_data)

    assert "id: 1234" in caplog.text
    assert "name: Agent X" in caplog.text
    assert "status: inactive" in caplog.text
