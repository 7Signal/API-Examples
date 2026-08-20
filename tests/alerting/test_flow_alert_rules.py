import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.alerting import flow_alert_rules

# Sample rule used across tests
SAMPLE_RULE = {
    "id": "3f2b9c1e-58a4-4d2f-9b71-2c0e5a7d1f34",
    "name": "Low client health on guest network",
    "metric": "client_health_score",
    "dimensionSet": ["network", "band"],
    "aggregationFunction": "avg",
    "thresholdValue": 70.0,
    "thresholdOperator": "<",
    "pendingPeriodSeconds": 600,
    "missingDataPolicy": "ignore",
    "enabled": True,
    "createdAt": "2026-07-14T18:22:05Z",
    "updatedAt": "2026-08-02T11:47:31Z",
}

SAMPLE_LIST = {
    "results": [SAMPLE_RULE],
    "pagination": {"perPage": 10, "page": 1, "total": 1, "pages": 1},
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(flow_alert_rules, "list_alert_rules")
    assert hasattr(flow_alert_rules, "get_alert_rules_summary")
    assert hasattr(flow_alert_rules, "get_alert_rule")
    assert hasattr(flow_alert_rules, "create_alert_rule")
    assert hasattr(flow_alert_rules, "replace_alert_rule")
    assert hasattr(flow_alert_rules, "set_alert_rule_enabled")
    assert hasattr(flow_alert_rules, "delete_alert_rule")
    assert hasattr(flow_alert_rules, "display_alert_rules")


# Test that list_alert_rules handles a successful API call
@patch("examples.alerting.flow_alert_rules.requests.get")
def test_list_alert_rules_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = flow_alert_rules.list_alert_rules("fake-token")

    assert data["results"][0]["id"] == SAMPLE_RULE["id"]
    # Paging should default to the API's 1-based first page
    assert mock_get.call_args.kwargs["params"]["page"] == 1


# Test that the summary endpoint is read correctly
@patch("examples.alerting.flow_alert_rules.requests.get")
def test_get_alert_rules_summary_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"totalCount": 23, "activeCount": 19, "disabledCount": 4}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    summary = flow_alert_rules.get_alert_rules_summary("fake-token")

    assert summary["totalCount"] == 23
    assert summary["disabledCount"] == 4


# Test that get_alert_rule returns None on 404 rather than raising
@patch("examples.alerting.flow_alert_rules.requests.get")
def test_get_alert_rule_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    assert flow_alert_rules.get_alert_rule("fake-token", "missing-id") is None


# Test that create_alert_rule sends all five required fields
@patch("examples.alerting.flow_alert_rules.requests.post")
def test_create_alert_rule_sends_required_fields(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = SAMPLE_RULE
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    created = flow_alert_rules.create_alert_rule(
        "fake-token",
        metric="client_health_score",
        dimension_set=["network", "band"],
        aggregation_function="avg",
        threshold_value=70.0,
        threshold_operator="<",
        name="Low client health on guest network",
    )

    payload = mock_post.call_args.kwargs["json"]
    for required_field in (
        "metric",
        "dimensionSet",
        "aggregationFunction",
        "thresholdValue",
        "thresholdOperator",
    ):
        assert required_field in payload

    # Enum values must be sent lowercase exactly as the API expects
    assert payload["aggregationFunction"] == "avg"
    assert payload["thresholdOperator"] == "<"
    assert created["id"] == SAMPLE_RULE["id"]


# Test that the enabled toggle sends a PATCH with the boolean body once confirmed
@patch("builtins.input", return_value="yes")
@patch("examples.alerting.flow_alert_rules.requests.patch")
def test_set_alert_rule_enabled_sends_boolean(mock_patch, mock_input):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = dict(SAMPLE_RULE, enabled=False)
    mock_response.raise_for_status = MagicMock()
    mock_patch.return_value = mock_response

    result = flow_alert_rules.set_alert_rule_enabled("fake-token", SAMPLE_RULE["id"], False)

    assert mock_patch.call_args.kwargs["json"] == {"enabled": False}
    assert result["enabled"] is False


# Test that declining the confirmation prompt aborts the delete entirely
@patch("examples.alerting.flow_alert_rules.requests.delete")
@patch("builtins.input", return_value="no")
def test_delete_alert_rule_aborts_without_confirmation(mock_input, mock_delete):
    deleted = flow_alert_rules.delete_alert_rule("fake-token", SAMPLE_RULE["id"])

    assert deleted is False
    mock_delete.assert_not_called()


# Test that confirming the prompt issues the delete
@patch("examples.alerting.flow_alert_rules.requests.delete")
@patch("builtins.input", return_value="yes")
def test_delete_alert_rule_deletes_when_confirmed(mock_input, mock_delete):
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.raise_for_status = MagicMock()
    mock_delete.return_value = mock_response

    deleted = flow_alert_rules.delete_alert_rule("fake-token", SAMPLE_RULE["id"])

    assert deleted is True
    mock_delete.assert_called_once()


# Test that display_alert_rules logs the key rule details
def test_display_alert_rules(caplog):
    with caplog.at_level("INFO"):
        flow_alert_rules.display_alert_rules(SAMPLE_LIST)

    assert "client_health_score" in caplog.text
    assert "Low client health on guest network" in caplog.text
    # The threshold should be rendered in a readable operator form
    assert "<" in caplog.text
    assert "70" in caplog.text


# Test that display handles missing/partial data gracefully
def test_display_alert_rules_partial_data(caplog):
    partial = {"results": [{"id": "abc", "metric": "latency"}]}

    with caplog.at_level("INFO"):
        flow_alert_rules.display_alert_rules(partial)

    assert "latency" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_alert_rules_empty(caplog):
    with caplog.at_level("INFO"):
        flow_alert_rules.display_alert_rules({"results": [], "pagination": {}})

    assert "No alert rules" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests


def http_error_response(text="Bad Request"):
    # Builds a mock whose raise_for_status raises, the way requests behaves on a 4xx
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = text
    mock_response.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return mock_response


# Test that an HTTP error on the list call is logged and returns None
@patch("examples.alerting.flow_alert_rules.requests.get")
def test_list_alert_rules_http_error_returns_none(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert flow_alert_rules.list_alert_rules("fake-token") is None

    assert "HTTP error" in caplog.text


# Test that an HTTP error on the summary call returns None
@patch("examples.alerting.flow_alert_rules.requests.get")
def test_get_alert_rules_summary_http_error_returns_none(mock_get):
    mock_get.return_value = http_error_response()
    assert flow_alert_rules.get_alert_rules_summary("fake-token") is None


# Test that an HTTP error on a single fetch returns None
@patch("examples.alerting.flow_alert_rules.requests.get")
def test_get_alert_rule_http_error_returns_none(mock_get):
    mock_get.return_value = http_error_response()
    assert flow_alert_rules.get_alert_rule("fake-token", "abc") is None


# Test that a connection-level failure is caught rather than escaping
@patch("examples.alerting.flow_alert_rules.requests.get",
       side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_alert_rules_connection_error_returns_none(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert flow_alert_rules.list_alert_rules("fake-token") is None

    assert "Unexpected error" in caplog.text


# Test that an HTTP error on create returns None
@patch("examples.alerting.flow_alert_rules.requests.post")
def test_create_alert_rule_http_error_returns_none(mock_post):
    mock_post.return_value = http_error_response()

    assert flow_alert_rules.create_alert_rule(
        "fake-token", metric="m", dimension_set=["network"],
        aggregation_function="avg", threshold_value=1.0, threshold_operator="<",
    ) is None


# Test that the optional create fields are only sent when supplied
@patch("examples.alerting.flow_alert_rules.requests.post")
def test_create_alert_rule_includes_optional_fields(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = SAMPLE_RULE
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    flow_alert_rules.create_alert_rule(
        "fake-token", metric="m", dimension_set=["network"],
        aggregation_function="avg", threshold_value=1.0, threshold_operator="<",
        name="named", pending_period_seconds=60, missing_data_policy="bad",
        notification_config={"deliveries": []}, enabled=False,
    )

    payload = mock_post.call_args.kwargs["json"]
    assert payload["pendingPeriodSeconds"] == 60
    assert payload["missingDataPolicy"] == "bad"
    assert payload["enabled"] is False


# Test that the list filters are passed through when supplied
@patch("examples.alerting.flow_alert_rules.requests.get")
def test_list_alert_rules_passes_filters(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    flow_alert_rules.list_alert_rules("fake-token", metric="m", enabled=True, name="n")

    params = mock_get.call_args.kwargs["params"]
    assert params["metric"] == "m"
    assert params["enabled"] is True
    assert params["name"] == "n"


# Test that a full replace is sent once confirmed, and an HTTP error returns None
@patch("builtins.input", return_value="yes")
@patch("examples.alerting.flow_alert_rules.requests.put")
def test_replace_alert_rule_success_and_error(mock_put, mock_input):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_RULE
    mock_response.raise_for_status = MagicMock()
    mock_put.return_value = mock_response

    assert flow_alert_rules.replace_alert_rule("fake-token", "abc", {"metric": "m"}) is not None

    mock_put.return_value = http_error_response()
    assert flow_alert_rules.replace_alert_rule("fake-token", "abc", {"metric": "m"}) is None


# Test that an HTTP error on the enabled toggle returns None
@patch("builtins.input", return_value="yes")
@patch("examples.alerting.flow_alert_rules.requests.patch")
def test_set_alert_rule_enabled_http_error_returns_none(mock_patch, mock_input):
    mock_patch.return_value = http_error_response()
    assert flow_alert_rules.set_alert_rule_enabled("fake-token", "abc", True) is None


# Test that an HTTP error on delete returns False
@patch("examples.alerting.flow_alert_rules.requests.delete")
@patch("builtins.input", return_value="yes")
def test_delete_alert_rule_http_error_returns_false(mock_input, mock_delete):
    mock_delete.return_value = http_error_response()
    assert flow_alert_rules.delete_alert_rule("fake-token", "abc") is False


# Test that the summary display tolerates an absent summary
def test_display_alert_rule_summary_handles_none(caplog):
    with caplog.at_level("INFO"):
        flow_alert_rules.display_alert_rule_summary(None)
        flow_alert_rules.display_alert_rule_summary({"totalCount": 1})

    assert "Total" in caplog.text


# Test that main's menu exit branch does nothing destructive
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("builtins.input", return_value="6")
def test_main_exit_branch(mock_input, mock_summary, mock_list, mock_token, caplog):
    with caplog.at_level("INFO"):
        flow_alert_rules.main()

    assert "Nothing to do" in caplog.text


# Test main's fetch-single branch
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.get_alert_rule", return_value=SAMPLE_RULE)
@patch("builtins.input", side_effect=["1", SAMPLE_RULE["id"]])
def test_main_fetch_single_branch(mock_input, mock_get, mock_summary, mock_list, mock_token, caplog):
    with caplog.at_level("INFO"):
        flow_alert_rules.main()

    mock_get.assert_called_once()
    assert "client_health_score" in caplog.text


# Test that main exits when the fetch branch is given an empty id
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("builtins.input", side_effect=["1", "  "])
def test_main_fetch_single_empty_id_exits(mock_input, mock_summary, mock_list, mock_token):
    with pytest.raises(SystemExit):
        flow_alert_rules.main()


# Test main's create branch end to end
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.create_alert_rule", return_value=SAMPLE_RULE)
@patch("builtins.input", side_effect=[
    "2", "client_health_score", "network, band", "avg", "<", "70", "My rule", "yes",
])
def test_main_create_branch(mock_input, mock_create, mock_summary, mock_list, mock_token):
    flow_alert_rules.main()

    kwargs = mock_create.call_args.kwargs
    assert kwargs["metric"] == "client_health_score"
    assert kwargs["dimension_set"] == ["network", "band"]
    assert kwargs["threshold_value"] == 70.0


# Test that the create branch refuses an unsupported dimension
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("builtins.input", side_effect=["2", "metric", "not_a_dimension"])
def test_main_create_rejects_bad_dimension(mock_input, mock_summary, mock_list, mock_token):
    with pytest.raises(SystemExit):
        flow_alert_rules.main()


# Test that the create branch refuses a non-numeric threshold
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("builtins.input", side_effect=["2", "metric", "network", "avg", "<", "not-a-number"])
def test_main_create_rejects_bad_threshold(mock_input, mock_summary, mock_list, mock_token):
    with pytest.raises(SystemExit):
        flow_alert_rules.main()


# Test that declining the create confirmation sends nothing
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.create_alert_rule")
@patch("builtins.input", side_effect=["2", "metric", "network", "avg", "<", "70", "", "no"])
def test_main_create_declined(mock_input, mock_create, mock_summary, mock_list, mock_token):
    flow_alert_rules.main()
    mock_create.assert_not_called()


# Test main's enable/disable branch
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.set_alert_rule_enabled")
@patch("builtins.input", side_effect=["3", SAMPLE_RULE["id"], "disable"])
def test_main_toggle_branch(mock_input, mock_set, mock_summary, mock_list, mock_token):
    flow_alert_rules.main()
    mock_set.assert_called_once_with("tok", SAMPLE_RULE["id"], False)


# Test that the toggle branch refuses an answer that is neither enable nor disable
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("builtins.input", side_effect=["3", SAMPLE_RULE["id"], "maybe"])
def test_main_toggle_rejects_bad_state(mock_input, mock_summary, mock_list, mock_token):
    with pytest.raises(SystemExit):
        flow_alert_rules.main()


# Test main's delete branch
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.delete_alert_rule", return_value=True)
@patch("builtins.input", side_effect=["5", SAMPLE_RULE["id"]])
def test_main_delete_branch(mock_input, mock_delete, mock_summary, mock_list, mock_token):
    flow_alert_rules.main()
    mock_delete.assert_called_once_with("tok", SAMPLE_RULE["id"])


# ---------------------------------------------------------------------------
# Confirmation gates on the remaining write operations
# ---------------------------------------------------------------------------

# Test that declining the toggle confirmation sends nothing. Disabling a rule stops
# it being evaluated, so it needs the same gate as a delete.
@patch("builtins.input", return_value="no")
@patch("examples.alerting.flow_alert_rules.requests.patch")
def test_set_alert_rule_enabled_declined(mock_patch, mock_input):
    assert flow_alert_rules.set_alert_rule_enabled("fake-token", "abc", False) is None
    mock_patch.assert_not_called()


# Test that declining the replace confirmation sends nothing
@patch("builtins.input", return_value="no")
@patch("examples.alerting.flow_alert_rules.requests.put")
def test_replace_alert_rule_declined(mock_put, mock_input):
    assert flow_alert_rules.replace_alert_rule("fake-token", "abc", {"metric": "m"}) is None
    mock_put.assert_not_called()


# Test that create validates the aggregation enum in-function, not only at the prompt
@patch("examples.alerting.flow_alert_rules.requests.post")
def test_create_alert_rule_rejects_bad_aggregation(mock_post, caplog):
    with caplog.at_level("ERROR"):
        result = flow_alert_rules.create_alert_rule(
            "fake-token", metric="m", dimension_set=["network"],
            aggregation_function="AVG", threshold_value=1.0, threshold_operator="<",
        )

    assert result is None
    mock_post.assert_not_called()
    assert "lowercase" in caplog.text


# Test that create validates the threshold operator in-function
@patch("examples.alerting.flow_alert_rules.requests.post")
def test_create_alert_rule_rejects_bad_operator(mock_post):
    assert flow_alert_rules.create_alert_rule(
        "fake-token", metric="m", dimension_set=["network"],
        aggregation_function="avg", threshold_value=1.0, threshold_operator="lt",
    ) is None
    mock_post.assert_not_called()


# Test that create validates dimension membership in-function
@patch("examples.alerting.flow_alert_rules.requests.post")
def test_create_alert_rule_rejects_bad_dimension(mock_post):
    assert flow_alert_rules.create_alert_rule(
        "fake-token", metric="m", dimension_set=["not_a_dimension"],
        aggregation_function="avg", threshold_value=1.0, threshold_operator="<",
    ) is None
    mock_post.assert_not_called()


# Test that create requires at least one dimension
@patch("examples.alerting.flow_alert_rules.requests.post")
def test_create_alert_rule_requires_a_dimension(mock_post):
    assert flow_alert_rules.create_alert_rule(
        "fake-token", metric="m", dimension_set=[],
        aggregation_function="avg", threshold_value=1.0, threshold_operator="<",
    ) is None
    mock_post.assert_not_called()


# Test main's replace branch, which refetches so the full-replace payload keeps
# every field the rule already had
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.get_alert_rule", return_value=SAMPLE_RULE)
@patch("examples.alerting.flow_alert_rules.replace_alert_rule", return_value=SAMPLE_RULE)
@patch("builtins.input", side_effect=["4", SAMPLE_RULE["id"], "55"])
def test_main_replace_branch(mock_input, mock_replace, mock_get, mock_summary,
                             mock_list, mock_token):
    flow_alert_rules.main()

    payload = mock_replace.call_args.args[2]
    # The new threshold is applied, and the untouched fields are carried over
    assert payload["thresholdValue"] == 55.0
    assert payload["metric"] == SAMPLE_RULE["metric"]
    assert payload["dimensionSet"] == SAMPLE_RULE["dimensionSet"]
    assert payload["pendingPeriodSeconds"] == SAMPLE_RULE["pendingPeriodSeconds"]


# Test that the replace branch stops when the rule does not exist
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.get_alert_rule", return_value=None)
@patch("builtins.input", side_effect=["4", "missing-id"])
def test_main_replace_branch_missing_rule(mock_input, mock_get, mock_summary,
                                         mock_list, mock_token):
    flow_alert_rules.main()


# Test that a non-numeric threshold on the replace branch exits
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.get_alert_rule", return_value=SAMPLE_RULE)
@patch("builtins.input", side_effect=["4", SAMPLE_RULE["id"], "not-a-number"])
def test_main_replace_branch_bad_threshold(mock_input, mock_get, mock_summary,
                                          mock_list, mock_token):
    with pytest.raises(SystemExit):
        flow_alert_rules.main()


# Test that an empty id on the replace branch exits
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("builtins.input", side_effect=["4", " "])
def test_main_replace_branch_empty_id(mock_input, mock_summary, mock_list, mock_token):
    with pytest.raises(SystemExit):
        flow_alert_rules.main()


# Test that a zero-padded menu entry does not dispatch an action. Matching on
# int(choice) would treat "01" as "1" and run a destructive path the user did not pick.
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.get_alert_rule")
@patch("builtins.input", side_effect=["01"])
def test_main_rejects_zero_padded_choice(mock_input, mock_get, mock_summary,
                                         mock_list, mock_token, caplog):
    with caplog.at_level("INFO"):
        flow_alert_rules.main()

    mock_get.assert_not_called()
    assert "Nothing to do" in caplog.text


# Test that other near-miss inputs also fall through rather than dispatching
@patch("examples.alerting.flow_alert_rules.get_token", return_value=("tok", 0))
@patch("examples.alerting.flow_alert_rules.list_alert_rules", return_value=SAMPLE_LIST)
@patch("examples.alerting.flow_alert_rules.get_alert_rules_summary", return_value={})
@patch("examples.alerting.flow_alert_rules.delete_alert_rule")
@patch("builtins.input", side_effect=["+5"])
def test_main_rejects_signed_choice(mock_input, mock_delete, mock_summary,
                                    mock_list, mock_token, caplog):
    with caplog.at_level("INFO"):
        flow_alert_rules.main()

    mock_delete.assert_not_called()
    assert "Nothing to do" in caplog.text
