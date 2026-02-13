import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.on_demand_tests import traceroute

# Test that the function 'start_traceroute' exists
def test_start_traceroute_function_exists():
    assert hasattr(traceroute, "start_traceroute")

# Test that start_traceroute handles a successful API call
@patch("examples.on_demand_tests.traceroute.requests.post")
def test_start_traceroute_success(mock_post, caplog):
    sample_response = {"testId": "test123"}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = sample_response
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    token = "fake-token"
    SENSOR_ID = "sensor-001"
    ACCESS_POINT_ID = 42
    TARGET_HOST = "8.8.8.8"

    with caplog.at_level("INFO"):
        response = traceroute.start_traceroute(token, SENSOR_ID, ACCESS_POINT_ID, TARGET_HOST)

    assert response["testId"] == "test123"
    assert "Traceroute test started" in caplog.text

# Test that get_traceroute_status handles a successful GET
@patch("examples.on_demand_tests.traceroute.requests.get")
def test_get_traceroute_status_success(mock_get):
    sample_status = {"runStatus": "COMPLETE"}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = sample_status
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    token = "fake-token"
    SENSOR_ID = "sensor-001"
    test_id = "test123"

    status = traceroute.get_traceroute_status(token, SENSOR_ID, test_id)
    assert status["runStatus"] == "COMPLETE"

# Test that get_traceroute_status returns None on 404
@patch("examples.on_demand_tests.traceroute.requests.get")
def test_get_traceroute_status_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    token = "fake-token"
    SENSOR_ID = "sensor-001"
    test_id = "test123"

    status = traceroute.get_traceroute_status(token, SENSOR_ID, test_id)
    assert status is None

# Sample API response used across display tests
SAMPLE_RESULTS = {
    "attachTimeMilliseconds": 912,
    "ipRetrievalTimeMilliseconds": 1369,
    "ipAddress": "192.168.50.44",
    "gatewayAddress": "192.168.50.1",
    "traceRouteResults": [
        {
            "hop": 1,
            "ipAddress": "192.168.50.1",
            "timeMilliseconds": [4524, 5571, 4439, 4684, 4119],
            "ttl": [64, 64, 64, 64, 64]
        },
        {
            "hop": 2,
            "ipAddress": "67.159.206.190",
            "timeMilliseconds": [5754, 5798, 7483, 6636, 6816],
            "ttl": [254, 254, 254, 254, 254]
        },
        {
            "hop": 3,
            "ipAddress": "216.66.73.141",
            "timeMilliseconds": [7330, 6834, 6490, 6678, 6768],
            "ttl": [62, 62, 62, 62, 62]
        },
        {
            "hop": 4,
            "ipAddress": "184.105.222.45",
            "timeMilliseconds": [19019, 19724, None, None, None],
            "ttl": [61, 61, None, None, None]
        }
    ]
}

# Test that display_traceroute_results prints formatted output
def test_display_traceroute_results(capsys):
    traceroute.display_traceroute_results(SAMPLE_RESULTS)
    output = capsys.readouterr().out

    # Verify header
    assert "TRACEROUTE RESULTS" in output

    # Verify connection section
    assert "CONNECTION" in output
    assert "912 ms" in output
    assert "1369 ms" in output
    assert "192.168.50.44" in output
    assert "192.168.50.1" in output

    # Verify route table
    assert "ROUTE" in output
    assert "67.159.206.190" in output
    assert "216.66.73.141" in output

    # Verify null probes shown as asterisks
    assert "*" in output

    # Verify latency chart
    assert "\u2588" in output
    assert "\u2591" in output

# Test that draw_latency_chart returns a valid chart string
def test_draw_latency_chart():
    hops = [
        {"hop": 1, "ipAddress": "192.168.50.1", "timeMilliseconds": [4524, 5571, 4439]},
        {"hop": 2, "ipAddress": "10.0.0.1", "timeMilliseconds": [5754, 5798, 7483]},
    ]
    chart = traceroute.draw_latency_chart(hops)

    assert "Hop 1" in chart
    assert "Hop 2" in chart
    assert "ms" in chart
    assert "\u2588" in chart
    assert "\u2591" in chart

# Test that display handles missing/partial data gracefully
def test_display_traceroute_results_partial_data(capsys):
    partial_results = {
        "attachTimeMilliseconds": 500,
        "ipAddress": "10.0.0.1",
    }
    traceroute.display_traceroute_results(partial_results)
    output = capsys.readouterr().out

    assert "TRACEROUTE RESULTS" in output
    assert "500 ms" in output
    assert "10.0.0.1" in output
