import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.packet_capture import pcap  # adjust if your module filename is different

# Test that the function 'start_packet_capture' exists
def test_start_packet_capture_function_exists():
    assert hasattr(pcap, "start_packet_capture")

# Test that start_packet_capture handles a successful API call
@patch("examples.packet_capture.pcap.requests.post")
def test_start_packet_capture_success(mock_post, caplog):
    sample_response = {"testId": "test123"}
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = sample_response
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    token = "fake-token"
    SENSOR_ID = "sensor-001"

    with caplog.at_level("INFO"):
        response = pcap.start_packet_capture(token, SENSOR_ID)

    assert response["testId"] == "test123"
    assert "Packet capture started" in caplog.text

# Test that get_packet_capture_status handles a successful GET
@patch("examples.packet_capture.pcap.requests.get")
def test_get_packet_capture_status_success(mock_get):
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

    status = pcap.get_packet_capture_status(token, SENSOR_ID, test_id)
    assert status["runStatus"] == "COMPLETE"

# Test that download_packet_capture writes file content correctly
@patch("examples.packet_capture.pcap.requests.get")
@patch("builtins.open")
def test_download_packet_capture_success(mock_open, mock_get, caplog):
    fake_content = b"pcap-data"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.content = fake_content
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    token = "fake-token"
    SENSOR_ID = "sensor-001"
    test_id = "test123"

    with caplog.at_level("INFO"):
        filename = pcap.download_packet_capture(token, SENSOR_ID, test_id)

    mock_open.assert_called_once_with(filename, "wb")
    assert filename == f"packet_capture_{test_id}.pcap"
    assert "Packet capture saved" in caplog.text
