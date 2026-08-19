import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.eyeris import client_analysis

AGENT_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
REQUEST_ID = "8b1d4e77-0c25-4a63-9f18-5d2a7e6b3c90"
QUEUE_ID = "c47a2f10-9e83-4b51-a2d6-70f1b8c94e25"
RESPONSE_ID = "e90f5c34-6b28-41d7-8a95-1f3c7d0b2a68"

SAMPLE_START = {
    "requestId": REQUEST_ID,
    "requestQueueId": QUEUE_ID,
    "responseId": RESPONSE_ID,
}

SAMPLE_RESULT = {
    "response": "# Wi-Fi Network Analysis\n\n## SUMMARY\nThe device roamed cleanly.",
    "requestId": REQUEST_ID,
    "responseId": RESPONSE_ID,
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(client_analysis, "start_analysis")
    assert hasattr(client_analysis, "get_analysis")
    assert hasattr(client_analysis, "poll_for_analysis")
    assert hasattr(client_analysis, "display_analysis")


# Test that start_analysis posts the four required fields
@patch("examples.eyeris.client_analysis.requests.post")
def test_start_analysis_success(mock_post, caplog):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = SAMPLE_START
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    with caplog.at_level("INFO"):
        started = client_analysis.start_analysis(
            "fake-token", AGENT_ID, "ROAMING", 1740106800000, 1740114000000
        )

    payload = mock_post.call_args.kwargs["json"]
    assert payload["agentId"] == AGENT_ID
    assert payload["type"] == "ROAMING"
    assert started["requestId"] == REQUEST_ID


# Test that from/to are sent as JSON strings, which is what the API expects
@patch("examples.eyeris.client_analysis.requests.post")
def test_start_analysis_sends_times_as_strings(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = SAMPLE_START
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    client_analysis.start_analysis(
        "fake-token", AGENT_ID, "ROAMING", 1740106800000, 1740114000000
    )

    payload = mock_post.call_args.kwargs["json"]
    assert payload["from"] == "1740106800000"
    assert payload["to"] == "1740114000000"
    assert isinstance(payload["from"], str)
    assert isinstance(payload["to"], str)


# Test that a lowercase analysis type is rejected before any request is sent
@patch("examples.eyeris.client_analysis.requests.post")
def test_start_analysis_rejects_invalid_type(mock_post, caplog):
    with caplog.at_level("ERROR"):
        started = client_analysis.start_analysis(
            "fake-token", AGENT_ID, "roaming", 1740106800000, 1740114000000
        )

    assert started is None
    mock_post.assert_not_called()


# Test that get_analysis passes requestQueueId as a required query parameter
@patch("examples.eyeris.client_analysis.requests.get")
def test_get_analysis_passes_queue_id(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_RESULT
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = client_analysis.get_analysis("fake-token", REQUEST_ID, QUEUE_ID)

    assert mock_get.call_args.kwargs["params"]["requestQueueId"] == QUEUE_ID
    assert result["response"].startswith("# Wi-Fi Network Analysis")


# Test that an optional responseId is forwarded when supplied
@patch("examples.eyeris.client_analysis.requests.get")
def test_get_analysis_includes_response_id_when_given(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_RESULT
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    client_analysis.get_analysis("fake-token", REQUEST_ID, QUEUE_ID, response_id=RESPONSE_ID)

    assert mock_get.call_args.kwargs["params"]["responseId"] == RESPONSE_ID


# Test that a 404 means "not ready yet" and returns None rather than raising
@patch("examples.eyeris.client_analysis.requests.get")
def test_get_analysis_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    assert client_analysis.get_analysis("fake-token", REQUEST_ID, QUEUE_ID) is None


# Test that polling stops as soon as a result is available
@patch("examples.eyeris.client_analysis.time.sleep", return_value=None)
@patch("examples.eyeris.client_analysis.get_analysis")
def test_poll_for_analysis_returns_first_result(mock_get_analysis, mock_sleep):
    mock_get_analysis.side_effect = [None, None, SAMPLE_RESULT]

    result = client_analysis.poll_for_analysis(
        "fake-token", REQUEST_ID, QUEUE_ID, interval=0, retries=10
    )

    assert result["requestId"] == REQUEST_ID
    assert mock_get_analysis.call_count == 3


# Test that polling gives up after the retry ceiling instead of looping forever
@patch("examples.eyeris.client_analysis.time.sleep", return_value=None)
@patch("examples.eyeris.client_analysis.get_analysis", return_value=None)
def test_poll_for_analysis_gives_up(mock_get_analysis, mock_sleep):
    result = client_analysis.poll_for_analysis(
        "fake-token", REQUEST_ID, QUEUE_ID, interval=0, retries=3
    )

    assert result is None
    assert mock_get_analysis.call_count == 3


# Test that display_analysis logs the returned prose
def test_display_analysis(caplog):
    with caplog.at_level("INFO"):
        client_analysis.display_analysis(SAMPLE_RESULT)

    assert "EYERIS ANALYSIS" in caplog.text
    assert "The device roamed cleanly." in caplog.text


# Test that display handles missing/partial data gracefully
def test_display_analysis_partial_data(caplog):
    with caplog.at_level("INFO"):
        client_analysis.display_analysis({"requestId": REQUEST_ID})

    assert "EYERIS ANALYSIS" in caplog.text
    assert "No analysis text" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests


def http_error_response(text="Bad Request"):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = text
    mock_response.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return mock_response


# Test that an HTTP error on start is logged and returns None
@patch("examples.eyeris.client_analysis.requests.post")
def test_start_analysis_http_error(mock_post, caplog):
    mock_post.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert client_analysis.start_analysis(
            "fake-token", AGENT_ID, "ROAMING", 1, 2
        ) is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure on start is caught
@patch("examples.eyeris.client_analysis.requests.post",
       side_effect=_requests.exceptions.ConnectionError("boom"))
def test_start_analysis_connection_error(mock_post, caplog):
    with caplog.at_level("ERROR"):
        assert client_analysis.start_analysis("fake-token", AGENT_ID, "ROAMING", 1, 2) is None

    assert "Unexpected error" in caplog.text


# Test that an HTTP error on the poll is distinguishable from "not ready yet",
# so polling can stop instead of retrying a rejected request for minutes
@patch("examples.eyeris.client_analysis.requests.get")
def test_get_analysis_http_error_returns_failed(mock_get):
    mock_get.return_value = http_error_response()

    result = client_analysis.get_analysis("fake-token", REQUEST_ID, QUEUE_ID)

    assert result == client_analysis.ANALYSIS_FAILED
    assert result is not None


# Test that polling stops immediately on a hard failure rather than retrying
@patch("examples.eyeris.client_analysis.time.sleep", return_value=None)
@patch("examples.eyeris.client_analysis.get_analysis",
       return_value=client_analysis.ANALYSIS_FAILED)
def test_poll_for_analysis_stops_on_failure(mock_get_analysis, mock_sleep, caplog):
    with caplog.at_level("ERROR"):
        result = client_analysis.poll_for_analysis(
            "fake-token", REQUEST_ID, QUEUE_ID, interval=0, retries=60
        )

    assert result is None
    assert mock_get_analysis.call_count == 1
    assert "not retrying" in caplog.text


# Test that display tolerates an entirely absent result
def test_display_analysis_handles_none(caplog):
    with caplog.at_level("INFO"):
        client_analysis.display_analysis(None)

    assert "No analysis text" in caplog.text


def run_main(input_values, **extra):
    applied = [
        patch("examples.eyeris.client_analysis.get_token", return_value=("tok", 0)),
        patch("builtins.input", side_effect=input_values),
    ]
    for target, value in extra.items():
        applied.append(patch(f"examples.eyeris.client_analysis.{target}", return_value=value))
    for p in applied:
        p.start()
    try:
        client_analysis.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main's happy path end to end
def test_main_happy_path(caplog):
    with caplog.at_level("INFO"):
        run_main(
            [AGENT_ID, "ROAMING", "", ""],
            start_analysis=SAMPLE_START,
            poll_for_analysis=SAMPLE_RESULT,
        )

    assert "EYERIS ANALYSIS" in caplog.text


# Test that main lowercases the typed analysis type before validating
def test_main_accepts_lowercase_type_input():
    run_main(
        [AGENT_ID, "roaming", "", ""],
        start_analysis=SAMPLE_START,
        poll_for_analysis=SAMPLE_RESULT,
    )


# Test that an empty agent id exits
def test_main_empty_agent_id_exits():
    with pytest.raises(SystemExit):
        run_main(["  "])


# Test that an unsupported analysis type exits
def test_main_bad_type_exits():
    with pytest.raises(SystemExit):
        run_main([AGENT_ID, "SIDEWAYS"])


# Test that non-numeric times exit
def test_main_bad_times_exit():
    with pytest.raises(SystemExit):
        run_main([AGENT_ID, "ROAMING", "abc", "def"])


# Test that a start time at or after the end time exits
def test_main_inverted_window_exits():
    with pytest.raises(SystemExit):
        run_main([AGENT_ID, "ROAMING", "200", "100"])


# Test that main stops cleanly when the analysis request is rejected
def test_main_exits_when_start_fails():
    with pytest.raises(SystemExit):
        run_main([AGENT_ID, "ROAMING", "", ""], start_analysis=None)
