import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.default_configurations import default_configurations_sensors as dc

SAMPLE_CONFIG = {
    "id": 5,
    "name": "Standard Branch Office",
    "testProfileTemplateId": 22,
    "otaConfigurationId": 3,
    "alarmGroupId": 9,
    "sonarId": 412,
    "pingEndPointId": 415,
    "webServerId": 417,
    "slaGroupId": 2,
}

SAMPLE_LIST = {
    "results": [SAMPLE_CONFIG],
    "pagination": {"perPage": 10, "page": 1, "total": 1, "pages": 1},
}


# Test that the expected functions exist
def test_functions_exist():
    assert hasattr(dc, "list_default_configurations")
    assert hasattr(dc, "get_default_configuration")
    assert hasattr(dc, "display_default_configurations")


# Test that the list endpoint is read correctly
@patch("examples.default_configurations.default_configurations_sensors.requests.get")
def test_list_default_configurations_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_LIST
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = dc.list_default_configurations("fake-token")

    assert data["results"][0]["id"] == 5
    assert mock_get.call_args.kwargs["params"]["page"] == 1


# Test that a single configuration is read correctly
@patch("examples.default_configurations.default_configurations_sensors.requests.get")
def test_get_default_configuration_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_CONFIG
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    config = dc.get_default_configuration("fake-token", 5)

    assert config["name"] == "Standard Branch Office"


# Test that a missing configuration returns None rather than raising
@patch("examples.default_configurations.default_configurations_sensors.requests.get")
def test_get_default_configuration_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    assert dc.get_default_configuration("fake-token", 999) is None


# Test that display logs the bundle contents
def test_display_default_configurations(caplog):
    with caplog.at_level("INFO"):
        dc.display_default_configurations(SAMPLE_LIST)

    assert "Standard Branch Office" in caplog.text
    assert "412" in caplog.text


# Test that a bundle which applies only some references still displays
def test_display_default_configurations_partial_data(caplog):
    partial = {"results": [{"id": 6, "name": "Minimal", "slaGroupId": 1}]}

    with caplog.at_level("INFO"):
        dc.display_default_configurations(partial)

    assert "Minimal" in caplog.text


# Test that an empty result set is reported rather than failing
def test_display_default_configurations_empty(caplog):
    with caplog.at_level("INFO"):
        dc.display_default_configurations({"results": [], "pagination": {}})

    assert "No sensor default configurations" in caplog.text


# ---------------------------------------------------------------------------
# Error handling and main() flows
# ---------------------------------------------------------------------------

import requests as _requests

MODULE = "examples.default_configurations.default_configurations_sensors"


def http_error_response():
    r = MagicMock()
    r.status_code = 400
    r.text = "Bad Request"
    r.raise_for_status.side_effect = _requests.exceptions.HTTPError("400")
    return r


# Test that HTTP errors on the read calls return None
@patch(f"{MODULE}.requests.get")
def test_read_calls_http_error(mock_get, caplog):
    mock_get.return_value = http_error_response()

    with caplog.at_level("ERROR"):
        assert dc.list_default_configurations("fake-token") is None
        assert dc.get_default_configuration("fake-token", 1) is None

    assert "HTTP error" in caplog.text


# Test that a connection-level failure is caught rather than escaping
@patch(f"{MODULE}.requests.get", side_effect=_requests.exceptions.ConnectionError("boom"))
def test_list_connection_error(mock_get, caplog):
    with caplog.at_level("ERROR"):
        assert dc.list_default_configurations("fake-token") is None

    assert "Unexpected error" in caplog.text


# Test that a bundle applying nothing is described rather than shown blank
def test_display_empty_bundle(caplog):
    with caplog.at_level("INFO"):
        dc.display_default_configurations({"results": [{"id": 9, "name": "Empty"}]})

    assert "empty bundle" in caplog.text


def run_main(input_values, **extra):
    applied = [
        patch(f"{MODULE}.get_token", return_value=("tok", 0)),
        patch(f"{MODULE}.list_default_configurations", return_value=SAMPLE_LIST),
        patch("builtins.input", side_effect=input_values),
    ]
    for target, value in extra.items():
        applied.append(patch(f"{MODULE}.{target}", return_value=value))
    for p in applied:
        p.start()
    try:
        dc.main()
    finally:
        for p in reversed(applied):
            p.stop()


# Test that main lists the bundles and then skips when Enter is pressed
def test_main_skip_branch(caplog):
    with caplog.at_level("INFO"):
        run_main([""])

    assert "Standard Branch Office" in caplog.text


# Test that main drills into a chosen bundle
def test_main_fetch_branch():
    run_main(["5"], get_default_configuration=SAMPLE_CONFIG)


# Test that a missing bundle simply returns
def test_main_fetch_missing():
    run_main(["999"], get_default_configuration=None)
