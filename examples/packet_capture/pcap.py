# This script demonstrates how to perform an on-demand packet capture on a sensor.
# It shows how to:
#  - Start a packet capture on the /on-demand-tests/sensors/{sensorId}/packet-capture endpoint
#  - Poll the capture status until it completes or fails
#  - Download the resulting pcap file locally

import os
import time
import logging
import requests
import sys 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Environment variables
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

def start_packet_capture(token, sensor_id):
    # Sends a POST request to initiate packet capture on a given sensor/AP.
    url = f"https://{API_HOST}/on-demand-tests/sensors/{sensor_id}/packet-capture"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

     # Define payload describing the data
    payload = {
        "mode": "CHANNEL",
        "captureTimeSeconds": "10",
        "captureFilter": "",
        "band": 5, 
        "channel": 36 
    }

    logging.debug(f"POST {url} with payload: {payload}")

    # Make the POST request to start the capture
    response = requests.post(url, headers=headers, json=payload)

    # If response code is not successful, log the error content for troubleshooting
    if not response.ok:
        logging.error(f"Response content: {response.text}")
    response.raise_for_status()

    # Parse JSON body of the successful response
    data = response.json()
    logging.info(f"Packet capture started, response: {data}")
    return data

def get_packet_capture_status(token, sensor_id, test_id):
    # Get packet capture status
    # Returns JSON response if available, or None if status file isn't ready yet (404).
    url = f"https://{API_HOST}/on-demand-tests/sensors/{sensor_id}/packet-capture/{test_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    logging.debug(f"GET {url} for status check")
    try:
        # Send GET request to retrieve current capture status
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            # If status file not found (404), capture file not ready yet, so return None to retry later
            logging.info("Status file not ready yet (404), will retry...")
            return None  # Indicate status not ready
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching status: {e}")
        return None

def download_packet_capture(token, sensor_id, test_id):
    # Downloads the completed pcap file and saves it locally.
    url = f"https://{API_HOST}/on-demand-tests/sensors/{sensor_id}/packet-capture/{test_id}/download"
    headers = {
        "accept": "application/octet-stream",
        "Authorization": f"Bearer {token}"
    }
    logging.debug(f"GET {url} to download pcap")

    # Make GET request to download the raw pcap file content
    response = requests.get(url, headers=headers)

    # Log error content if download response failed
    if not response.ok:
        logging.error(f"Download response content: {response.text}")
    response.raise_for_status()

    # Define local filename based on test ID
    filename = f"packet_capture_{test_id}.pcap"

    # Write the content to the file
    with open(filename, "wb") as f:
        f.write(response.content)
    logging.info(f"Packet capture saved as {filename}")
    return filename

def main():
    # Ask user for sensor_id at runtime
    sensor_id = input("Enter the SENSOR ID: ").strip()
    if not sensor_id:
        logging.error("sensor_id cannot be empty.")
        sys.exit(1)
    
    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Start the packet capture
    start_response = start_packet_capture(token, sensor_id)

    # Extract the testId from response to use for status polling and download
    # Normally the API should always return a testId; if it's missing, the response was unexpected.
    test_id = start_response.get("testId")
    # This check stops execution early to avoid making later requests with an invalid ID.
    if not test_id:
        logging.error("No testId received from start packet capture response")
        return

    logging.info(f"Packet capture initiated with testId: {test_id}")

    # Step 3: Poll for status until capture is complete or fails
    max_retries = 30  # number of polling attempts
    retries = 0

    while retries < max_retries:
        # Request current status of the capture
        status_response = get_packet_capture_status(token, sensor_id, test_id)
        # A 404 usually means the packet capture status file isn’t ready yet, not that the test failed.
        # Returning None tells the loop to wait and retry instead of treating it as an error.
        if status_response is None:
            # Status not ready yet, wait and retry
            retries += 1
            time.sleep(5)
            continue

        # Extract run status from response
        run_status = status_response.get("runStatus")
        logging.info(f"Run Status: {run_status}")

        if run_status == "COMPLETE":
            # Step 4: Download the completed capture
            logging.info("Packet capture completed successfully.")
            download_packet_capture(token, sensor_id, test_id)
            break
        elif run_status == "FAILED":
            # Capture failed (log reason if available)
            logging.error(f"Packet capture failed: {status_response.get('errorMessage')}")
            break
        else:
            # Capture still running (wait before polling again)
            logging.debug("Packet capture still in progress, waiting 5 seconds...")
            time.sleep(5)
            retries += 1
    else:
        logging.error("Max retries exceeded waiting for packet capture to complete.")

if __name__ == "__main__":
    main()
