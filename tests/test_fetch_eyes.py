import pytest
from unittest.mock import patch, MagicMock

# Import the module to be tested
from examples.authentication import fetch_eyes

# Test that the function 'fetch_eyes_summary' exists in the fetch_eyes module
def test_fetch_eyes_summary_function_exists():
    assert hasattr(fetch_eyes, "fetch_eyes_summary")


# Test that fetch_eyes_summary correctly handles a successful API call
@patch("examples.authentication.fetch_eyes.requests.get")
def test_fetch_eyes_summary_success(mock_get):
    
     # Create a mock response object to simulate requests.get return value
    mock_response = MagicMock()

    # Simulate HTTP 200 OK response
    mock_response.status_code = 200

    # Define the JSON data returned by .json()
    mock_response.json.return_value = {
        "agents": {
            "organizationName": "TestOrg",
            "deviceCount": 10,
            "licenseSummary": {
                "packageName": "Pro",
                "totalLicenses": 100,
                "usedLicenses": 50,
                "freeLicenses": 50,
            },
            "platformSummary": {
                "windows": 5,
                "linux": 5,
            },
        },
        "sensors": {
            "deviceCount": 5,
            "deviceStatusSummary": {
                "active": 4,
                "inactive": 1,
            },
            "modelSummary": {
                "X1000": 3,
                "X2000": 2,
            },
        },
    }

    # Patch requests.get to return mock_response
    mock_get.return_value = mock_response

    # Provide a fake token for authentication
    token = "fake-token"

    # Call function under test, which should invoke requests.get internally
    fetch_eyes.fetch_eyes_summary(token)


# Test that the function log_summary runs without throwing errors
def test_log_summary_runs_without_error(caplog):

    # Sample data structured as expected by log_summary
    sample_data = {
        "agents": {
            "organizationName": "TestOrg",
            "deviceCount": 5,
            "licenseSummary": {
                "packageName": "Basic",
                "totalLicenses": 10,
                "usedLicenses": 5,
                "freeLicenses": 5,
            },
            "platformSummary": {
                "mac": 3,
                "windows": 2,
            },
        },
        "sensors": {
            "deviceCount": 3,
            "deviceStatusSummary": {
                "active": 2,
                "inactive": 1,
            },
            "modelSummary": {
                "ModelA": 2,
                "ModelB": 1,
            },
        },
    }

    # caplog captures logging output during tests.
    # Use caplog pytest fixture to capture logs at INFO level during the call
    with caplog.at_level("INFO"):
        # Call the function that logs the summary of agents and sensors
        fetch_eyes.log_summary(sample_data)

    # Assert that expected summary headings appear in the logs
    assert "Agents Summary" in caplog.text
    assert "Sensors Summary" in caplog.text
