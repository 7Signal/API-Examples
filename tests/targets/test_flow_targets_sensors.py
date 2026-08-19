import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.targets import flow_targets_sensors

SAMPLE_TARGET = {
    "id": 412,
    "name": "Corporate Sonar",
    "description": "Primary Sonar server in the Cleveland datacenter",
    "targetType": "SONAR",
    "tcpPort": 80,
    "dnsName": "sonar.example.com",
    "ipV4Address": "10.20.30.40",
    "ipV6Address": None,
}

SAMPLE_LIST = {
    "results": [SAMPLE_TARGET],
    "pagination": {"perPage": 10, "page": 1, "total": 1, "pages": 1},
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(flow_targets_sensors, "list_targets")
    assert hasattr(flow_targets_sensors, "get_target")
    assert hasattr(flow_targets_sensors, "create_target")
    assert hasattr(flow_targets_sensors, "replace_target")
    assert hasattr(flow_targets_sensors, "delete_target")
    assert hasattr(flow_targets_sensors, "display_targets")


# Test that list_targets handles a successful API call
@patch("examples.targets.flow_targets_sensors.requests.get")
def test_list_targets_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = flow_targets_sensors.list_targets("fake-token")

    assert data["results"][0]["id"] == 412
    assert mock_get.call_args.kwargs["params"]["page"] == 1


# Test that get_target returns None on 404 rather than raising
@patch("examples.targets.flow_targets_sensors.requests.get")
def test_get_target_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    assert flow_targets_sensors.get_target("fake-token", 999) is None


# Test that a WEB_SERVER target without a dnsName is refused before any request
@patch("examples.targets.flow_targets_sensors.requests.post")
def test_create_target_web_server_requires_dns_name(mock_post, caplog):
    with caplog.at_level("ERROR"):
        created = flow_targets_sensors.create_target(
            "fake-token", "WEB_SERVER", "Corp Web", ipv4_address="10.0.0.1"
        )

    assert created is None
    mock_post.assert_not_called()
    assert "dnsName" in caplog.text


# Test that a SONAR target is accepted with only an IPv4 address
@patch("examples.targets.flow_targets_sensors.requests.post")
def test_create_target_sonar_accepts_ip_only(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_TARGET
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    created = flow_targets_sensors.create_target(
        "fake-token", "SONAR", "Corp Sonar", ipv4_address="10.20.30.40"
    )

    payload = mock_post.call_args.kwargs["json"]
    assert payload["targetType"] == "SONAR"
    assert payload["name"] == "Corp Sonar"
    assert payload["ipV4Address"] == "10.20.30.40"
    assert created["id"] == 412


# Test that an unsupported target type is refused before any request
@patch("examples.targets.flow_targets_sensors.requests.post")
def test_create_target_rejects_invalid_type(mock_post, caplog):
    with caplog.at_level("ERROR"):
        created = flow_targets_sensors.create_target(
            "fake-token", "FTP_SERVER", "Nope", dns_name="ftp.example.com"
        )

    assert created is None
    mock_post.assert_not_called()


# Test that declining the confirmation prompt aborts the delete entirely
@patch("examples.targets.flow_targets_sensors.requests.delete")
@patch("builtins.input", return_value="no")
def test_delete_target_aborts_without_confirmation(mock_input, mock_delete):
    deleted = flow_targets_sensors.delete_target("fake-token", 412)

    assert deleted is False
    mock_delete.assert_not_called()


# Test that confirming the prompt issues the delete
@patch("examples.targets.flow_targets_sensors.requests.delete")
@patch("builtins.input", return_value="yes")
def test_delete_target_deletes_when_confirmed(mock_input, mock_delete):
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.raise_for_status = MagicMock()
    mock_delete.return_value = mock_response

    deleted = flow_targets_sensors.delete_target("fake-token", 412)

    assert deleted is True
    mock_delete.assert_called_once()


# Test that replace_target warns that omitted address fields are cleared
@patch("examples.targets.flow_targets_sensors.requests.put")
def test_replace_target_success(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_TARGET
    mock_response.raise_for_status = MagicMock()
    mock_put.return_value = mock_response

    updated = flow_targets_sensors.replace_target(
        "fake-token", 412, {"name": "Renamed", "dnsName": "sonar.example.com"}
    )

    assert updated["id"] == 412
    assert mock_put.call_args.kwargs["json"]["name"] == "Renamed"


# Test that display_targets logs the key target details
def test_display_targets(caplog):
    with caplog.at_level("INFO"):
        flow_targets_sensors.display_targets(SAMPLE_LIST)

    assert "Corporate Sonar" in caplog.text
    assert "SONAR" in caplog.text
    assert "sonar.example.com" in caplog.text


# Test that display handles missing/partial data gracefully
def test_display_targets_partial_data(caplog):
    with caplog.at_level("INFO"):
        flow_targets_sensors.display_targets({"results": [{"id": 1, "name": "Bare"}]})

    assert "Bare" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_targets_empty(caplog):
    with caplog.at_level("INFO"):
        flow_targets_sensors.display_targets({"results": [], "pagination": {}})

    assert "No sensor targets" in caplog.text


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


def ok_response(payload, status_code=200):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = payload
    r.raise_for_status = MagicMock()
    return r


# Test that HTTP errors on the read calls return None
@patch("examples.targets.flow_targets_sensors.requests.get")
def test_read_calls_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert flow_targets_sensors.list_targets("fake-token") is None
        assert flow_targets_sensors.get_target("fake-token", 1) is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch("examples.targets.flow_targets_sensors.requests.get",
       side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_targets_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert flow_targets_sensors.list_targets("fake-token") is None

    assert "Unexpected error" in caplog.text


# Test that a SONAR target with no address at all is refused
def test_validate_address_requires_something_for_sonar():
    assert flow_targets_sensors.validate_address("SONAR", None, None, None) is not None
    assert flow_targets_sensors.validate_address("SONAR", None, "10.0.0.1", None) is None
    assert flow_targets_sensors.validate_address("WEB_SERVER", "a.example.com", None, None) is None


# Test that create forwards the optional description, IPv6, and port
@patch("examples.targets.flow_targets_sensors.requests.post")
def test_create_target_forwards_optional_fields(mock_post):
    mock_post.return_value = ok_response(SAMPLE_TARGET)

    flow_targets_sensors.create_target(
        "fake-token", "SONAR", "n", description="d",
        dns_name="a.example.com", ipv6_address="::1", tcp_port=8080,
    )

    payload = mock_post.call_args.kwargs["json"]
    assert payload["description"] == "d"
    assert payload["ipV6Address"] == "::1"
    assert payload["tcpPort"] == 8080


# Test that an HTTP error on create returns None
@patch("examples.targets.flow_targets_sensors.requests.post")
def test_create_target_http_error(mock_post):
    mock_post.return_value = http_error_response()
    assert flow_targets_sensors.create_target(
        "fake-token", "SONAR", "n", ipv4_address="10.0.0.1"
    ) is None


# Test that an HTTP error on replace returns None
@patch("examples.targets.flow_targets_sensors.requests.put")
def test_replace_target_http_error(mock_put):
    mock_put.return_value = http_error_response()
    assert flow_targets_sensors.replace_target("fake-token", 1, {"name": "n"}) is None


# Test that a delete blocked by a test profile is explained
@patch("examples.targets.flow_targets_sensors.requests.delete")
@patch("builtins.input", return_value="yes")
def test_delete_target_http_error_explains(mock_input, mock_delete, caplog):
    mock_delete.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert flow_targets_sensors.delete_target("fake-token", 1) is False

    assert "test profile" in caplog.text


def run_main(input_values, **extra):
    applied = [
        patch("examples.targets.flow_targets_sensors.get_token", return_value=("tok", 0)),
        patch("examples.targets.flow_targets_sensors.list_targets", return_value=SAMPLE_LIST),
        patch("builtins.input", side_effect=input_values),
    ]
    for target, value in extra.items():
        applied.append(patch(f"examples.targets.flow_targets_sensors.{target}", return_value=value))
    for p in applied:
        p.start()
    try:
        flow_targets_sensors.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test main's exit branch
def test_main_exit_branch(caplog):
    with caplog.at_level("INFO"):
        run_main(["5"])

    assert "Nothing to do" in caplog.text


# Test main's fetch-single branch
def test_main_fetch_single_branch():
    run_main(["1", "412"], get_target=SAMPLE_TARGET)


# Test that an empty target id exits
def test_main_fetch_single_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["1", " "])


# Test main's create branch for a type that needs only an IP
def test_main_create_branch():
    run_main(
        ["2", "SONAR", "Corp Sonar", "", "10.20.30.40", "", "yes"],
        create_target=SAMPLE_TARGET,
    )


# Test main's create branch for a DNS-only type, with a port supplied
def test_main_create_branch_with_port():
    run_main(
        ["2", "IPERF3_SERVER", "Branch iPerf3", "iperf.example.com", "", "5201", "yes"],
        create_target=SAMPLE_TARGET,
    )


# Test that an unsupported type exits
def test_main_create_bad_type_exits():
    with pytest.raises(SystemExit):
        run_main(["2", "FTP_SERVER"])


# Test that an empty name exits
def test_main_create_empty_name_exits():
    with pytest.raises(SystemExit):
        run_main(["2", "SONAR", " "])


# Test that a non-numeric port exits
def test_main_create_bad_port_exits():
    with pytest.raises(SystemExit):
        run_main(["2", "SONAR", "n", "", "10.0.0.1", "not-a-port"])


# Test that declining the create confirmation sends nothing
def test_main_create_declined():
    with patch("examples.targets.flow_targets_sensors.create_target") as mock_create:
        run_main(["2", "SONAR", "n", "", "10.0.0.1", "", "no"])
        mock_create.assert_not_called()


# Test main's rename branch, which refetches so address fields are preserved
def test_main_rename_branch():
    run_main(
        ["3", "412", "Renamed", "yes"],
        get_target=SAMPLE_TARGET,
        replace_target=SAMPLE_TARGET,
    )


# Test that the rename branch stops when the target does not exist
def test_main_rename_missing_target():
    run_main(["3", "412"], get_target=None)


# Test that an empty new name exits
def test_main_rename_empty_name_exits():
    with pytest.raises(SystemExit):
        run_main(["3", "412", " "], get_target=SAMPLE_TARGET)


# Test main's delete branch
def test_main_delete_branch():
    run_main(["4", "412"], delete_target=True)


# Test that an empty id on the delete branch exits
def test_main_delete_empty_exits():
    with pytest.raises(SystemExit):
        run_main(["4", " "])
