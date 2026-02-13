# This script demonstrates how to perform an on-demand speedtest on a sensor.
# It shows how to:
#  - Start a speedtest on the /on-demand-tests/sensors/{sensorId}/speedtest endpoint
#  - Poll the speedtest status until it completes or fails
#  - Display the resulting speedtest metrics

import os
import time
import math
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

def start_speedtest(token, sensor_id, access_point_id):
    # Sends a POST request to initiate a speedtest on a given sensor/AP.
    url = f"https://{API_HOST}/on-demand-tests/sensors/{sensor_id}/speedtest"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Define payload describing the speedtest configuration
    payload = {
        "testType": "WLAN",
        "accessPointId": access_point_id,
        "maxAttachTimeoutMilliseconds": 20000,
        "maxIpAddressWaitTimeMilliseconds": 60000,
        "ipAddress": {
            "ipProtocol": "IPV4",
            "useDhcp": True
        }
    }

    logging.debug(f"POST {url} with payload: {payload}")

    # Make the POST request to start the speedtest
    response = requests.post(url, headers=headers, json=payload)

    # If response code is not successful, log the error content for troubleshooting
    if not response.ok:
        logging.error(f"Response content: {response.text}")
    response.raise_for_status()

    # Parse JSON body of the successful response
    data = response.json()
    logging.info(f"Speedtest started, response: {data}")
    return data

def get_speedtest_status(token, sensor_id, test_id):
    # Get speedtest status
    # Returns JSON response if available, or None if status file isn't ready yet (404).
    url = f"https://{API_HOST}/on-demand-tests/sensors/{sensor_id}/speedtest/{test_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    logging.debug(f"GET {url} for status check")
    try:
        # Send GET request to retrieve current speedtest status
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            # If status file not found (404), speedtest not ready yet, so return None to retry later
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

def _format_bytes(byte_count):
    # Format bytes into a human-readable string.
    if byte_count >= 1_000_000_000:
        return f"{byte_count / 1_000_000_000:.2f} GB"
    elif byte_count >= 1_000_000:
        return f"{byte_count / 1_000_000:.2f} MB"
    elif byte_count >= 1_000:
        return f"{byte_count / 1_000:.2f} KB"
    return f"{byte_count} B"

def draw_throughput_chart(download_mbps, upload_mbps):
    # Returns an ASCII bar chart showing download and upload throughput.
    max_val = _round_up_nice(max(download_mbps, upload_mbps) * 1.1)
    bar_width = 40

    dl_filled = int((download_mbps / max_val) * bar_width)
    ul_filled = int((upload_mbps / max_val) * bar_width)

    dl_bar = "\u2588" * dl_filled + "\u2591" * (bar_width - dl_filled)
    ul_bar = "\u2588" * ul_filled + "\u2591" * (bar_width - ul_filled)

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

    lines = [
        "",
        f"  Download  {dl_bar}  {download_mbps:>8.2f} Mbps",
        f"  Upload    {ul_bar}  {upload_mbps:>8.2f} Mbps",
        "",
        f"            {scale}",
    ]
    return "\n".join(lines)

def _print_section(title, rows):
    # Prints a formatted section with a title and key-value rows.
    print(f"\n  {title}")
    print(f"  {'─' * 42}")
    for label, value in rows:
        print(f"  {label:<20} {value}")

def display_speedtest_results(results):
    # Formats and prints the speedtest results in a readable layout with an ASCII throughput chart.
    download = results.get("download", {})
    upload = results.get("upload", {})
    ping = results.get("ping", {})
    server = results.get("selectedServer", {})
    interface = results.get("interface", {})
    attribution = results.get("attribution", {})

    powered_by = attribution.get("poweredBy", "")

    # Header
    width = 60
    print("")
    print(f"  {'═' * width}")
    print(f"  {'SPEEDTEST RESULTS':^{width}}")
    if powered_by:
        print(f"  {powered_by:^{width}}")
    print(f"  {'═' * width}")

    # ASCII throughput chart
    dl_mbps = download.get("throughputMbps", 0)
    ul_mbps = upload.get("throughputMbps", 0)
    if dl_mbps or ul_mbps:
        print(draw_throughput_chart(dl_mbps, ul_mbps))

    # Ping section
    if ping:
        _print_section("PING", [
            ("Latency",  f"{ping.get('latencyMilliseconds', 'N/A')} ms"),
            ("Jitter",   f"{ping.get('jitterMilliseconds', 'N/A')} ms"),
            ("Low",      f"{ping.get('latencyLowMilliseconds', 'N/A')} ms"),
            ("High",     f"{ping.get('latencyHighMilliseconds', 'N/A')} ms"),
        ])

    # Download section
    if download:
        dl_bytes = download.get("bytes", 0)
        dl_elapsed = download.get("elapsedMilliseconds", 0)
        _print_section("DOWNLOAD", [
            ("Throughput",     f"{download.get('throughputMbps', 'N/A')} Mbps"),
            ("Data",           _format_bytes(dl_bytes)),
            ("Duration",       f"{dl_elapsed / 1000:.2f} s"),
            ("Latency",        f"{download.get('latencyMilliseconds', 'N/A')} ms"),
            ("Latency Range",  f"{download.get('latencyLowMilliseconds', 'N/A')} - {download.get('latencyHighMilliseconds', 'N/A')} ms"),
            ("Jitter",         f"{download.get('jitterMilliseconds', 'N/A')} ms"),
        ])

    # Upload section
    if upload:
        ul_bytes = upload.get("bytes", 0)
        ul_elapsed = upload.get("elapsedMilliseconds", 0)
        _print_section("UPLOAD", [
            ("Throughput",     f"{upload.get('throughputMbps', 'N/A')} Mbps"),
            ("Data",           _format_bytes(ul_bytes)),
            ("Duration",       f"{ul_elapsed / 1000:.2f} s"),
            ("Latency",        f"{upload.get('latencyMilliseconds', 'N/A')} ms"),
            ("Latency Range",  f"{upload.get('latencyLowMilliseconds', 'N/A')} - {upload.get('latencyHighMilliseconds', 'N/A')} ms"),
            ("Jitter",         f"{upload.get('jitterMilliseconds', 'N/A')} ms"),
        ])

    # Server section
    if server:
        location = server.get("location", "")
        country = server.get("country", "")
        full_location = f"{location}, {country}" if location and country else location or country
        _print_section("SERVER", [
            ("Name",     server.get("name", "N/A")),
            ("Location", full_location or "N/A"),
            ("Host",     f"{server.get('host', 'N/A')}:{server.get('port', '')}"),
            ("Latency",  f"{server.get('latency', 'N/A')} ms"),
        ])

    # Interface section
    if interface:
        vpn_status = "Yes" if interface.get("vpn") else "No"
        _print_section("INTERFACE", [
            ("Internal IP",  interface.get("internalIp", "N/A")),
            ("External IP",  interface.get("externalIp", "N/A")),
            ("MAC",          interface.get("macAddress", "N/A")),
            ("Interface",    interface.get("interface", "N/A")),
            ("VPN",          vpn_status),
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

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Start the speedtest
    start_response = start_speedtest(token, sensor_id, access_point_id)

    # Extract the testId from response to use for status polling
    # Normally the API should always return a testId; if it's missing, the response was unexpected.
    test_id = start_response.get("testId")
    # This check stops execution early to avoid making later requests with an invalid ID.
    if not test_id:
        logging.error("No testId received from start speedtest response")
        return

    logging.info(f"Speedtest initiated with testId: {test_id}")

    # Step 3: Poll for status until speedtest is complete or fails
    max_retries = 60  # number of polling attempts
    retries = 0

    while retries < max_retries:
        # Request current status of the speedtest
        status_response = get_speedtest_status(token, sensor_id, test_id)
        # A 404 usually means the speedtest status isn't ready yet, not that the test failed.
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
            # Step 4: Display the speedtest results
            logging.info("Speedtest completed successfully.")
            # The speedtest metrics are nested under the "results" key
            results = status_response.get("results", status_response)
            display_speedtest_results(results)
            break
        elif run_status == "FAILED":
            # Speedtest failed (log reason if available)
            logging.error(f"Speedtest failed: {status_response.get('errorMessage')}")
            break
        else:
            # Speedtest still running (wait before polling again)
            logging.debug("Speedtest still in progress, waiting 5 seconds...")
            time.sleep(5)
            retries += 1
    else:
        logging.error("Max retries exceeded waiting for speedtest to complete.")

if __name__ == "__main__":
    main()
