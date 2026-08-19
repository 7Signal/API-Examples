import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.summaries import users_summary

SAMPLE_SUMMARY = {"total": 148, "loginLast30Days": 92, "loginLast90Days": 121}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(users_summary, "get_user_summary")
    assert hasattr(users_summary, "display_user_summary")


# Test that get_user_summary handles a successful API call
@patch("examples.summaries.users_summary.requests.get")
def test_get_user_summary_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_SUMMARY
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    summary = users_summary.get_user_summary("fake-token")

    assert summary["total"] == 148


# Test that the organization filter uses this endpoint's organizationId parameter.
# Most endpoints use `organization`, and an unrecognised name is ignored rather than
# rejected, so the wrong spelling silently returns the primary organization instead.
@patch("examples.summaries.users_summary.requests.get")
def test_get_user_summary_uses_organization_id_param(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_SUMMARY
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    users_summary.get_user_summary("fake-token", organization_id="org-123")

    params = mock_get.call_args.kwargs["params"]
    assert params["organizationId"] == "org-123"
    assert "organization" not in params


# Test that no organization filter is sent when none is asked for
@patch("examples.summaries.users_summary.requests.get")
def test_get_user_summary_omits_organization_when_not_given(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_SUMMARY
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    users_summary.get_user_summary("fake-token")

    assert mock_get.call_args.kwargs["params"] == {}


# Test that display logs the counts
def test_display_user_summary(caplog):
    with caplog.at_level("INFO"):
        users_summary.display_user_summary(SAMPLE_SUMMARY)

    assert "148" in caplog.text
    assert "92" in caplog.text
    assert "121" in caplog.text


# Test that the dormant estimate is derived from total minus the 90 day logins,
# rather than by adding the overlapping windows together
def test_display_user_summary_reports_dormant_estimate(caplog):
    with caplog.at_level("INFO"):
        users_summary.display_user_summary(SAMPLE_SUMMARY)

    # 148 - 121 = 27
    assert "27" in caplog.text


# Test that display handles missing/partial data gracefully
def test_display_user_summary_partial_data(caplog):
    with caplog.at_level("INFO"):
        users_summary.display_user_summary({"total": 10})

    assert "10" in caplog.text


# Test that an empty summary is reported rather than failing
def test_display_user_summary_empty(caplog):
    with caplog.at_level("INFO"):
        users_summary.display_user_summary(None)

    assert "No user summary" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests

MODULE = "examples.summaries.users_summary"


def http_error_response():
    r = MagicMock()
    r.status_code = 400
    r.text = "Bad Request"
    r.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return r


# Test that an HTTP error returns None
@patch(f"{MODULE}.requests.get")
def test_get_user_summary_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert users_summary.get_user_summary("fake-token") is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch(f"{MODULE}.requests.get", side_effect=_requests.exceptions.ConnectionError("boom"))
def test_get_user_summary_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert users_summary.get_user_summary("fake-token") is None

    assert "Unexpected error" in caplog.text


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
        users_summary.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main with no organization supplied
def test_main_primary_org(caplog):
    with caplog.at_level("INFO"):
        run_main([""], get_user_summary=SAMPLE_SUMMARY)

    assert "148" in caplog.text


# Test main with an explicit organization
def test_main_explicit_org():
    run_main(["org-123"], get_user_summary=SAMPLE_SUMMARY)
