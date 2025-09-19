import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import requests

# Add root directory to sys.path so that network_agents module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the module under test
from examples.networks import network_agents


# Test that the 'fetch_networks_agents' function exists in the module
def test_fetch_networks_agents_function_exists():
    assert hasattr(network_agents, "fetch_networks_agents")


# Test that fetch_networks_agents correctly handles a successful API call
@patch("examples.networks.network_agents.requests.get")
def test_fetch_networks_agents_success(mock_get, caplog):
    # Sample API response to simulate a successful call
    sample_data = {
        "results": [
            {
                "id": "agent1",
                "name": "Agent One",
                "isEnabled": True,
                "createdAt": "2025-08-25T12:00:00Z",
                "updatedAt": "2025-08-26T12:00:00Z"
            }
        ]
    }

    # Create a mock response object to simulate requests.get return value
    mock_response = MagicMock()
    # Simulate HTTP 200 OK
    mock_response.status_code = 200   
    mock_response.ok = True
    # Return sample JSON
    mock_response.json.return_value = sample_data 
    # Prevent exception
    mock_response.raise_for_status = MagicMock() 
    # Patch requests.get
    mock_get.return_value = mock_response    

    token = "fake-token"

    # Call function under test, caplog captures logging output
    with caplog.at_level("INFO"):
        data = network_agents.fetch_networks_agents(token)

    # Verify that the returned data matches expected sample data
    assert data == sample_data
    # Verify that expected logging messages were emitted
    assert "Networks Agents fetched successfully." in caplog.text
    assert "Fetching networks agents" in caplog.text


# Test that log_networks_agents correctly logs agent details
def test_log_network_agents_runs(caplog):
    # Sample data structured as expected by log_networks_agents
    sample_data = {
        "results": [
            {
                "id": "agent1",
                "name": "Agent One",
                "isEnabled": True,
                "createdAt": "2025-08-25T12:00:00Z",
                "updatedAt": "2025-08-26T12:00:00Z"
            }
        ]
    }

    # Capture INFO-level logs during function execution
    with caplog.at_level("INFO"):
        network_agents.log_networks_agents(sample_data)

    # Verify that expected agent details appear in logs
    assert "ID: agent1" in caplog.text
    assert "Agent One" in caplog.text
    assert "True" in caplog.text
    assert "2025-08-25T12:00:00Z" in caplog.text
    assert "2025-08-26T12:00:00Z" in caplog.text


# Test that log_networks_agents logs a warning when no data is provided
def test_log_network_agents_warns_if_no_results(caplog):
    # Pass None to trigger warning
    with caplog.at_level("WARNING"):
        network_agents.log_networks_agents(None)

    # Verify that the warning message appears in logs
    assert "No results found in networks agents data." in caplog.text


# Test that fetch_networks_agents logs an error when the API request fails
@patch("examples.networks.network_agents.requests.get")
def test_fetch_network_agents_failure(mock_get, caplog):
    # Simulate a network or API error
    mock_get.side_effect = requests.exceptions.RequestException("Network error")

    # Capture ERROR-level logs
    with caplog.at_level("ERROR"):
        data = network_agents.fetch_networks_agents("fake-token")

    # Verify function returns None on failure
    assert data is None
    # Verify that the expected error message is logged
    assert "Error fetching networks agents: Network error" in caplog.text
