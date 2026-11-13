import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.eyeris import analysis_stream

SAMPLE_LINES = [
    "data:# Wi-Fi Network Analysis",
    "data:",
    "data:## SUMMARY",
    "data:The device experienced a brief 2-minute connectivity problem",
    "",
    "data:## RECOMMENDATIONS",
    "data:No device-side changes are recommended.",
]


def build_streaming_response(lines=None, headers=None):
    # Builds a mock that behaves like a streaming requests response used in a
    # `with` block: the context manager yields the response itself.
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_lines.return_value = iter(lines if lines is not None else SAMPLE_LINES)
    mock_response.headers = headers if headers is not None else {}

    mock_post = MagicMock()
    mock_post.return_value.__enter__.return_value = mock_response
    mock_post.return_value.__exit__.return_value = False
    return mock_post, mock_response


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(analysis_stream, "stream_analysis")
    assert hasattr(analysis_stream, "log_stream_identifiers")


# Test that the request opts into streaming; without this the client buffers
# the whole body and the incremental behaviour is lost
def test_stream_analysis_uses_stream_true():
    mock_post, _ = build_streaming_response()

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert mock_post.call_args.kwargs["stream"] is True


# Test that the body carries promptTypeKey and inputData, not the
# request/poll endpoint's agentId/type/from/to shape
def test_stream_analysis_sends_prompt_type_and_input_data():
    mock_post, _ = build_streaming_response()

    input_data = analysis_stream.build_input_data("WIFI_CONGESTION_ANALYSIS", "abc", 1, 2)
    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", input_data)

    payload = mock_post.call_args.kwargs["json"]
    assert payload["promptTypeKey"] == "WIFI_CONGESTION_ANALYSIS"
    assert payload["inputData"] == input_data


# Test that inputData is the agent time-series query the prompt types read
def test_build_input_data_is_an_agent_time_series_query():
    input_data = analysis_stream.build_input_data("WIFI_COVERAGE_ANALYSIS", "agent-1", 100, 200)

    assert input_data == {
        "groupByDimension": "BSSID",
        "from": 100,
        "to": 200,
        "timeBucket": "ONE_MIN",
        "aggregateFunctions": ["AVG"],
        "metrics": ["COVERAGE", "SIGNAL_STRENGTH", "BEST_NEIGHBOR_SIGNAL_STRENGTH", "SEVEN_MCS"],
        "deviceIds": ["agent-1"],
    }


# Test that an unknown prompt type still gets a query, with every known metric
def test_build_input_data_for_an_unknown_prompt_type():
    input_data = analysis_stream.build_input_data("SOMETHING_NEW", "agent-1", 100, 200)

    assert set(input_data["metrics"]) == set(analysis_stream.DEFAULT_METRICS)


# Test that the data: prefix is stripped and the text is assembled in order
def test_stream_analysis_strips_data_prefix():
    mock_post, _ = build_streaming_response()

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        text = analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert "# Wi-Fi Network Analysis" in text
    assert "## RECOMMENDATIONS" in text
    # The prefix itself should not survive into the assembled output
    assert "data:" not in text


# Test that lines are consumed incrementally rather than via response.text
def test_stream_analysis_iterates_lines():
    mock_post, mock_response = build_streaming_response()

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    mock_response.iter_lines.assert_called_once()


# Test that each chunk is logged as it arrives
def test_stream_analysis_logs_chunks(caplog):
    mock_post, _ = build_streaming_response()

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        with caplog.at_level("INFO"):
            analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert "## SUMMARY" in caplog.text


# Test that the identifiers returned as response headers are logged, since they
# are how a streamed analysis can be re-read later
def test_log_stream_identifiers(caplog):
    mock_response = MagicMock()
    mock_response.headers = {
        "Eyeris-Request-Id": "req-1",
        "Eyeris-Request-Queue-Id": "queue-1",
        "Eyeris-Response-Id": "resp-1",
    }

    with caplog.at_level("INFO"):
        analysis_stream.log_stream_identifiers(mock_response)

    assert "req-1" in caplog.text
    assert "queue-1" in caplog.text
    assert "resp-1" in caplog.text


# Test that a stream with no data lines is reported rather than returning silently
def test_stream_analysis_empty_stream(caplog):
    mock_post, _ = build_streaming_response(lines=[])

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        with caplog.at_level("INFO"):
            text = analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert text == ""
    assert "No analysis" in caplog.text


# Test that missing identifier headers do not break the run
def test_log_stream_identifiers_missing_headers(caplog):
    mock_response = MagicMock()
    mock_response.headers = {}

    with caplog.at_level("INFO"):
        analysis_stream.log_stream_identifiers(mock_response)

    assert "N/A" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests


# Test that an HTTP error on the stream is logged and yields no text
def test_stream_analysis_http_error(caplog):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    mock_response.iter_lines.return_value = iter([])

    mock_post = MagicMock()
    mock_post.return_value.__enter__.return_value = mock_response
    mock_post.return_value.__exit__.return_value = False

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        with caplog.at_level("ERROR"):
            text = analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert text == ""
    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
def test_stream_analysis_connection_error(caplog):
    mock_post = MagicMock(side_effect=_requests.exceptions.ConnectionError("boom"))

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        with caplog.at_level("ERROR"):
            text = analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert text == ""
    assert "Unexpected error" in caplog.text


# Test that comments and named events other than progress/error never reach the text
def test_stream_analysis_ignores_comments_and_unknown_events():
    mock_post, _ = build_streaming_response(
        lines=[":keepalive", "", "event:ping", "data:{}", "", "data:real"]
    )

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        text = analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert text == "real"


# Test that a frame's data lines are joined with newlines and frames are joined
# with nothing, since each frame is one chunk of the answer
def test_stream_analysis_assembles_frames():
    mock_post, _ = build_streaming_response(
        lines=["data:# Title", "data:", "data:Wi-", "", "data:Fi is fine", ""]
    )

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        text = analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert text == "# Title\n\nWi-Fi is fine"


# Test that the progress event is logged as a status, not added to the text
def test_stream_analysis_progress_event_is_not_text(caplog):
    mock_post, _ = build_streaming_response(
        lines=["event:progress", 'data:{"stage":"generating"}', "", "data:answer", ""]
    )

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        with caplog.at_level("INFO"):
            text = analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert text == "answer"
    assert "generating" in caplog.text
    assert "stage" not in caplog.text


# Test that an error event raises with the partial text, so an incomplete
# analysis is never returned as if it were complete
def test_stream_analysis_error_event_raises_with_partial_text():
    mock_post, _ = build_streaming_response(
        lines=["data:partial", "", "event:error", 'data:{"reason":"timeout"}', ""]
    )

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        with pytest.raises(analysis_stream.StreamEndedEarly) as ended_early:
            analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert ended_early.value.reason == "timeout"
    assert ended_early.value.partial_text == "partial"


# Test that any reason other than timeout, or an unreadable one, is reported as failed
@pytest.mark.parametrize("data", ['{"reason":"failed"}', '{"reason":"other"}', "not json", "[]"])
def test_stream_analysis_error_event_reason_defaults_to_failed(data):
    mock_post, _ = build_streaming_response(lines=["event:error", f"data:{data}", ""])

    with patch("examples.eyeris.analysis_stream.requests.post", mock_post):
        with pytest.raises(analysis_stream.StreamEndedEarly) as ended_early:
            analysis_stream.stream_analysis("fake-token", "WIFI_CONGESTION_ANALYSIS", {})

    assert ended_early.value.reason == "failed"
    assert ended_early.value.partial_text == ""


def run_main(input_values):
    stream = MagicMock(return_value="text")
    applied = [
        patch("examples.eyeris.analysis_stream.get_token", return_value=("tok", 0)),
        patch("builtins.input", side_effect=input_values),
        patch("examples.eyeris.analysis_stream.stream_analysis", stream),
    ]
    for p in applied:
        p.start()
    try:
        analysis_stream.main()
    finally:
        for p in reversed(applied):
            p.stop()
    return stream


# Test main's happy path, including the agent and window it sends
def test_main_happy_path(caplog):
    with caplog.at_level("INFO"):
        stream = run_main(["3fa85f64-5717-4562-b3fc-2c963f66afa6", "WIFI_CONGESTION_ANALYSIS", "100", "200"])

    assert "streaming" in caplog.text
    input_data = stream.call_args.args[2]
    assert input_data["deviceIds"] == ["3fa85f64-5717-4562-b3fc-2c963f66afa6"]
    assert (input_data["from"], input_data["to"]) == (100, 200)


# Test that main exits with an error when the analysis stops early
def test_main_stream_ended_early_exits(caplog):
    applied = [
        patch("examples.eyeris.analysis_stream.get_token", return_value=("tok", 0)),
        patch("builtins.input", side_effect=["agent", "WIFI_CONGESTION_ANALYSIS", "", ""]),
        patch(
            "examples.eyeris.analysis_stream.stream_analysis",
            side_effect=analysis_stream.StreamEndedEarly("timeout", "partial"),
        ),
    ]
    for p in applied:
        p.start()
    try:
        with caplog.at_level("ERROR"):
            with pytest.raises(SystemExit) as exit_info:
                analysis_stream.main()
    finally:
        for p in reversed(applied):
            p.stop()

    assert exit_info.value.code == 1
    assert "incomplete" in caplog.text


# Test that an empty agent id exits
def test_main_empty_agent_id_exits():
    with pytest.raises(SystemExit):
        run_main(["  "])


# Test that an unknown prompt type is passed through with a warning, since the
# specification puts no fixed list on promptTypeKey
def test_main_unknown_prompt_type_warns(caplog):
    with caplog.at_level("WARNING"):
        run_main(["agent", "SIDEWAYS", "", ""])

    assert "not one of the known prompt types" in caplog.text


# Test that an empty prompt type still exits
def test_main_empty_prompt_type_exits():
    with pytest.raises(SystemExit):
        run_main(["agent", "  "])


# Test that non-numeric times exit
def test_main_bad_times_exit():
    with pytest.raises(SystemExit):
        run_main(["agent", "WIFI_CONGESTION_ANALYSIS", "abc", "def"])


# Test that a start time at or after the end time exits
def test_main_inverted_window_exits():
    with pytest.raises(SystemExit):
        run_main(["agent", "WIFI_CONGESTION_ANALYSIS", "200", "100"])
