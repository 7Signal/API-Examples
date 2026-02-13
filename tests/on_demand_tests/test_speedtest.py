import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.on_demand_tests import speedtest

# Test that the function 'start_speedtest' exists
def test_start_speedtest_function_exists():
    assert hasattr(speedtest, "start_speedtest")

# Test that start_speedtest handles a successful API call
@patch("examples.on_demand_tests.speedtest.requests.post")
def test_start_speedtest_success(mock_post, caplog):
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

    with caplog.at_level("INFO"):
        response = speedtest.start_speedtest(token, SENSOR_ID, ACCESS_POINT_ID)

    assert response["testId"] == "test123"
    assert "Speedtest started" in caplog.text

# Test that get_speedtest_status handles a successful GET
@patch("examples.on_demand_tests.speedtest.requests.get")
def test_get_speedtest_status_success(mock_get):
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

    status = speedtest.get_speedtest_status(token, SENSOR_ID, test_id)
    assert status["runStatus"] == "COMPLETE"

# Test that get_speedtest_status returns None on 404
@patch("examples.on_demand_tests.speedtest.requests.get")
def test_get_speedtest_status_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    token = "fake-token"
    SENSOR_ID = "sensor-001"
    test_id = "test123"

    status = speedtest.get_speedtest_status(token, SENSOR_ID, test_id)
    assert status is None

# Sample API response used across display tests
SAMPLE_RESULTS = {
    "attribution": {"poweredBy": "Speedtest.net - http://speedtest.net"},
    "download": {
        "throughputMbps": 263.358816,
        "bytes": 501016267,
        "elapsedMilliseconds": 15016,
        "latencyMilliseconds": 19.123,
        "latencyLowMilliseconds": 6.195,
        "latencyHighMilliseconds": 2083.321,
        "jitterMilliseconds": 21.421,
    },
    "upload": {
        "throughputMbps": 153.845088,
        "bytes": 281741118,
        "elapsedMilliseconds": 14999,
        "latencyMilliseconds": 9.996,
        "latencyLowMilliseconds": 4.645,
        "latencyHighMilliseconds": 29.376,
        "jitterMilliseconds": 3.283,
    },
    "ping": {
        "latencyMilliseconds": 5.731,
        "latencyLowMilliseconds": 5.026,
        "latencyHighMilliseconds": 11.525,
        "jitterMilliseconds": 2.908,
    },
    "selectedServer": {
        "id": 42209,
        "latency": 4.712,
        "name": "Independents Fiber Network",
        "host": "speedtest.ifnetwork.biz",
        "port": 8080,
        "location": "Columbus, OH",
        "country": "United States",
    },
    "interface": {
        "internalIp": "192.168.50.38",
        "macAddress": "B8:99:19:63:16:8D",
        "externalIp": "67.159.206.177",
        "vpn": False,
        "interface": "ath2",
    },
}

# Test that display_speedtest_results prints formatted output
def test_display_speedtest_results(capsys):
    speedtest.display_speedtest_results(SAMPLE_RESULTS)
    output = capsys.readouterr().out

    # Verify header
    assert "SPEEDTEST RESULTS" in output
    assert "Speedtest.net" in output

    # Verify throughput chart contains download and upload bars
    assert "Download" in output
    assert "Upload" in output
    assert "263.36" in output
    assert "153.85" in output

    # Verify sections are present
    assert "PING" in output
    assert "DOWNLOAD" in output
    assert "UPLOAD" in output
    assert "SERVER" in output
    assert "INTERFACE" in output

    # Verify specific data values appear
    assert "Independents Fiber Network" in output
    assert "192.168.50.38" in output

# Test that draw_throughput_chart returns a valid chart string
def test_draw_throughput_chart():
    chart = speedtest.draw_throughput_chart(263.36, 153.85)

    # Chart should contain bar characters and labels
    assert "Download" in chart
    assert "Upload" in chart
    assert "263.36" in chart
    assert "153.85" in chart
    assert "Mbps" in chart
    # Chart should contain filled and empty bar characters
    assert "\u2588" in chart
    assert "\u2591" in chart

# Test that display handles missing/partial data gracefully
def test_display_speedtest_results_partial_data(capsys):
    partial_results = {
        "download": {"throughputMbps": 100.0, "bytes": 50000000, "elapsedMilliseconds": 10000},
        "upload": {"throughputMbps": 50.0, "bytes": 25000000, "elapsedMilliseconds": 10000},
    }
    speedtest.display_speedtest_results(partial_results)
    output = capsys.readouterr().out

    assert "SPEEDTEST RESULTS" in output
    assert "100.00" in output
    assert "50.00" in output
