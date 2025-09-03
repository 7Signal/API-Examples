import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to sys.path so fetch_roles module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module under test
from examples.roles import fetch_roles


# Test that the 'fetch_roles' function exists in the module
def test_fetch_roles_function_exists():
    assert hasattr(fetch_roles, "fetch_roles")


# Test that fetch_roles correctly handles a successful API call
@patch("examples.roles.fetch_roles.requests.get")
def test_fetch_roles_success(mock_get, caplog):

    # Sample API response to simulate a successful call
    sample_data = {
        "results": [
            {
                "id": "role1",
                "key": "admin",
                "description": "Administrator role",
                "auth0Id": "auth0|123",
                "isPublic": True
            }
        ]
    }

    # Create a mock response object for requests.get
    mock_response = MagicMock()
    # Simulate HTTP 200 OK
    mock_response.status_code = 200
    mock_response.ok = True
    # Return sample JSON
    mock_response.json.return_value = sample_data 
    # Prevent exception
    mock_response.raise_for_status = MagicMock() 
    # Patch requests.get
    mock_get.return_value = mock_response

    token = "fake-token"

    # Call function under test; caplog captures logging output
    with caplog.at_level("INFO"):
        data = fetch_roles.fetch_roles(token)

    # Verify that the returned data matches expected sample data
    assert data == sample_data
    # Verify that expected logging messages were emitted
    assert "Roles fetched successfully." in caplog.text
    assert "Fetching roles from https://" in caplog.text


# Test that log_roles correctly logs role details
def test_log_roles_runs(caplog):

    # Sample data structured as expected by log_roles
    sample_data = {
        "results": [
            {
                "id": "role1",
                "key": "admin",
                "description": "Administrator role",
                "auth0Id": "auth0|123",
                "isPublic": True
            }
        ]
    }

    # Capture INFO-level logs during function execution
    with caplog.at_level("INFO"):
        fetch_roles.log_roles(sample_data)

    # Verify that expected role details appear in logs
    assert "ID: role1" in caplog.text
    assert "admin" in caplog.text
    assert "Administrator role" in caplog.text


# Test that log_roles logs a warning when data is None
def test_log_roles_warns_if_none(caplog):

    # Pass None to trigger the warning
    with caplog.at_level("WARNING"):
        fetch_roles.log_roles(None)

    # Verify that the warning message appears in logs
    assert "No results found in roles data." in caplog.text
