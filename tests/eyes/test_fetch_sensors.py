import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.eyes import fetch_sensors

# Test that the function 'fetch_sensors' exists in the module
def test_fetch_sensors_function_exists():
    assert hasattr(fetch_sensors, "fetch_sensors")

# Test that fetch_sensors correctly handles a successful API call
@patch("examples.eyes.fetch_sensors.requests.get")
def test_fetch_sensors_success(mock_get, caplog):
    # Sample data returned from mocked API call
    sample_data = {
        "results": [
            {
                "id": "abcd",
                "name": "Sensor 1",
                "status": "online"
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

    # Provide a fake token
    token = "fake-token"

    # Call the function under test
    with caplog.at_level("INFO"):
        fetch_sensors.fetch_sensors(token)

    # Assert that expected logs appear
    assert "===== Sensor Summary =====" in caplog.text
    assert "id: abcd" in caplog.text
    assert "name: Sensor 1" in caplog.text
    assert "status: online" in caplog.text

# Test that log_sensor_summary runs and logs sensor details
def test_log_sensor_summary(caplog):
    sensor = {
        "id": "xyz",
        "name": "Test Sensor",
        "status": "offline"
    }

    with caplog.at_level("INFO"):
        fetch_sensors.log_sensor_summary(sensor)

    assert "id: xyz" in caplog.text
    assert "name: Test Sensor" in caplog.text
    assert "status: offline" in caplog.text

# Test that main() calls get_token and fetch_sensors
@patch("examples.eyes.fetch_sensors.fetch_sensors")
@patch("examples.eyes.fetch_sensors.get_token", return_value=("fake-token", None))
def test_main_calls_fetch_sensors(mock_get_token, mock_fetch_sensors):
    fetch_sensors.main()
    mock_get_token.assert_called_once()
    mock_fetch_sensors.assert_called_once_with("fake-token")
