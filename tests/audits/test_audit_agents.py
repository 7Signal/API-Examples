import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.audits import audit_agents

SAMPLE_LIST = {
    "results": [
        {
            "id": "d51c7a90-4f36-4b28-91e5-6c0a3f8b2d47",
            "timestamp": "2026-08-17T14:22:41Z",
            "organizationName": "globalcorp",
            "actor": "jdoe@example.com",
            "action": "PATCH_EYES_AGENT",
            "source": "GATEWAY",
            "initiated": "API",
            "details": {"agentId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"},
        }
    ],
    "pagination": {"perPage": 10, "page": 1, "total": 1, "pages": 1},
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(audit_agents, "list_audit_records")
    assert hasattr(audit_agents, "iso_utc")
    assert hasattr(audit_agents, "display_audit_records")


# Test that list_audit_records handles a successful API call
@patch("examples.audits.audit_agents.requests.get")
def test_list_audit_records_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = audit_agents.list_audit_records("fake-token")

    assert data["results"][0]["action"] == "PATCH_EYES_AGENT"
    assert mock_get.call_args.kwargs["params"]["page"] == 1


# Test that the filters are passed through with the API's parameter names
@patch("examples.audits.audit_agents.requests.get")
def test_list_audit_records_passes_filters(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    audit_agents.list_audit_records(
        "fake-token",
        start_time="2026-08-01T00:00:00Z",
        end_time="2026-08-18T00:00:00Z",
        actor="jdoe@example.com",
        action="PATCH_EYES_AGENT",
    )

    params = mock_get.call_args.kwargs["params"]
    assert params["startTimeRange"] == "2026-08-01T00:00:00Z"
    assert params["endTimeRange"] == "2026-08-18T00:00:00Z"
    assert params["actor"] == "jdoe@example.com"
    assert params["action"] == "PATCH_EYES_AGENT"


# Test that an epoch-millisecond time range is refused, since this endpoint wants
# ISO-8601 strings unlike the rest of the API
@patch("examples.audits.audit_agents.requests.get")
def test_list_audit_records_rejects_epoch_millis(mock_get, caplog):
    with caplog.at_level("ERROR"):
        data = audit_agents.list_audit_records("fake-token", start_time=1755512400000)

    assert data is None
    mock_get.assert_not_called()
    assert "ISO-8601" in caplog.text


# Test that iso_utc renders an epoch-millisecond value in the format this endpoint wants
def test_iso_utc_formats_epoch_millis():
    assert audit_agents.iso_utc(1787043600000) == "2026-08-18T09:00:00Z"


# Test that display logs the audit details
def test_display_audit_records(caplog):
    with caplog.at_level("INFO"):
        audit_agents.display_audit_records(SAMPLE_LIST)

    assert "PATCH_EYES_AGENT" in caplog.text
    assert "jdoe@example.com" in caplog.text
    assert "GATEWAY" in caplog.text


# Test that a record whose free-form details lack the usual keys still displays
def test_display_audit_records_handles_freeform_details(caplog):
    partial = {"results": [{"id": "abc", "action": "DELETE_EYES_AGENT", "details": {}}]}

    with caplog.at_level("INFO"):
        audit_agents.display_audit_records(partial)

    assert "DELETE_EYES_AGENT" in caplog.text


# Test that a record with no details key at all does not break the display
def test_display_audit_records_handles_missing_details(caplog):
    partial = {"results": [{"id": "abc", "action": "PATCH_EYES_AGENTS"}]}

    with caplog.at_level("INFO"):
        audit_agents.display_audit_records(partial)

    assert "PATCH_EYES_AGENTS" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_audit_records_empty(caplog):
    with caplog.at_level("INFO"):
        audit_agents.display_audit_records({"results": [], "pagination": {}})

    assert "No audit records" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests

MODULE = "examples.audits.audit_agents"


def http_error_response():
    r = MagicMock()
    r.status_code = 400
    r.text = "Bad Request"
    r.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return r


# Test that an HTTP error returns None
@patch(f"{MODULE}.requests.get")
def test_list_audit_records_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert audit_agents.list_audit_records("fake-token") is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch(f"{MODULE}.requests.get", side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_audit_records_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert audit_agents.list_audit_records("fake-token") is None

    assert "Unexpected error" in caplog.text


# Test that an epoch end_time is refused too, not just start_time
@patch(f"{MODULE}.requests.get")
def test_list_audit_records_rejects_epoch_end_time(mock_get):
    assert audit_agents.list_audit_records("fake-token", end_time=1755512400000) is None
    mock_get.assert_not_called()


# Test that the remaining filters and sort options are forwarded
@patch(f"{MODULE}.requests.get")
def test_list_audit_records_forwards_source_and_sort(mock_get):
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = SAMPLE_LIST
    r.raise_for_status = MagicMock()
    mock_get.return_value = r

    audit_agents.list_audit_records(
        "fake-token", source="GATEWAY", initiated="API", sort_field="timestamp", order="desc"
    )

    params = mock_get.call_args.kwargs["params"]
    assert params["source"] == "GATEWAY"
    assert params["initiated"] == "API"
    assert params["sortField"] == "timestamp"
    assert params["order"] == "desc"


# Test that the distinct-action helper de-duplicates and sorts
def test_summarize_actions():
    records = [{"action": "B"}, {"action": "A"}, {"action": "B"}, {}]
    assert audit_agents.summarize_actions(records) == ["A", "B"]


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
        audit_agents.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main's exit branch
def test_main_exit_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["5"])

    assert "Nothing to do" in caplog.text


# Test main's default listing branch
def test_main_list_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["1"], list_audit_records=SAMPLE_LIST)

    assert "PATCH_EYES_AGENT" in caplog.text


# Test main's actor filter branch
def test_main_actor_branch():
    run_main(["2", "jdoe@example.com"], list_audit_records=SAMPLE_LIST)


# Test that an empty actor exits
def test_main_actor_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["2", " "])


# Test main's action filter branch
def test_main_action_branch():
    run_main(["3", "PATCH_EYES_AGENT"], list_audit_records=SAMPLE_LIST)


# Test that an empty action exits
def test_main_action_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["3", " "])


# Test main's distinct-actions branch
def test_main_distinct_actions_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["4"], list_audit_records=SAMPLE_LIST)

    assert "Distinct actions seen" in caplog.text


# Test that the distinct-actions branch reports an empty result set
def test_main_distinct_actions_empty(caplog):
    with caplog.at_level("INFO"):
        run_main(["4"], list_audit_records={"results": []})

    assert "No audit records" in caplog.text
