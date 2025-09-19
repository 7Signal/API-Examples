import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import requests

# Add root directory to sys.path so that fetch_orgs module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module under test
from examples.organization import fetch_orgs


# Test that the function 'fetch_organizations' exists in the fetch_orgs module
def test_fetch_organizations_function_exists():
    assert hasattr(fetch_orgs, "fetch_organizations")


# Test that fetch_organizations correctly handles a successful API call
@patch("examples.organization.fetch_orgs.requests.get")
def test_fetch_organizations_success(mock_get, caplog):
    # Sample API response to simulate a successful call
    sample_data = {
        "results": [
            {
                "id": "org123",
                "name": "Test Organization",
                "connection": {"id": "conn456"},
                "mobileEyeOrgCode": "MOBILE123",
                "isSuspended": False
            }
        ]
    }

    # Create a mock response object to simulate requests.get return value
    mock_response = MagicMock()
    # Simulate HTTP 200 OK
    mock_response.status_code = 200 
    mock_response.ok = True
    # Return sample JSON
    mock_response.json.return_value = sample_data 
    # Prevent exceptions
    mock_response.raise_for_status = MagicMock() 
    # Patch requests.get
    mock_get.return_value = mock_response 

    token = "fake-token"

    # Call function under test; caplog captures logging output
    with caplog.at_level("INFO"):
        data = fetch_orgs.fetch_organizations(token)

    # Verify returned data matches expected sample data
    assert data == sample_data
    # Verify expected logging output
    assert "Fetching organizations" in caplog.text
    assert "Organizations fetched successfully." in caplog.text


# Test that log_organizations correctly logs organization details
def test_log_organizations_runs(caplog):
    # Sample data structured as expected by log_organizations
    sample_data = {
        "results": [
            {
                "id": "org123",
                "name": "Test Organization",
                "connection": {"id": "conn456"},
                "mobileEyeOrgCode": "MOBILE123",
                "isSuspended": False
            }
        ]
    }

    # Capture INFO-level logs during function execution
    with caplog.at_level("INFO"):
        fetch_orgs.log_organizations(sample_data)

    # Verify that expected details appear in logs
    assert "ID: org123" in caplog.text
    assert "Test Organization" in caplog.text
    assert "conn456" in caplog.text
    assert "MOBILE123" in caplog.text
    assert "False" in caplog.text


# Test that log_organizations warns when no data is provided
def test_log_organizations_warns_if_no_organizations(caplog):
    # Pass None to trigger warning
    with caplog.at_level("WARNING"):
        fetch_orgs.log_organizations(None)

    # Verify that warning message appears in logs
    assert "No results found in organizations data." in caplog.text


# Test that fetch_organizations logs an error when the API request fails
@patch("examples.organization.fetch_orgs.requests.get")
def test_fetch_organizations_failure(mock_get, caplog):
    # Simulate a network or API error
    mock_get.side_effect = requests.exceptions.RequestException("Network error")

    # Capture ERROR-level logs
    with caplog.at_level("ERROR"):
        data = fetch_orgs.fetch_organizations("fake-token")

    # Verify function returns None on failure
    assert data is None
    # Verify that expected error message is logged
    assert "Error fetching organizations: Network error" in caplog.text
