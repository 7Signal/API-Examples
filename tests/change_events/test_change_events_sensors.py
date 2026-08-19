import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.change_events import change_events_sensors as ce

SAMPLE_LIST = {
    "results": [
        {
            "timestamp": 1750821376000,
            "name": "TEST_PROFILE_CHANGED",
            "element": "Eye-Cleveland-03",
            "parentElement": "Cleveland HQ - Floor 3",
            "description": "Test profile changed from 'Standard Branch' to 'High Frequency'",
        }
    ],
    "pagination": {"perPage": 10, "page": 1, "total": 1, "pages": 1},
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(ce, "list_change_events")
    assert hasattr(ce, "validate_filter_combination")
    assert hasattr(ce, "display_change_events")


# Test that each documented filter combination is accepted
def test_validate_filter_combination_accepts_supported_combinations():
    assert ce.validate_filter_combination(access_point_id=1) is None
    assert ce.validate_filter_combination(sensor_id=2) is None
    assert ce.validate_filter_combination(access_point_id=1, sensor_id=2) is None
    assert ce.validate_filter_combination(network_id=3) is None
    assert ce.validate_filter_combination(network_id=3, service_area_id=4) is None
    # No element filter at all is allowed
    assert ce.validate_filter_combination() is None


# Test that a service area on its own is rejected, since it is only meaningful
# alongside a network
def test_validate_filter_combination_rejects_lone_service_area():
    problem = ce.validate_filter_combination(service_area_id=4)

    assert problem is not None
    assert "networkId" in problem


# Test that mixing a network with an access point is rejected
def test_validate_filter_combination_rejects_network_with_access_point():
    problem = ce.validate_filter_combination(network_id=3, access_point_id=1)

    assert problem is not None


# Test that list_change_events handles a successful API call
@patch("examples.change_events.change_events_sensors.requests.get")
def test_list_change_events_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = ce.list_change_events("fake-token", sensor_id=1042)

    assert data["results"][0]["name"] == "TEST_PROFILE_CHANGED"
    assert mock_get.call_args.kwargs["params"]["sensorId"] == 1042


# Test that an unsupported filter combination is refused before any request
@patch("examples.change_events.change_events_sensors.requests.get")
def test_list_change_events_rejects_bad_combination(mock_get, caplog):
    with caplog.at_level("ERROR"):
        data = ce.list_change_events("fake-token", service_area_id=4)

    assert data is None
    mock_get.assert_not_called()


# Test that display logs the event details
def test_display_change_events(caplog):
    with caplog.at_level("INFO"):
        ce.display_change_events(SAMPLE_LIST)

    assert "TEST_PROFILE_CHANGED" in caplog.text
    assert "Eye-Cleveland-03" in caplog.text
    assert "Cleveland HQ - Floor 3" in caplog.text


# Test that the epoch timestamp is rendered as a readable date
def test_display_change_events_formats_timestamp(caplog):
    with caplog.at_level("INFO"):
        ce.display_change_events(SAMPLE_LIST)

    assert "2025-06-25" in caplog.text
    assert "UTC" in caplog.text


# Test that display handles missing/partial data gracefully
def test_display_change_events_partial_data(caplog):
    partial = {"results": [{"name": "SOMETHING_CHANGED"}]}

    with caplog.at_level("INFO"):
        ce.display_change_events(partial)

    assert "SOMETHING_CHANGED" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_change_events_empty(caplog):
    with caplog.at_level("INFO"):
        ce.display_change_events({"results": [], "pagination": {}})

    assert "No change events" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests

MODULE = "examples.change_events.change_events_sensors"


def http_error_response():
    r = MagicMock()
    r.status_code = 400
    r.text = "Bad Request"
    r.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return r


# Test that an HTTP error returns None
@patch(f"{MODULE}.requests.get")
def test_list_change_events_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert ce.list_change_events("fake-token", sensor_id=1) is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch(f"{MODULE}.requests.get", side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_change_events_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert ce.list_change_events("fake-token", sensor_id=1) is None

    assert "Unexpected error" in caplog.text


# Test that every accepted filter is forwarded with the API's parameter names
@patch(f"{MODULE}.requests.get")
def test_list_change_events_forwards_filters(mock_get):
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = SAMPLE_LIST
    r.raise_for_status = MagicMock()
    mock_get.return_value = r

    ce.list_change_events("fake-token", network_id=3, service_area_id=4, from_ms=1, to_ms=2)

    params = mock_get.call_args.kwargs["params"]
    assert params["networkId"] == 3
    assert params["serviceAreaId"] == 4
    assert params["from"] == 1
    assert params["to"] == 2


# Test that the timestamp formatter tolerates junk
def test_format_timestamp_handles_junk():
    assert ce.format_timestamp(None) == "N/A"
    assert ce.format_timestamp("nope") == "nope"


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
        ce.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test each supported filter combination through main
def test_main_sensor_only(caplog):
    with caplog.at_level("INFO"):
        run_main(["1", "1042", "", ""], list_change_events=SAMPLE_LIST)

    assert "TEST_PROFILE_CHANGED" in caplog.text


def test_main_access_point_only():
    run_main(["2", "5517", "", ""], list_change_events=SAMPLE_LIST)


def test_main_access_point_with_sensor():
    run_main(["3", "5517", "1042", "", ""], list_change_events=SAMPLE_LIST)


def test_main_network_only():
    run_main(["4", "77", "", ""], list_change_events=SAMPLE_LIST)


def test_main_network_with_service_area():
    run_main(["5", "77", "88", "", ""], list_change_events=SAMPLE_LIST)


# Test that an unrecognised menu choice exits
def test_main_bad_choice_exits():
    with pytest.raises(SystemExit):
        run_main(["9"])


# Test that omitting the element id exits
def test_main_missing_element_id_exits():
    with pytest.raises(SystemExit):
        run_main(["1", " "])


# Test that non-numeric window values exit
def test_main_bad_window_exits():
    with pytest.raises(SystemExit):
        run_main(["1", "1042", "abc", "def"])


# Test that an inverted window exits
def test_main_inverted_window_exits():
    with pytest.raises(SystemExit):
        run_main(["1", "1042", "200", "100"])
