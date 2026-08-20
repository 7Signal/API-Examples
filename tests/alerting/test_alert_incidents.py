import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.alerting import alert_incidents

SAMPLE_INCIDENT = {
    "id": "9c81f0a7-3d6e-4b12-8f55-71ae4c2b9d08",
    "ticketId": "INC0012345",
    "ruleId": "3f2b9c1e-58a4-4d2f-9b71-2c0e5a7d1f34",
    "metric": "client_health_score",
    "dimensionSet": ["network", "band"],
    "dimensionKey": "CorpWiFi|5",
    "startedAt": 1755512400000,
    "resolvedAt": 1755519600000,
    "resolutionReason": "cleared",
    "triggerValue": 61.4,
    "resolveValue": 78.2,
    "snapshot": {
        "thresholdValue": 70.0,
        "thresholdOperator": "<",
        "aggregationFunction": "avg",
        "pendingPeriodSeconds": 600,
    },
}

SAMPLE_LIST = {
    "results": [SAMPLE_INCIDENT],
    "pagination": {"perPage": 10, "page": 1, "total": 1, "pages": 1},
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(alert_incidents, "list_incidents")
    assert hasattr(alert_incidents, "get_incidents_summary")
    assert hasattr(alert_incidents, "get_incidents_by_rule")
    assert hasattr(alert_incidents, "get_incident")
    assert hasattr(alert_incidents, "resolve_incident")
    assert hasattr(alert_incidents, "display_incidents")


# Test that list_incidents handles a successful API call and passes filters through
@patch("examples.alerting.alert_incidents.requests.get")
def test_list_incidents_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = alert_incidents.list_incidents("fake-token", status="active")

    assert data["results"][0]["id"] == SAMPLE_INCIDENT["id"]
    assert mock_get.call_args.kwargs["params"]["status"] == "active"
    assert mock_get.call_args.kwargs["params"]["page"] == 1


# Test that the summary endpoint is read correctly
@patch("examples.alerting.alert_incidents.requests.get")
def test_get_incidents_summary_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"totalCount": 148, "activeCount": 6}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    summary = alert_incidents.get_incidents_summary("fake-token")

    assert summary["activeCount"] == 6


# Test that the by-rule endpoint is handled as a bare array, not a results envelope
@patch("examples.alerting.alert_incidents.requests.get")
def test_get_incidents_by_rule_returns_list(mock_get):
    sample = [
        {
            "ruleId": "3f2b9c1e-58a4-4d2f-9b71-2c0e5a7d1f34",
            "rule": {"metric": "client_health_score", "thresholdValue": 70.0, "thresholdOperator": "<"},
            "incidentCount": 42,
            "activeCount": 3,
        }
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    rows = alert_incidents.get_incidents_by_rule("fake-token")

    assert isinstance(rows, list)
    assert rows[0]["incidentCount"] == 42


# Test that get_incident returns None on 404 rather than raising
@patch("examples.alerting.alert_incidents.requests.get")
def test_get_incident_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    assert alert_incidents.get_incident("fake-token", "missing-id") is None


# Test that declining the confirmation prompt aborts the resolve entirely
@patch("examples.alerting.alert_incidents.requests.post")
@patch("builtins.input", return_value="no")
def test_resolve_incident_aborts_without_confirmation(mock_input, mock_post):
    resolved = alert_incidents.resolve_incident("fake-token", SAMPLE_INCIDENT["id"])

    assert resolved is False
    mock_post.assert_not_called()


# Test that confirming the prompt issues the resolve
@patch("examples.alerting.alert_incidents.requests.post")
@patch("builtins.input", return_value="yes")
def test_resolve_incident_when_confirmed(mock_input, mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = dict(SAMPLE_INCIDENT, resolutionReason="cleared_by_user")
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    resolved = alert_incidents.resolve_incident("fake-token", SAMPLE_INCIDENT["id"])

    assert resolved is True
    mock_post.assert_called_once()


# Test that an already-resolved incident (409) is reported clearly, not raised
@patch("examples.alerting.alert_incidents.requests.post")
@patch("builtins.input", return_value="yes")
def test_resolve_incident_409_already_resolved(mock_input, mock_post, caplog):
    mock_response = MagicMock()
    mock_response.status_code = 409
    mock_post.return_value = mock_response

    with caplog.at_level("INFO"):
        resolved = alert_incidents.resolve_incident("fake-token", SAMPLE_INCIDENT["id"])

    assert resolved is False
    assert "already resolved" in caplog.text.lower()


# Test that display_incidents logs the key incident details
def test_display_incidents(caplog):
    with caplog.at_level("INFO"):
        alert_incidents.display_incidents(SAMPLE_LIST)

    assert "client_health_score" in caplog.text
    assert "CorpWiFi|5" in caplog.text
    assert "cleared" in caplog.text


# Test that an active (unresolved) incident is labelled as such
def test_display_incidents_active(caplog):
    active = {
        "results": [dict(SAMPLE_INCIDENT, resolvedAt=None, resolutionReason=None)],
        "pagination": {},
    }

    with caplog.at_level("INFO"):
        alert_incidents.display_incidents(active)

    assert "active" in caplog.text.lower()


# Test that display handles missing/partial data gracefully
def test_display_incidents_partial_data(caplog):
    partial = {"results": [{"id": "abc", "metric": "latency"}]}

    with caplog.at_level("INFO"):
        alert_incidents.display_incidents(partial)

    assert "latency" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_incidents_empty(caplog):
    with caplog.at_level("INFO"):
        alert_incidents.display_incidents({"results": [], "pagination": {}})

    assert "No incidents" in caplog.text


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


# Test that HTTP errors on the read calls are logged and return None
@patch("examples.alerting.alert_incidents.requests.get")
def test_read_calls_http_error_return_none(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert alert_incidents.list_incidents("fake-token") is None
        assert alert_incidents.get_incidents_summary("fake-token") is None
        assert alert_incidents.get_incidents_by_rule("fake-token") is None
        assert alert_incidents.get_incident("fake-token", "abc") is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch("examples.alerting.alert_incidents.requests.get",
       side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_incidents_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert alert_incidents.list_incidents("fake-token") is None

    assert "Unexpected error" in caplog.text


# Test that all the optional list filters are forwarded
@patch("examples.alerting.alert_incidents.requests.get")
def test_list_incidents_passes_all_filters(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    alert_incidents.list_incidents(
        "fake-token", status="resolved", metric="m", rule_id="r",
        started_after=1, started_before=2,
    )

    params = mock_get.call_args.kwargs["params"]
    assert params["metric"] == "m"
    assert params["ruleId"] == "r"
    assert params["startedAfter"] == 1
    assert params["startedBefore"] == 2


# Test that the by-rule window filters are forwarded, and that no ruleId is sent -
# the spec declares no per-rule filter on this endpoint, and an unrecognised
# parameter would be ignored, silently returning unfiltered counts
@patch("examples.alerting.alert_incidents.requests.get")
def test_get_incidents_by_rule_passes_window(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    alert_incidents.get_incidents_by_rule("fake-token", from_ms=1, to_ms=2)

    params = mock_get.call_args.kwargs["params"]
    assert params["from"] == 1
    assert params["to"] == 2
    assert "ruleId" not in params


# Test that a resolve against an unknown incident is reported, not raised
@patch("examples.alerting.alert_incidents.requests.post")
@patch("builtins.input", return_value="yes")
def test_resolve_incident_404(mock_input, mock_post, caplog):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_post.return_value = mock_response

    with caplog.at_level("INFO"):
        assert alert_incidents.resolve_incident("fake-token", "abc") is False

    assert "No incident found" in caplog.text


# Test that an HTTP error on resolve returns False
@patch("examples.alerting.alert_incidents.requests.post")
@patch("builtins.input", return_value="yes")
def test_resolve_incident_http_error(mock_input, mock_post):
    mock_post.return_value = http_error_response()
    assert alert_incidents.resolve_incident("fake-token", "abc") is False


# Test that the epoch formatter renders UTC and tolerates junk
def test_format_timestamp():
    assert alert_incidents.format_timestamp(1787043600000) == "2026-08-18 09:00:00 UTC"
    assert alert_incidents.format_timestamp(None) == "N/A"
    assert alert_incidents.format_timestamp("not-a-number") == "not-a-number"


# Test the summary and by-rule display helpers
def test_display_summary_and_by_rule(caplog):
    with caplog.at_level("INFO"):
        alert_incidents.display_incidents_summary(None)
        alert_incidents.display_incidents_summary({"totalCount": 5, "activeCount": 1})
        alert_incidents.display_incidents_by_rule([])
        alert_incidents.display_incidents_by_rule([
            {"ruleId": "r1", "rule": {"metric": "m1"}, "incidentCount": 2, "activeCount": 1},
            {"ruleId": "r2", "rule": {"metric": "m2"}, "incidentCount": 9, "activeCount": 0},
        ])

    assert "No incidents grouped by rule" in caplog.text
    # The noisiest rule should be reported first
    assert caplog.text.index("r2") < caplog.text.index("r1")


def main_patches(input_values, **extra):
    # Builds the standard patch set for exercising main()
    patches = [
        patch("examples.alerting.alert_incidents.get_token", return_value=("tok", 0)),
        patch("examples.alerting.alert_incidents.get_incidents_summary", return_value={}),
        patch("builtins.input", side_effect=input_values),
    ]
    for target, value in extra.items():
        patches.append(patch(f"examples.alerting.alert_incidents.{target}", return_value=value))
    return patches


def run_main(input_values, **extra):
    applied = main_patches(input_values, **extra)
    for p in applied:
        p.start()
    try:
        alert_incidents.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main's exit branch
def test_main_exit_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["6"])

    assert "Nothing to do" in caplog.text


# Test main's list branches, both all and active-only
def test_main_list_branches(caplog):
    with caplog.at_level("INFO"):
        run_main(["1"], list_incidents=SAMPLE_LIST)
        run_main(["2"], list_incidents=SAMPLE_LIST)

    assert "client_health_score" in caplog.text


# Test main's by-rule branch
def test_main_by_rule_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["3"], get_incidents_by_rule=[
            {"ruleId": "r1", "rule": {"metric": "m"}, "incidentCount": 1, "activeCount": 0}
        ])

    assert "Incidents by Rule" in caplog.text


# Test main's fetch-single branch
def test_main_fetch_single_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["4", SAMPLE_INCIDENT["id"]], get_incident=SAMPLE_INCIDENT)

    assert SAMPLE_INCIDENT["id"] in caplog.text


# Test that an empty id exits rather than calling the API
def test_main_fetch_single_empty_id_exits():
    with pytest.raises(SystemExit):
        run_main(["4", "  "])


# Test main's resolve branch
def test_main_resolve_branch():
    with pytest.raises(SystemExit):
        run_main(["5", ""])


# Test that the resolve branch forwards a supplied id
def test_main_resolve_branch_with_id():
    run_main(["5", SAMPLE_INCIDENT["id"]], resolve_incident=True)


# Test that an unrecognised status filter is refused before any request. An
# unrecognised query parameter value is ignored by the API rather than rejected, so
# sending "Active" would return every incident while looking like a filtered result.
@patch("examples.alerting.alert_incidents.requests.get")
def test_list_incidents_rejects_bad_status(mock_get, caplog):
    with caplog.at_level("ERROR"):
        result = alert_incidents.list_incidents("fake-token", status="Active")

    assert result is None
    mock_get.assert_not_called()
    assert "lowercase" in caplog.text


# Test that both documented status values are accepted
@patch("examples.alerting.alert_incidents.requests.get")
def test_list_incidents_accepts_valid_statuses(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    for status in alert_incidents.VALID_STATUSES:
        assert alert_incidents.list_incidents("fake-token", status=status) is not None
