import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import requests

# Add root directory to sys.path so the fetch_groups module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module under test
from examples.groups import fetch_groups


# Test that the 'fetch_groups' function exists in the module
def test_fetch_groups_function_exists():
    assert hasattr(fetch_groups, "fetch_groups")


# Test that fetch_groups correctly handles a successful API call
@patch("examples.groups.fetch_groups.requests.get")
def test_fetch_groups_success(mock_get, caplog):
    # Sample API response to simulate a successful call
    sample_data = {
        "results": [
            {
                "id": "grp1",
                "key": "group-key",
                "displayName": "Test Group",
                "organization": {"id": "org1"},
                "instance": {"id": "inst1"}
            }
        ]
    }

    # Create a mock response object
    mock_response = MagicMock()
    # Simulate successful HTTP response
    mock_response.ok = True  
    # Return our sample data
    mock_response.json.return_value = sample_data 
    # Avoid raising exceptions
    mock_response.raise_for_status = MagicMock() 
    # Patch requests.get to return the mock response
    mock_get.return_value = mock_response  

    # Provide a fake token
    token = "fake-token"

    # Call function under test, caplog captures logging output
    with caplog.at_level("INFO"):
        data = fetch_groups.fetch_groups(token)

    # Verify that returned data matches our sample data
    assert data == sample_data
    # Verify expected log output
    assert "Groups fetched successfully." in caplog.text


# Test that fetch_groups logs an error when the API request fails
@patch("examples.groups.fetch_groups.requests.get")
def test_fetch_groups_failure(mock_get, caplog):
    # Simulate a network or API error
    mock_get.side_effect = requests.exceptions.RequestException("Internal Server Error")

    token = "fake-token"

    # Capture ERROR-level logs
    with caplog.at_level("ERROR"):
        data = fetch_groups.fetch_groups(token)

    # Verify function returns None on failure
    assert data is None
    # Verify that expected error message is logged
    assert "Error fetching groups: Internal Server Error" in caplog.text
