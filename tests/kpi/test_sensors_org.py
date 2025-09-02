import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the root directory so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module to be tested
from examples.kpi import sensors_org

# Test that the function 'fetch_sensor_kpis_by_org' exists
def test_fetch_sensor_kpis_by_org_function_exists():
    assert hasattr(sensors_org, "fetch_sensor_kpis_by_org")

# Test that fetch_sensor_kpis_by_org correctly handles a successful API call
@patch("examples.kpi.sensors_org.requests.get")
def test_fetch_sensor_kpis_by_org_success(mock_get, caplog):
    # Sample data returned from mocked API call
    sample_data = {
        "range": {},
        "results": [
            {
                "name": "Test KPI",
                "kpiCode": "KPI123",
                "description": "Test KPI description",
                "measurements24GHz": []
            }
        ]
    }

    # Mock response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = sample_data
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    # Provide a fake token
    token = "fake-token"
    KPI_CODE = "KPI123"

    # Call the function under test using the correct module name
    with caplog.at_level("INFO"):
        sensors_org.fetch_sensor_kpis_by_org(token, KPI_CODE)

    # Assert that expected logs appear
    assert "===== KPI Summary" in caplog.text
    assert "Test KPI" in caplog.text
    assert "KPI123" in caplog.text
    assert "Test KPI description" in caplog.text

# Test that log_kpi_summary runs without throwing errors
def test_log_kpi_summary_runs(caplog):
    sample_data = {
        "range": {},
        "results": [
            {
                "name": "Sample KPI",
                "kpiCode": "SAMPLE123",
                "description": "Sample description",
                "measurements24GHz": []
            }
        ]
    }

    with caplog.at_level("INFO"):
        sensors_org.log_kpi_summary(sample_data)

    assert "Sample KPI" in caplog.text
    assert "SAMPLE123" in caplog.text
    assert "Sample description" in caplog.text
