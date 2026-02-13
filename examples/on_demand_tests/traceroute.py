# This script demonstrates how to perform an on-demand traceroute test on a sensor.
# It shows how to:
#  - Start a traceroute test on the /on-demand-tests/sensors/{sensorId}/traceroute endpoint
#  - Poll the test status until it completes or fails
#  - Display the resulting traceroute metrics

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

def start_traceroute(token, sensor_id, access_point_id, target_host):
    # Sends a POST request to initiate a traceroute test on a given sensor/AP.
    url = f"https://{API_HOST}/on-demand-tests/sensors/{sensor_id}/traceroute"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Define payload describing the traceroute test configuration
    payload = {
        "testType": "WLAN",
        "accessPointId": access_point_id,
        "ipAddress": {
            "ipProtocol": "IPV4",
            "useDhcp": True
        },
        "testEndpoint": {
            "testHost": target_host,
            "resolveDNSOnSensor": True
        },
        "minimumTtl": 1,
        "maximumTtl": 255,
        "queriesPerHop": 5,
        "timeoutMilliseconds": 2000,
        "testTimeoutSeconds": 20,
        "qosCategory": "BEST_EFFORT_0"
    }

    logging.debug(f"POST {url} with payload: {payload}")

    # Make the POST request to start the traceroute test
    response = requests.post(url, headers=headers, json=payload)

    # If response code is not successful, log the error content for troubleshooting
    if not response.ok:
        logging.error(f"Response content: {response.text}")
    response.raise_for_status()

    # Parse JSON body of the successful response
    data = response.json()
    logging.info(f"Traceroute test started, response: {data}")
    return data

def get_traceroute_status(token, sensor_id, test_id):
    # Get traceroute test status.
    # Returns JSON response if available, or None if status file isn't ready yet (404).
    url = f"https://{API_HOST}/on-demand-tests/sensors/{sensor_id}/traceroute/{test_id}"
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

def _aggregate_hop_latencies(hops):
    # Compute average latency per unique hop number for charting.
    # Returns list of (hop_num, first_ip, avg_ms) sorted by hop number.
    seen = {}
    for h in hops:
        hop_num = h.get("hop")
        ip = h.get("ipAddress", "?")
        times = [t for t in h.get("timeMilliseconds", []) if t is not None]
        if hop_num not in seen:
            seen[hop_num] = (ip, times)
        else:
            seen[hop_num] = (seen[hop_num][0], seen[hop_num][1] + times)

    result = []
    for hop_num in sorted(seen.keys()):
        ip, times = seen[hop_num]
        if times:
            avg = sum(times) / len(times)
            result.append((hop_num, ip, avg))
    return result

def draw_latency_chart(hops):
    # Returns an ASCII bar chart showing average latency per hop.
    hop_avgs = _aggregate_hop_latencies(hops)
    if not hop_avgs:
        return ""

    max_val = _round_up_nice(max(avg for _, _, avg in hop_avgs) * 1.1)
    bar_width = 40

    lines = [""]
    for hop_num, ip, avg in hop_avgs:
        filled = int((avg / max_val) * bar_width)
        bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
        lines.append(f"  Hop {hop_num:<3} {bar}  {avg:>9.1f} ms")

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
    lines.append(f"          {scale}")
    return "\n".join(lines)

def _print_section(title, rows):
    # Prints a formatted section with a title and key-value rows.
    print(f"\n  {title}")
    print(f"  {'─' * 42}")
    for label, value in rows:
        print(f"  {label:<20} {value}")

def _print_route_table(hops):
    # Prints a formatted table of traceroute hop results.
    max_probes = max((len(h.get("timeMilliseconds", [])) for h in hops), default=0)
    if max_probes == 0:
        return

    probe_w = 7
    hop_w = 3
    ip_w = 22
    avg_w = 10

    # Build probe column headers
    probe_headers = "".join(f"{'#' + str(i+1):>{probe_w}}" for i in range(max_probes))
    total_w = hop_w + 2 + ip_w + 2 + max_probes * probe_w + 2 + avg_w

    print(f"\n  ROUTE")
    print(f"  {'─' * total_w}")
    print(f"  {'Hop':>{hop_w}}  {'IP Address':<{ip_w}}  {probe_headers}  {'Avg (ms)':>{avg_w}}")
    print(f"  {'─' * total_w}")

    for h in hops:
        hop_num = h.get("hop", "?")
        ip = h.get("ipAddress", "N/A")
        times = h.get("timeMilliseconds", [])

        # Format each probe value
        probes_str = ""
        valid_times = []
        for t in times:
            if t is None:
                probes_str += f"{'*':>{probe_w}}"
            else:
                probes_str += f"{t:>{probe_w}}"
                valid_times.append(t)

        # Pad remaining columns if fewer probes than max
        remaining = max_probes - len(times)
        probes_str += " " * (remaining * probe_w)

        # Calculate average of valid probe times
        if valid_times:
            avg = sum(valid_times) / len(valid_times)
            avg_str = f"{avg:>{avg_w}.1f}"
        else:
            avg_str = f"{'N/A':>{avg_w}}"

        print(f"  {hop_num:>{hop_w}}  {ip:<{ip_w}}  {probes_str}  {avg_str}")

def display_traceroute_results(results):
    # Formats and prints the traceroute test results in a readable layout with an ASCII latency chart.
    attach_time = results.get("attachTimeMilliseconds", "N/A")
    ip_retrieval_time = results.get("ipRetrievalTimeMilliseconds", "N/A")
    ip_address = results.get("ipAddress", "N/A")
    gateway = results.get("gatewayAddress", "N/A")
    hops = results.get("traceRouteResults", [])

    # Header
    width = 60
    print("")
    print(f"  {'═' * width}")
    print(f"  {'TRACEROUTE RESULTS':^{width}}")
    print(f"  {'═' * width}")

    # ASCII latency chart
    if hops:
        print(draw_latency_chart(hops))

    # Connection section
    _print_section("CONNECTION", [
        ("Attach Time",      f"{attach_time} ms"),
        ("IP Retrieval Time", f"{ip_retrieval_time} ms"),
        ("IP Address",       ip_address),
        ("Gateway",          gateway),
    ])

    # Route table
    if hops:
        _print_route_table(hops)

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

    # Ask user for target host
    target_host = input("Enter the TARGET HOST (e.g. 8.8.8.8): ").strip()
    if not target_host:
        logging.error("target_host cannot be empty.")
        sys.exit(1)

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Start the traceroute test
    start_response = start_traceroute(token, sensor_id, access_point_id, target_host)

    # Extract the testId from response to use for status polling
    # Normally the API should always return a testId; if it's missing, the response was unexpected.
    test_id = start_response.get("testId")
    # This check stops execution early to avoid making later requests with an invalid ID.
    if not test_id:
        logging.error("No testId received from start traceroute response")
        return

    logging.info(f"Traceroute test initiated with testId: {test_id}")

    # Step 3: Poll for status until test is complete or fails
    max_retries = 60  # number of polling attempts
    retries = 0

    while retries < max_retries:
        # Request current status of the test
        status_response = get_traceroute_status(token, sensor_id, test_id)
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
            logging.info("Traceroute test completed successfully.")
            # The test metrics are nested under the "results" key
            results = status_response.get("results", status_response)
            display_traceroute_results(results)
            break
        elif run_status == "FAILED":
            # Test failed (log reason if available)
            logging.error(f"Traceroute test failed: {status_response.get('errorMessage')}")
            break
        else:
            # Test still running (wait before polling again)
            logging.debug("Traceroute test still in progress, waiting 5 seconds...")
            time.sleep(5)
            retries += 1
    else:
        logging.error("Max retries exceeded waiting for traceroute test to complete.")

if __name__ == "__main__":
    main()
