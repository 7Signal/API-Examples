# This script demonstrates how to perform an on-demand HTTP Download Throughput test on a sensor.
# It shows how to:
#  - Start an HTTP download test on the /on-demand-tests/sensors/{sensorId}/http-download endpoint
#  - Poll the test status until it completes or fails
#  - Display the resulting test metrics

import os
import time
import math
import json
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

def start_http_download(token, sensor_id, access_point_id, duration_seconds=5):
    # Sends a POST request to initiate an HTTP download throughput test on a given sensor/AP.
    url = f"https://{API_HOST}/on-demand-tests/sensors/{sensor_id}/http-download"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Define payload describing the HTTP download test configuration
    payload = {
        "testType": "WLAN",
        "accessPointId": access_point_id,
        "testEndpoint": {
            "testHost": "195.181.171.208", # central1 sonar
            "testPort": "80",
            "sonarId": None,
            "resolveDNSOnSensor": False
        },
        "ipAddress": {
            "ipProtocol": "IPV4",
            "useDhcp": True
        },
        "durationSeconds": str(duration_seconds),
        "testCount": 1,
        "qosCategory": "BEST_EFFORT_0",
        "sonarDSCP": 0
    }

    logging.debug(f"POST {url} with payload: {payload}")

    # Make the POST request to start the HTTP download test
    response = requests.post(url, headers=headers, json=payload)

    # If response code is not successful, log the error content for troubleshooting
    if not response.ok:
        logging.error(f"Response content: {response.text}")
    response.raise_for_status()

    # Parse JSON body of the successful response
    data = response.json()
    logging.info(f"HTTP download test started, response: {data}")
    return data

def get_http_download_status(token, sensor_id, test_id):
    # Get HTTP download test status.
    # Returns JSON response if available, or None if status file isn't ready yet (404).
    url = f"https://{API_HOST}/on-demand-tests/sensors/{sensor_id}/http-download/{test_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    logging.debug(f"GET {url} for status check")
    try:
        # Send GET request to retrieve current test status
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            # If status file not found (404), test not ready yet, so return None to retry later
            logging.info("Status file not ready yet (404), will retry...")
            return None  # Indicate status not ready
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching status: {e}")
        return None

def _round_up_nice(value):
    # Round up to a nice number for the chart scale.
    if value <= 0:
        return 100
    magnitude = 10 ** math.floor(math.log10(value))
    normalized = value / magnitude
    if normalized <= 1:
        nice = 1
    elif normalized <= 2:
        nice = 2
    elif normalized <= 5:
        nice = 5
    else:
        nice = 10
    return int(nice * magnitude)

def draw_throughput_chart(download_results):
    # Returns an ASCII bar chart showing download throughput for each test run.
    max_val = _round_up_nice(max(r["throughputMbps"] for r in download_results) * 1.1)
    bar_width = 40

    lines = [""]
    for r in download_results:
        mbps = r["throughputMbps"]
        filled = int((mbps / max_val) * bar_width)
        bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
        label = f"Test {r['testNumber']}"
        lines.append(f"  {label:<10} {bar}  {mbps:>8.2f} Mbps")

    # Build scale labels at 0%, 25%, 50%, 75%, 100%
    segment = bar_width // 4
    ticks = [max_val * i / 4 for i in range(5)]
    scale = ""
    for i, t in enumerate(ticks):
        label = f"{t:.0f}"
        if i < 4:
            scale += label.ljust(segment)
        else:
            scale += label

    lines.append("")
    lines.append(f"            {scale}")
    return "\n".join(lines)

def _print_section(title, rows):
    # Prints a formatted section with a title and key-value rows.
    print(f"\n  {title}")
    print(f"  {'─' * 42}")
    for label, value in rows:
        print(f"  {label:<20} {value}")

def display_http_download_results(results):
    # Formats and prints the HTTP download test results in a readable layout with an ASCII throughput chart.
    attach_time = results.get("attachTimeMilliseconds", "N/A")
    ip_retrieval_time = results.get("ipRetrievalTimeMilliseconds", "N/A")
    ip_address = results.get("ipAddress", "N/A")
    gateway = results.get("gatewayAddress", "N/A")
    download_results = results.get("httpDownloadResults", [])

    # Header
    width = 60
    print("")
    print(f"  {'═' * width}")
    print(f"  {'HTTP DOWNLOAD RESULTS':^{width}}")
    print(f"  {'═' * width}")

    # ASCII throughput chart
    if download_results:
        print(draw_throughput_chart(download_results))

    # Connection section
    _print_section("CONNECTION", [
        ("Attach Time",      f"{attach_time} ms"),
        ("IP Retrieval Time", f"{ip_retrieval_time} ms"),
        ("IP Address",       ip_address),
        ("Gateway",          gateway),
    ])

    # Download results section
    if download_results:
        _print_section("DOWNLOAD", [
            (f"Test {r['testNumber']}", f"{r['throughputMbps']} Mbps (QoS: {r['qosCategory']})")
            for r in download_results
        ])

    print("")

def main():
    # Ask user for sensor_id at runtime
    sensor_id = input("Enter the SENSOR ID: ").strip()
    if not sensor_id:
        logging.error("sensor_id cannot be empty.")
        sys.exit(1)

    # Ask user for access_point_id at runtime
    access_point_id_input = input("Enter the ACCESS POINT ID: ").strip()
    if not access_point_id_input:
        logging.error("access_point_id cannot be empty.")
        sys.exit(1)

    # Convert access_point_id to integer for the payload
    try:
        access_point_id = int(access_point_id_input)
    except ValueError:
        logging.error("access_point_id must be a valid integer.")
        sys.exit(1)

    # Ask user for duration in seconds (default 5)
    duration_input = input("Enter the DURATION in seconds (default 5): ").strip()
    if duration_input:
        try:
            duration_seconds = int(duration_input)
        except ValueError:
            logging.error("duration must be a valid integer.")
            sys.exit(1)
    else:
        duration_seconds = 5

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Start the HTTP download test
    start_response = start_http_download(token, sensor_id, access_point_id, duration_seconds)

    # Extract the testId from response to use for status polling
    # Normally the API should always return a testId; if it's missing, the response was unexpected.
    test_id = start_response.get("testId")
    # This check stops execution early to avoid making later requests with an invalid ID.
    if not test_id:
        logging.error("No testId received from start HTTP download response")
        return

    logging.info(f"HTTP download test initiated with testId: {test_id}")

    # Step 3: Poll for status until test is complete or fails
    max_retries = 60  # number of polling attempts
    retries = 0

    while retries < max_retries:
        # Request current status of the test
        status_response = get_http_download_status(token, sensor_id, test_id)
        # A 404 usually means the test status isn't ready yet, not that the test failed.
        # Returning None tells the loop to wait and retry instead of treating it as an error.
        if status_response is None:
            # Status not ready yet, wait and retry
            retries += 1
            time.sleep(5)
            continue

        # Extract run status and test status from response
        run_status = status_response.get("runStatus")
        test_status = status_response.get("testStatus")
        logging.info(f"Run Status: {run_status}, Test Status: {test_status}")

        if run_status == "COMPLETE":
            # Step 4: Display the test results
            logging.info("HTTP download test completed successfully.")
            # The test metrics are nested under the "results" key
            results = status_response.get("results", status_response)
            display_http_download_results(results)
            break
        elif run_status == "FAILED":
            # Test failed (log reason if available)
            logging.error(f"HTTP download test failed: {status_response.get('errorMessage')}")
            break
        else:
            # Test still running (wait before polling again)
            logging.debug("HTTP download test still in progress, waiting 5 seconds...")
            time.sleep(5)
            retries += 1
    else:
        logging.error("Max retries exceeded waiting for HTTP download test to complete.")

if __name__ == "__main__":
    main()
