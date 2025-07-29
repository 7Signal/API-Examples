import pytest
from unittest.mock import MagicMock, patch
from examples.rate_limiting import rate_limit

# Helper function to create a mocked HTTP response object
def make_mock_response(status_code=200, json_data=None, headers=None):
    resp = MagicMock()

    # Set the HTTP status code (e.g., 200, 429, 500)
    resp.status_code = status_code

    # .ok is True only if status_code == 200
    resp.ok = (status_code == 200)

    # When .json() is called, return given json_data (or empty dict)
    resp.json.return_value = json_data or {}

    # Set HTTP response headers (can be empty)
    resp.headers = headers or {}

    # Response body text (error message for non-200)
    resp.text = "error" if status_code != 200 else ""
    return resp

# This mock API function always returns a successful 200 response immediately
@patch("examples.rate_limiting.rate_limit.time.sleep", return_value=None)
def test_success_no_retry(mock_sleep):
    def api_func():
        return make_mock_response(200, {"result": "ok"})
    
    # Call the rate limit handler with the mocked API function
    result = rate_limit.handle_rate_limits(api_func)

    # Assert that the handler returned a dictionary (parsed JSON)
    assert isinstance(result, dict)

    # Assert that the result contains the expected data
    assert result.get("result") == "ok"

    # Assert that time.sleep was never called since no retry was needed
    mock_sleep.assert_not_called()
    mock_sleep.assert_not_called()

@patch("examples.rate_limiting.rate_limit.time.sleep", return_value=None)
def test_retry_for_429_then_success(mock_sleep):
    calls = [0]

    # This mock API function returns 429 error twice, then succeeds with 200
    def api_func():
        if calls[0] < 2:
            calls[0] += 1
             # Simulate rate limit error
            return make_mock_response(429)
        
        # Success response after retries
        return make_mock_response(200, {"done": True})
    
    # Call the rate limit handler
    result = rate_limit.handle_rate_limits(api_func)

    # Assert final result is a dictionary
    assert isinstance(result, dict)

    # Assert the success flag is present in the response
    assert result.get("done") is True

    # Assert that time.sleep was called twice because of two retries
    assert mock_sleep.call_count == 2

# This test guards against infinite retries; forcibly exit after several tries
@patch("examples.rate_limiting.rate_limit.time.sleep", return_value=None)
def test_max_retries_or_infinite_loop_guard(mock_sleep):
    calls = [0]

    # Simulate API that always returns 429 rate limit error,
    # but after 8 tries forcibly returns success to stop infinite loop in test
    def api_func():
        calls[0] += 1
        if calls[0] > 8:
            # Forced exit condition to prevent test hanging in case of buggy retry logic
            return make_mock_response(200, {"forced": True})
        
         # Simulate rate limit error
        return make_mock_response(429)
    
     # Call the handler with the mocked api_func
    result = rate_limit.handle_rate_limits(api_func)
    # Accepts None (if code gives up) or receive the forced success response
    assert result is None or (isinstance(result, dict) and result.get("forced") is True)


#This tests if a non-429 error happens (like 500), handler returns None immediately
@patch("examples.rate_limiting.rate_limit.time.sleep", return_value=None)
def test_non_429_error(mock_sleep):
    def api_func():
        # Simulate server error (HTTP 500)
        return make_mock_response(500)
    
    # Call the handler; it should not retry but return None immediately
    result = rate_limit.handle_rate_limits(api_func)

    # Assert that result is None since the error is not retriable
    assert result is None

    # Assert that time.sleep was never called because no retry was attempted
    mock_sleep.assert_not_called()
