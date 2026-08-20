import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.on_demand_tests import active_tests

SAMPLE_RESPONSE = {
    "pagination": {"perPage": 20, "page": 0, "total": 2, "pages": 1},
    "items": [
        {
            "id": "f0c8a3d1-6b74-4e29-9a5c-31d7b8e05f62",
            "testKey": "5c9a1e84-2f70-4b3d-8e16-7a0c4d9b2f58",
            "testId": 884213,
            "testType": "SPEEDTEST",
            "sensorId": 1042,
            "sensorName": "Eye-Cleveland-03",
            "apId": 5517,
            "band": "5",
            "channel": 36,
            "runStatus": "IN_PROGRESS",
            "errorCode": 0,
            "createdAt": "2026-08-18T13:04:11Z",
        },
        {
            "id": "a1b2c3d4-6b74-4e29-9a5c-31d7b8e05f63",
            "testId": 884190,
            "testType": "SPEEDTEST",
            "sensorId": 1042,
            "band": "5",
            "runStatus": "COMPLETE",
            "errorCode": 0,
            "createdAt": "2026-08-18T12:44:02Z",
        },
    ],
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(active_tests, "list_active_tests")
    assert hasattr(active_tests, "display_active_tests")


# Test that list_active_tests handles a successful API call
@patch("examples.on_demand_tests.active_tests.requests.get")
def test_list_active_tests_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = active_tests.list_active_tests("fake-token", 1042, "SPEEDTEST")

    assert data["items"][0]["testId"] == 884213
    params = mock_get.call_args.kwargs["params"]
    assert params["sensorId"] == 1042
    assert params["testType"] == "SPEEDTEST"


# Test that paging is zero-based on this endpoint, unlike most others in the API
@patch("examples.on_demand_tests.active_tests.requests.get")
def test_list_active_tests_paging_is_zero_based(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    active_tests.list_active_tests("fake-token", 1042, "SPEEDTEST")

    params = mock_get.call_args.kwargs["params"]
    assert params["page"] == 0
    # This endpoint uses `size`, not `perPage`
    assert "size" in params
    assert "perPage" not in params


# Test that an unsupported test type is refused before any request
@patch("examples.on_demand_tests.active_tests.requests.get")
def test_list_active_tests_rejects_invalid_test_type(mock_get, caplog):
    with caplog.at_level("ERROR"):
        data = active_tests.list_active_tests("fake-token", 1042, "PACKET_CAPTURE")

    assert data is None
    mock_get.assert_not_called()


# Test that the optional filters are passed through
@patch("examples.on_demand_tests.active_tests.requests.get")
def test_list_active_tests_passes_optional_filters(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    active_tests.list_active_tests(
        "fake-token", 1042, "SPEEDTEST", channel=36, ap_id=5517, band="5"
    )

    params = mock_get.call_args.kwargs["params"]
    assert params["channel"] == 36
    assert params["apId"] == 5517
    assert params["band"] == "5"


# Test that display reads the `items` array rather than `results`
def test_display_active_tests(caplog):
    with caplog.at_level("INFO"):
        active_tests.display_active_tests(SAMPLE_RESPONSE)

    assert "884213" in caplog.text
    assert "SPEEDTEST" in caplog.text
    assert "IN_PROGRESS" in caplog.text


# Test that filtering to only in-flight tests drops the completed ones
def test_display_active_tests_in_progress_only(caplog):
    with caplog.at_level("INFO"):
        active_tests.display_active_tests(SAMPLE_RESPONSE, in_progress_only=True)

    assert "884213" in caplog.text
    assert "884190" not in caplog.text


# Test that display handles missing/partial data gracefully
def test_display_active_tests_partial_data(caplog):
    partial = {"items": [{"testId": 1, "testType": "PING"}]}

    with caplog.at_level("INFO"):
        active_tests.display_active_tests(partial)

    assert "PING" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_active_tests_empty(caplog):
    with caplog.at_level("INFO"):
        active_tests.display_active_tests({"items": [], "pagination": {}})

    assert "No active tests" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests

MODULE = "examples.on_demand_tests.active_tests"


def http_error_response():
    r = MagicMock()
    r.status_code = 400
    r.text = "Bad Request"
    r.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return r


# Test that an HTTP error returns None
@patch(f"{MODULE}.requests.get")
def test_list_active_tests_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert active_tests.list_active_tests("fake-token", 1042, "SPEEDTEST") is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch(f"{MODULE}.requests.get", side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_active_tests_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert active_tests.list_active_tests("fake-token", 1042, "SPEEDTEST") is None

    assert "Unexpected error" in caplog.text


# Test that an unsupported band is refused before any request
@patch(f"{MODULE}.requests.get")
def test_list_active_tests_rejects_bad_band(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert active_tests.list_active_tests(
            "fake-token", 1042, "SPEEDTEST", band="60"
        ) is None

    mock_get.assert_not_called()


# Test that the time bounds are forwarded
@patch(f"{MODULE}.requests.get")
def test_list_active_tests_forwards_window(mock_get):
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = SAMPLE_RESPONSE
    r.raise_for_status = MagicMock()
    mock_get.return_value = r

    active_tests.list_active_tests("fake-token", 1042, "SPEEDTEST", start=1, end=2)

    params = mock_get.call_args.kwargs["params"]
    assert params["start"] == 1
    assert params["end"] == 2


# Test that a genuine error code is surfaced while errorCode 0 is not
def test_display_active_tests_reports_errors(caplog):
    failed = {
        "items": [
            {"testId": 1, "testType": "PING", "runStatus": "ERROR",
             "errorCode": 7, "errorMessage": "unreachable"},
        ]
    }

    with caplog.at_level("INFO"):
        active_tests.display_active_tests(failed)

    assert "unreachable" in caplog.text


def run_main(input_values, **extra):
    applied = [
        patch(f"{MODULE}.get_token", return_value=("tok", 0)),
        patch("builtins.input", side_effect=input_values),
    ]
    for target, value in extra.items():
        applied.append(patch(f"{MODULE}.{target}", return_value=value))
    for p in applied:
        p.start()
    try:
        active_tests.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main's happy path
def test_main_happy_path(caplog):
    with caplog.at_level("INFO"):
        run_main(["1042", "SPEEDTEST", "no", ""], list_active_tests=SAMPLE_RESPONSE)

    assert "884213" in caplog.text


# Test main filtering to in-progress tests only
def test_main_in_progress_only(caplog):
    with caplog.at_level("INFO"):
        run_main(["1042", "SPEEDTEST", "yes", ""], list_active_tests=SAMPLE_RESPONSE)

    assert "884190" not in caplog.text


# Test that an empty sensor id exits
def test_main_empty_sensor_exits():
    with pytest.raises(SystemExit):
        run_main([" "])


# Test that a non-numeric sensor id exits
def test_main_bad_sensor_exits():
    with pytest.raises(SystemExit):
        run_main(["not-a-number"])


# Test that an unsupported test type exits
def test_main_bad_test_type_exits():
    with pytest.raises(SystemExit):
        run_main(["1042", "PACKET_CAPTURE"])


# Test that a non-numeric start time exits
def test_main_bad_start_exits():
    with pytest.raises(SystemExit):
        run_main(["1042", "SPEEDTEST", "no", "abc"])
