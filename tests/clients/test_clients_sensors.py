import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.clients import clients_sensors

SAMPLE_LIST = {
    "range": {
        "from": 1752920400000,
        "to": 1755512400000,
        "total": 2,
        "durationAsString": "30 days",
    },
    "results": [
        {
            "id": 90714,
            "name": "ENG-LAPTOP-114",
            "macAddress": "a4:83:e7:1b:5c:90",
            "description": "Engineering loaner laptop",
            "user": "jdoe",
            "vendor": "Apple, Inc.",
        },
        {
            "id": 90715,
            "name": None,
            "macAddress": "00:1b:63:84:45:e6",
            "description": None,
            "user": None,
            "vendor": "Zebra Technologies",
        },
    ],
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(clients_sensors, "list_clients")
    assert hasattr(clients_sensors, "display_clients")


# Test that list_clients handles a successful API call
@patch("examples.clients.clients_sensors.requests.get")
def test_list_clients_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = clients_sensors.list_clients("fake-token")

    assert len(data["results"]) == 2


# Test that the mac and vendor filters are passed through
@patch("examples.clients.clients_sensors.requests.get")
def test_list_clients_passes_filters(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    clients_sensors.list_clients("fake-token", mac="a4:83:e7", vendor="apple")

    params = mock_get.call_args.kwargs["params"]
    assert params["mac"] == "a4:83:e7"
    assert params["vendor"] == "apple"


# Test that a window wider than the API's 90 day limit is refused up front
@patch("examples.clients.clients_sensors.requests.get")
def test_list_clients_rejects_window_over_90_days(mock_get, caplog):
    to_ms = 1755512400000
    from_ms = to_ms - (91 * 24 * 60 * 60 * 1000)

    with caplog.at_level("ERROR"):
        data = clients_sensors.list_clients("fake-token", from_ms=from_ms, to_ms=to_ms)

    assert data is None
    mock_get.assert_not_called()
    assert "90 days" in caplog.text


# Test that display logs the client details
def test_display_clients(caplog):
    with caplog.at_level("INFO"):
        clients_sensors.display_clients(SAMPLE_LIST)

    assert "ENG-LAPTOP-114" in caplog.text
    assert "Apple, Inc." in caplog.text
    assert "Zebra Technologies" in caplog.text


# Test that an unnamed client falls back to its MAC address rather than showing None
def test_display_clients_handles_null_name(caplog):
    with caplog.at_level("INFO"):
        clients_sensors.display_clients(SAMPLE_LIST)

    assert "00:1b:63:84:45:e6" in caplog.text
    assert "None" not in caplog.text


# Test that display handles missing/partial data gracefully
def test_display_clients_partial_data(caplog):
    partial = {"results": [{"id": 1, "macAddress": "aa:bb:cc:dd:ee:ff"}]}

    with caplog.at_level("INFO"):
        clients_sensors.display_clients(partial)

    assert "aa:bb:cc:dd:ee:ff" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_clients_empty(caplog):
    with caplog.at_level("INFO"):
        clients_sensors.display_clients({"results": [], "range": {}})

    assert "No sensor clients" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests

MODULE = "examples.clients.clients_sensors"


def http_error_response():
    r = MagicMock()
    r.status_code = 400
    r.text = "Bad Request"
    r.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return r


# Test that an HTTP error returns None
@patch(f"{MODULE}.requests.get")
def test_list_clients_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert clients_sensors.list_clients("fake-token") is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch(f"{MODULE}.requests.get", side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_clients_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert clients_sensors.list_clients("fake-token") is None

    assert "Unexpected error" in caplog.text


# Test that the window bounds are forwarded
@patch(f"{MODULE}.requests.get")
def test_list_clients_forwards_window(mock_get):
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = SAMPLE_LIST
    r.raise_for_status = MagicMock()
    mock_get.return_value = r

    clients_sensors.list_clients("fake-token", from_ms=1, to_ms=2)

    params = mock_get.call_args.kwargs["params"]
    assert params["from"] == 1
    assert params["to"] == 2


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
        clients_sensors.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main's happy path with no filters and default window
def test_main_happy_path(caplog):
    with caplog.at_level("INFO"):
        run_main(["", "", "", ""], list_clients=SAMPLE_LIST)

    assert "ENG-LAPTOP-114" in caplog.text


# Test main with both filters supplied
def test_main_with_filters():
    run_main(["a4:83:e7", "apple", "", ""], list_clients=SAMPLE_LIST)


# Test that non-numeric window values exit
def test_main_bad_window_exits():
    with pytest.raises(SystemExit):
        run_main(["", "", "abc", "def"])


# Test that an inverted window exits
def test_main_inverted_window_exits():
    with pytest.raises(SystemExit):
        run_main(["", "", "200", "100"])
