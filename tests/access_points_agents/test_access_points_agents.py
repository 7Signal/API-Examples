import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory to sys.path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.access_points import access_points_agents

# Test that the function 'fetch_accesspoints' exists in the access_points_agents module
def test_fetch_accesspoints_function_exists():
    assert hasattr(access_points_agents, "fetch_accesspoints")


# Test that fetch_accesspoints correctly handles a successful API call
@patch("examples.access_points.access_points_agents.requests.get")
def test_fetch_accesspoints_success(mock_get, caplog):
    # Sample data to return from the mocked API call
    sample_data = {
        "results": [
            {
                "id": "ap1",
                "name": "AccessPoint1",
                "controller": "Controller1",
                "macAddress": "00:11:22:33:44:55",
                "locationId": "loc1"
            }
        ]
    }

    # Create a mock response object
    mock_response = MagicMock()
    # Simulate HTTP 200 OK
    mock_response.status_code = 200
    mock_response.ok = True
    # Return our sample data
    mock_response.json.return_value = sample_data 
    # Avoid raising exceptions
    mock_response.raise_for_status = MagicMock() 
    # Patch requests.get to return mock_response
    mock_get.return_value = mock_response        

    # Provide a fake token
    token = "fake-token"

    # Call the function under test, caplog will capture logging output
    with caplog.at_level("INFO"):
        access_points_agents.fetch_accesspoints(token)

    # Assert that expected logs appear
    assert "Access points fetched successfully." in caplog.text
    assert "Access Point - ID: ap1" in caplog.text
    assert "Controller1" in caplog.text
    assert "00:11:22:33:44:55" in caplog.text


# Test that log_accesspoints_summary runs without throwing errors
def test_log_accesspoints_summary_runs(caplog):
    # Sample data structured as expected by log_accesspoints_summary
    sample_data = {
        "results": [
            {
                "id": "ap1",
                "name": "AccessPoint1",
                "controller": "Controller1",
                "macAddress": "00:11:22:33:44:55",
                "locationId": "loc1"
            }
        ]
    }

    # Capture logs at INFO level
    with caplog.at_level("INFO"):
        access_points_agents.log_accesspoints_summary(sample_data)

    # Assert that expected details appear in the logs
    assert "Access Point - ID: ap1" in caplog.text
    assert "Controller1" in caplog.text
