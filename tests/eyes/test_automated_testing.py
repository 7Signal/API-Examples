import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.eyes import automated_testing

SAMPLE_STATUS = {
    "eyeName": "Eye-Cleveland-03",
    "testProfileName": "Standard Branch",
    "testStatus": "RUNNING",
    "currentTestStatus": "Test started",
    "currentAccessPoint": "AP-CLE-3-North",
    "currentTestRunning": "SPEEDTEST",
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(automated_testing, "get_automated_testing_status")
    assert hasattr(automated_testing, "set_automated_testing")
    assert hasattr(automated_testing, "display_automated_testing_status")


# Test that the status endpoint is read correctly
@patch("examples.eyes.automated_testing.requests.get")
def test_get_automated_testing_status_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_STATUS
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    status = automated_testing.get_automated_testing_status("fake-token", 1042)

    assert status["testStatus"] == "RUNNING"
    assert "/eyes/sensors/1042/automated-testing" in mock_get.call_args.args[0]


# Test that an unknown sensor returns None rather than raising
@patch("examples.eyes.automated_testing.requests.get")
def test_get_automated_testing_status_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    assert automated_testing.get_automated_testing_status("fake-token", 9999) is None


# Test that declining the confirmation prompt aborts the change entirely.
# Stopping automated testing halts the measurements KPIs are built from.
@patch("examples.eyes.automated_testing.requests.post")
@patch("builtins.input", return_value="no")
def test_set_automated_testing_aborts_without_confirmation(mock_input, mock_post):
    result = automated_testing.set_automated_testing(
        "fake-token", 1042, "STOP_AUTOMATED_TESTING"
    )

    assert result is None
    mock_post.assert_not_called()


# Test that confirming sends the action in the request body
@patch("examples.eyes.automated_testing.requests.post")
@patch("builtins.input", return_value="yes")
def test_set_automated_testing_sends_action(mock_input, mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"action": "START_AUTOMATED_TESTING", "result": "SUCCESS"}
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = automated_testing.set_automated_testing(
        "fake-token", 1042, "START_AUTOMATED_TESTING"
    )

    assert mock_post.call_args.kwargs["json"] == {"action": "START_AUTOMATED_TESTING"}
    assert result["result"] == "SUCCESS"


# Test that an unsupported action is refused before any request
@patch("examples.eyes.automated_testing.requests.post")
@patch("builtins.input", return_value="yes")
def test_set_automated_testing_rejects_invalid_action(mock_input, mock_post, caplog):
    with caplog.at_level("ERROR"):
        result = automated_testing.set_automated_testing("fake-token", 1042, "PAUSE")

    assert result is None
    mock_post.assert_not_called()


# Test that display logs the current state
def test_display_automated_testing_status(caplog):
    with caplog.at_level("INFO"):
        automated_testing.display_automated_testing_status(SAMPLE_STATUS)

    assert "Eye-Cleveland-03" in caplog.text
    assert "RUNNING" in caplog.text
    assert "AP-CLE-3-North" in caplog.text


# Test that a RUNNING sensor is flagged as blocking on-demand tests
def test_display_automated_testing_status_warns_when_running(caplog):
    with caplog.at_level("INFO"):
        automated_testing.display_automated_testing_status(SAMPLE_STATUS)

    assert "on-demand" in caplog.text.lower()


# Test that the transient STOPPING state is explained rather than shown bare
def test_display_automated_testing_status_explains_stopping(caplog):
    stopping = dict(SAMPLE_STATUS, testStatus="STOPPING")

    with caplog.at_level("INFO"):
        automated_testing.display_automated_testing_status(stopping)

    assert "still winding down" in caplog.text.lower()


# Test that display handles missing/partial data gracefully
def test_display_automated_testing_status_partial_data(caplog):
    with caplog.at_level("INFO"):
        automated_testing.display_automated_testing_status({"testStatus": "STOPPED"})

    assert "STOPPED" in caplog.text


# Test that an absent status is reported rather than failing
def test_display_automated_testing_status_empty(caplog):
    with caplog.at_level("INFO"):
        automated_testing.display_automated_testing_status(None)

    assert "No automated testing status" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests

MODULE = "examples.eyes.automated_testing"


def http_error_response():
    r = MagicMock()
    r.status_code = 400
    r.text = "Bad Request"
    r.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return r


# Test that an HTTP error on the status read returns None
@patch(f"{MODULE}.requests.get")
def test_get_status_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert automated_testing.get_automated_testing_status("fake-token", 1) is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch(f"{MODULE}.requests.get", side_effect=_requests.exceptions.ConnectionError("boom"))
def test_get_status_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert automated_testing.get_automated_testing_status("fake-token", 1) is None

    assert "Unexpected error" in caplog.text


# Test that a stop against an unknown sensor is reported rather than raised
@patch(f"{MODULE}.requests.post")
@patch("builtins.input", return_value="yes")
def test_set_automated_testing_404(mock_input, mock_post, caplog):
    r = MagicMock()
    r.status_code = 404
    mock_post.return_value = r

    with caplog.at_level("INFO"):
        assert automated_testing.set_automated_testing(
            "fake-token", 9999, "STOP_AUTOMATED_TESTING"
        ) is None

    assert "No sensor found" in caplog.text


# Test that an HTTP error on the change returns None
@patch(f"{MODULE}.requests.post")
@patch("builtins.input", return_value="yes")
def test_set_automated_testing_http_error(mock_input, mock_post):
    mock_post.return_value = http_error_response()

    assert automated_testing.set_automated_testing(
        "fake-token", 1042, "START_AUTOMATED_TESTING"
    ) is None


# Test that the stop action warns about the data gap before prompting
@patch(f"{MODULE}.requests.post")
@patch("builtins.input", return_value="no")
def test_set_automated_testing_stop_warns(mock_input, mock_post, caplog):
    with caplog.at_level("INFO"):
        automated_testing.set_automated_testing("fake-token", 1042, "STOP_AUTOMATED_TESTING")

    assert "data gaps" in caplog.text.lower()


def run_main(input_values, **extra):
    applied = [
        patch(f"{MODULE}.get_token", return_value=("tok", 0)),
        patch(f"{MODULE}.time.sleep", return_value=None),
        patch("builtins.input", side_effect=input_values),
    ]
    for target, value in extra.items():
        applied.append(patch(f"{MODULE}.{target}", return_value=value))
    for p in applied:
        p.start()
    try:
        automated_testing.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test that an empty sensor id exits
def test_main_empty_sensor_exits():
    with pytest.raises(SystemExit):
        run_main([" "])


# Test that main exits when the sensor is unknown
def test_main_unknown_sensor_exits():
    with pytest.raises(SystemExit):
        run_main(["9999"], get_automated_testing_status=None)


# Test main's do-nothing branch
def test_main_exit_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["1042", "3"], get_automated_testing_status=SAMPLE_STATUS)

    assert "Nothing to do" in caplog.text


# Test main's start branch, which re-checks the status afterwards
def test_main_start_branch():
    run_main(
        ["1042", "1"],
        get_automated_testing_status=SAMPLE_STATUS,
        set_automated_testing={"action": "START_AUTOMATED_TESTING", "result": "SUCCESS"},
    )


# Test main's stop branch
def test_main_stop_branch():
    run_main(
        ["1042", "2"],
        get_automated_testing_status=SAMPLE_STATUS,
        set_automated_testing={"action": "STOP_AUTOMATED_TESTING", "result": "SUCCESS"},
    )


# Test that a declined change stops before the re-check
def test_main_declined_change():
    run_main(
        ["1042", "1"],
        get_automated_testing_status=SAMPLE_STATUS,
        set_automated_testing=None,
    )
