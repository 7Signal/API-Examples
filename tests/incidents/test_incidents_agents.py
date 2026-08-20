import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.incidents import incidents_agents

# The list endpoint nests the threshold fields under "thresholds"
NESTED_INCIDENT = {
    "id": "b7c19d3a-4e82-4f16-9d05-3a8c2f7b1e64",
    "startTimestamp": "2026-08-17T14:12:00.000Z",
    "endTimestamp": "2026-08-17T14:38:00.000Z",
    "timestampDeterminedToBeIncident": "2026-08-17T14:22:00.000Z",
    "organizationName": "globalcorp",
    "type": "CONNECTION",
    "location": "4d1e8b7c-9a35-4c72-b6f0-2e5a9d3c8f41",
    "locationName": "Cleveland HQ - Floor 3",
    "network": "CorpWiFi",
    "band": 5.00,
    "countImpacted": 12,
    "populationCount": 84,
    "thresholds": {
        "warningThreshold": 80,
        "criticalThreshold": 60,
        "minIncidentDurationMinutes": 10,
    },
}

# The single-incident endpoint returns the same fields flattened
FLAT_INCIDENT = {
    "id": "b7c19d3a-4e82-4f16-9d05-3a8c2f7b1e64",
    "startTimestamp": "2026-08-17T14:12:00.000Z",
    "locationName": "Cleveland HQ - Floor 3",
    "network": "CorpWiFi",
    "band": 5.00,
    "countImpacted": 12,
    "populationCount": 84,
    "warningThreshold": 80,
    "criticalThreshold": 60,
    "minIncidentDurationMinutes": 10,
}

SAMPLE_LIST = {
    "range": {
        "from": 1755426000000,
        "to": 1755512400000,
        "total": 1,
        "durationAsString": "24 hours",
    },
    "results": [NESTED_INCIDENT],
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(incidents_agents, "list_incidents")
    assert hasattr(incidents_agents, "get_incident")
    assert hasattr(incidents_agents, "get_threshold")
    assert hasattr(incidents_agents, "display_incidents")


# Test that list_incidents handles a successful API call
@patch("examples.incidents.incidents_agents.requests.get")
def test_list_incidents_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = incidents_agents.list_incidents("fake-token")

    assert data["results"][0]["id"] == NESTED_INCIDENT["id"]


# Test that the location filter uses the API's snake_case parameter name
@patch("examples.incidents.incidents_agents.requests.get")
def test_list_incidents_uses_snake_case_location_id(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    location_id = "4d1e8b7c-9a35-4c72-b6f0-2e5a9d3c8f41"
    incidents_agents.list_incidents("fake-token", location_id=location_id)

    params = mock_get.call_args.kwargs["params"]
    # An unrecognised name is silently ignored by the API, so the exact
    # spelling matters more than usual here
    assert params["location_id"] == location_id
    assert "locationId" not in params


# Test that a window wider than the API's 30 day limit is refused up front
@patch("examples.incidents.incidents_agents.requests.get")
def test_list_incidents_rejects_window_over_30_days(mock_get, caplog):
    to_ms = 1755512400000
    from_ms = to_ms - (31 * 24 * 60 * 60 * 1000)

    with caplog.at_level("ERROR"):
        data = incidents_agents.list_incidents("fake-token", from_ms=from_ms, to_ms=to_ms)

    assert data is None
    mock_get.assert_not_called()
    assert "30 days" in caplog.text


# Test that get_incident returns None on 404 rather than raising
@patch("examples.incidents.incidents_agents.requests.get")
def test_get_incident_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    assert incidents_agents.get_incident("fake-token", "missing-id") is None


# Test that get_threshold reads the nested shape from the list endpoint
def test_get_threshold_nested():
    assert incidents_agents.get_threshold(NESTED_INCIDENT, "criticalThreshold") == 60


# Test that get_threshold reads the flat shape from the single-incident endpoint
def test_get_threshold_flat():
    assert incidents_agents.get_threshold(FLAT_INCIDENT, "criticalThreshold") == 60


# Test that a threshold that is absent in either shape returns None
def test_get_threshold_missing():
    assert incidents_agents.get_threshold({"id": "abc"}, "criticalThreshold") is None


# Test that display_incidents logs the key incident details
def test_display_incidents(caplog):
    with caplog.at_level("INFO"):
        incidents_agents.display_incidents(SAMPLE_LIST)

    assert "Cleveland HQ - Floor 3" in caplog.text
    assert "CorpWiFi" in caplog.text
    assert "12" in caplog.text
    assert "84" in caplog.text


# Test that a single flat incident can be displayed through the same helper
def test_display_incidents_accepts_flat_incident(caplog):
    with caplog.at_level("INFO"):
        incidents_agents.display_incidents({"results": [FLAT_INCIDENT]})

    assert "Cleveland HQ - Floor 3" in caplog.text


# Test that display handles missing/partial data gracefully
def test_display_incidents_partial_data(caplog):
    with caplog.at_level("INFO"):
        incidents_agents.display_incidents({"results": [{"id": "abc", "type": "COVERAGE"}]})

    assert "COVERAGE" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_incidents_empty(caplog):
    with caplog.at_level("INFO"):
        incidents_agents.display_incidents({"results": [], "range": {}})

    assert "No agent incidents" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests


def http_error_response(text="Bad Request"):
    r = MagicMock()
    r.status_code = 400
    r.text = text
    r.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return r


# Test that HTTP errors on the read calls return None
@patch("examples.incidents.incidents_agents.requests.get")
def test_read_calls_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert incidents_agents.list_incidents("fake-token") is None
        assert incidents_agents.get_incident("fake-token", "abc") is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch("examples.incidents.incidents_agents.requests.get",
       side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_incidents_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert incidents_agents.list_incidents("fake-token") is None

    assert "Unexpected error" in caplog.text


# Test that the window and order filters are forwarded
@patch("examples.incidents.incidents_agents.requests.get")
def test_list_incidents_forwards_window_and_order(mock_get):
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = SAMPLE_LIST
    r.raise_for_status = MagicMock()
    mock_get.return_value = r

    incidents_agents.list_incidents("fake-token", from_ms=1, to_ms=2, order="desc")

    params = mock_get.call_args.kwargs["params"]
    assert params["from"] == 1
    assert params["to"] == 2
    assert params["order"] == "desc"


# Test that an absent end timestamp is reported as absent rather than being
# interpreted as "still running" - the API defines no active/resolved flag for
# agent incidents, so inferring one would be inventing semantics
def test_display_incidents_missing_end_timestamp(caplog):
    ongoing = {"results": [dict(NESTED_INCIDENT, endTimestamp=None)]}

    with caplog.at_level("INFO"):
        incidents_agents.display_incidents(ongoing)

    assert "not reported" in caplog.text
    assert "still in progress" not in caplog.text


# Test that impact is reported without a population count
def test_display_incidents_without_population(caplog):
    no_pop = {"results": [{"id": "a", "countImpacted": 3}]}

    with caplog.at_level("INFO"):
        incidents_agents.display_incidents(no_pop)

    assert "3 agents" in caplog.text


def run_main(input_values, **extra):
    applied = [
        patch("examples.incidents.incidents_agents.get_token", return_value=("tok", 0)),
        patch("builtins.input", side_effect=input_values),
    ]
    for target, value in extra.items():
        applied.append(patch(f"examples.incidents.incidents_agents.{target}", return_value=value))
    for p in applied:
        p.start()
    try:
        incidents_agents.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main's exit branch
def test_main_exit_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["5"])

    assert "Nothing to do" in caplog.text


# Test main's default 24 hour listing
def test_main_default_window_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["1"], list_incidents=SAMPLE_LIST)

    assert "Cleveland HQ - Floor 3" in caplog.text


# Test main's per-location branch
def test_main_location_branch():
    run_main(["2", "loc-1"], list_incidents=SAMPLE_LIST)


# Test that an empty location id exits
def test_main_location_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["2", " "])


# Test main's custom window branch, including the default when Enter is pressed
def test_main_custom_window_branch():
    run_main(["3", "", ""], list_incidents=SAMPLE_LIST)


# Test that non-numeric window values exit
def test_main_custom_window_bad_values_exit():
    with pytest.raises(SystemExit):
        run_main(["3", "abc", "def"])


# Test that an inverted window exits
def test_main_custom_window_inverted_exits():
    with pytest.raises(SystemExit):
        run_main(["3", "200", "100"])


# Test main's fetch-single branch
def test_main_fetch_single_branch():
    run_main(["4", NESTED_INCIDENT["id"]], get_incident=FLAT_INCIDENT)


# Test that an empty incident id exits
def test_main_fetch_single_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["4", " "])
