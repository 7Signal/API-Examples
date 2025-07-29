import pytest
from unittest.mock import patch, MagicMock
from examples.api_keys import get_apikeys

# Test that the 'get_apikeys' function exists in the get_apikeys module
def test_get_apikeys_function_exists():
    assert hasattr(get_apikeys, "get_apikeys")

# Test that get_apikeys returns JSON data on a successful response
@patch("examples.api_keys.get_apikeys.requests.get")
def test_get_apikeys_returns_json(mock_get):

    # Create a mock response object to simulate requests.get
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {"pagination": {}, "results": []}
    mock_get.return_value = mock_response

    # Use a fake token for authentication
    token = "fake-token"

    # Call the function under test
    result = get_apikeys.get_apikeys(token)

    # Assert that the returned result is a dictionary and includes expected keys
    assert isinstance(result, dict)
    assert "pagination" in result
    assert "results" in result

# Test that get_apikeys returns None when the HTTP response is not OK
@patch("examples.api_keys.get_apikeys.requests.get")
def test_get_apikeys_returns_none_on_failure(mock_get):

    # mock objects to simulate requests.get
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_get.return_value = mock_response

    # Use a fake token for authentication
    token = "fake-token"
    
    # Call the function under test
    result = get_apikeys.get_apikeys(token)

    # Expecting None to be returned on auth failure
    assert result is None

# Test that log_response_data logs expected lines for a typical response
def test_log_response_data_runs_smoothly(caplog):
    sample_response = {
        "pagination": {
            "perPage": 10,
            "page": 1,
            "total": 1,
            "pages": 1
        },
        "results": [
            {
                "id": "123",
                "apiKey": "abc",
                "createdBy": "user1",
                "description": "desc",
                "createdAt": "2022-01-01T00:00:00Z",
                "organization": {"id": "org123"},
                "isSystem": False,
            }
        ]
    }

    # Import function directly for clarity
    from examples.api_keys.get_apikeys import log_response_data

    # Use 'caplog' to capture INFO-level logs during the function call
    with caplog.at_level("INFO"):
        log_response_data(sample_response)

    # Check certain lines appear in the logs, confirming correct logging
    assert "Pagination:" in caplog.text
    assert "Results (1 items):" in caplog.text

    # Make sure the logged output includes the API key id, but not "id: None"
    assert "id: 123" in caplog.text or "id: None" not in caplog.text

# Test that log_response_data emits a warning log if called with None
def test_log_response_data_with_none_logs_warning(caplog):
    from examples.api_keys.get_apikeys import log_response_data

    # Capture WARNING-level logging
    with caplog.at_level("WARNING"):
        log_response_data(None)

    # Verify that the warning is present in the logs
    assert "No response data to log." in caplog.text
