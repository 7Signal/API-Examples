import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.on_demand_tests import http_download

# Test that the function 'start_http_download' exists
def test_start_http_download_function_exists():
    assert hasattr(http_download, "start_http_download")

# Test that start_http_download handles a successful API call
@patch("examples.on_demand_tests.http_download.requests.post")
def test_start_http_download_success(mock_post, caplog):
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
        response = http_download.start_http_download(token, SENSOR_ID, ACCESS_POINT_ID)

    assert response["testId"] == "test123"
    assert "HTTP download test started" in caplog.text

# Test that get_http_download_status handles a successful GET
@patch("examples.on_demand_tests.http_download.requests.get")
def test_get_http_download_status_success(mock_get):
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

    status = http_download.get_http_download_status(token, SENSOR_ID, test_id)
    assert status["runStatus"] == "COMPLETE"

# Test that get_http_download_status returns None on 404
@patch("examples.on_demand_tests.http_download.requests.get")
def test_get_http_download_status_404_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    token = "fake-token"
    SENSOR_ID = "sensor-001"
    test_id = "test123"

    status = http_download.get_http_download_status(token, SENSOR_ID, test_id)
    assert status is None

# Sample API response used across display tests
SAMPLE_RESULTS = {
    "attachTimeMilliseconds": 758,
    "ipRetrievalTimeMilliseconds": 1094,
    "ipAddress": "192.0.2.38",
    "gatewayAddress": "192.0.2.1",
    "httpDownloadResults": [
        {
            "testNumber": 1,
            "qosCategory": 0,
            "throughputMbps": 93.241932
        }
    ]
}

# Test that display_http_download_results prints formatted output
def test_display_http_download_results(capsys):
    http_download.display_http_download_results(SAMPLE_RESULTS)
    output = capsys.readouterr().out

    # Verify header
    assert "HTTP DOWNLOAD RESULTS" in output

    # Verify connection section
    assert "CONNECTION" in output
    assert "758 ms" in output
    assert "1094 ms" in output
    assert "192.0.2.38" in output
    assert "192.0.2.1" in output

    # Verify download section
    assert "DOWNLOAD" in output
    assert "93.241932 Mbps" in output

    # Verify throughput chart
    assert "Test 1" in output
    assert "Mbps" in output
    assert "\u2588" in output
    assert "\u2591" in output

# Test that draw_throughput_chart returns a valid chart string
def test_draw_throughput_chart():
    download_results = [
        {"testNumber": 1, "qosCategory": 0, "throughputMbps": 93.24}
    ]
    chart = http_download.draw_throughput_chart(download_results)

    assert "Test 1" in chart
    assert "93.24" in chart
    assert "Mbps" in chart
    assert "\u2588" in chart
    assert "\u2591" in chart

# Test that display handles missing/partial data gracefully
def test_display_http_download_results_partial_data(capsys):
    partial_results = {
        "attachTimeMilliseconds": 500,
        "ipAddress": "192.0.2.10",
    }
    http_download.display_http_download_results(partial_results)
    output = capsys.readouterr().out

    assert "HTTP DOWNLOAD RESULTS" in output
    assert "500 ms" in output
    assert "192.0.2.10" in output
