import pytest
from unittest.mock import patch, MagicMock
from examples.user_management import fetch_user

 # Test that the 'fetch_users' function exists in the fetch_user module
def test_fetch_users_function_exists():
    assert hasattr(fetch_user, "fetch_users")

# Test that fetch_users correctly processes a successful API response
@patch("examples.user_management.fetch_user.requests.get")
def test_fetch_users_success(mock_get):

    # Mock a successful JSON response with sample users
    sample_data = {
        "results": [
            {
                "firstName": "Test",
                "lastName": "User",
                "email": "test.user@example.com",
                "id": "123",
                "roleKey": "tester"
            },
            {
                "firstName": "Sample",
                "lastName": "Person",
                "email": "sample.person@example.com",
                "id": "456",
                "role": {"name": "user"}
            }
        ]
    }

    # Create a mock response object (to simulate what requests.get would return)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = sample_data
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    # Use a fake token for authentication
    token = "fake-token"

    # Call function under test which uses requests.get internally
    fetch_user.fetch_users(token)

# Test that logging the user summary emits expected info log output
def test_log_users_summary_runs(caplog):

    # Provide sample response data with minimal user info
    sample_data = {
        "results": [
            {
                "firstName": "Test",
                "lastName": "User",
                "email": "test.user@example.com",
                "id": "123",
                "roleKey": "tester"
            }
        ]
    }
    # Use caplog to capture logs at INFO level during log_users_summary call
    with caplog.at_level("INFO"):
        fetch_user.log_users_summary(sample_data)

    # Assert that the log output includes these expected summary lines
    assert "Total Users:" in caplog.text
    assert "Test User" in caplog.text

# Test that log_users_summary logs a warning when there are no users
def test_log_users_summary_warns_if_no_users(caplog):

    # Provide empty results to trigger warning
    sample_data = {"results": []}

    # Use caplog to capture WARNING-level logs
    with caplog.at_level("WARNING"):
        fetch_user.log_users_summary(sample_data)

    # Assert the log output includes the warning about no users found
    assert "No users found" in caplog.text
