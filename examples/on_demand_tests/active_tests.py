# This script demonstrates how to list on-demand tests already submitted on a sensor.
# It shows how to:
#  - Query active test metadata, which requires both a sensor and a test type
#  - Handle this endpoint's zero-based paging and `items` array
#  - Narrow the output to tests still in progress
#
# Use this when a submitted test appears to be doing nothing: on-demand tests do not
# start while automated testing is running on the sensor. See
# examples/eyes/automated_testing.py to check that.

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

VALID_TEST_TYPES = [
    "PING", "HTTP_DOWNLOAD", "HTTP_UPLOAD", "IPERF3", "SPEEDTEST", "TRACEROUTE",
    "MOS", "UDP_DOWNLOAD", "UDP_UPLOAD", "TCP_DOWNLOAD", "TCP_UPLOAD", "WEB_DOWNLOAD",
]

VALID_BANDS = ["2.4", "5", "6", "all"]

# This endpoint pages from 0 and uses `size`, unlike most 7SIGNAL endpoints which
# page from 1 and use `perPage`.
DEFAULT_PAGE = 0
DEFAULT_SIZE = 20


def list_active_tests(token, sensor_id, test_type, channel=None, ap_id=None, band=None,
                      start=None, end=None, page=DEFAULT_PAGE, size=DEFAULT_SIZE):
    # Fetches on-demand test metadata for a sensor. Both sensor_id and test_type are
    # required by the API; there is no "all sensors" or "all types" query.
    if test_type not in VALID_TEST_TYPES:
        logging.error(f"Unsupported test type: {test_type}")
        logging.error(f"Valid values are: {', '.join(VALID_TEST_TYPES)}")
        return None

    if band is not None and band not in VALID_BANDS:
        logging.error(f"Unsupported band: {band}")
        logging.error(f"Valid values are: {', '.join(VALID_BANDS)}")
        return None

    url = f"https://{API_HOST}/on-demand-tests/sensors/active-tests"
    headers = {"Authorization": f"Bearer {token}"}

    params = {
        "sensorId": sensor_id,
        "testType": test_type,
        "page": page,
        "size": size,
    }
    if channel is not None:
        params["channel"] = channel
    if ap_id is not None:
        params["apId"] = ap_id
    if band is not None:
        params["band"] = band
    if start is not None:
        params["start"] = start
    if end is not None:
        params["end"] = end

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def display_active_tests(data, in_progress_only=False):
    # Logs a readable summary of the test metadata. The results array is named `items`
    # on this endpoint rather than `results`.
    items = data.get("items", [])
    pagination = data.get("pagination", {})
    returned_count = len(items)

    if in_progress_only:
        items = [i for i in items if i.get("runStatus") == "IN_PROGRESS"]

    logging.info("===== On-Demand Test Metadata =====")

    if not items:
        # Distinguish "the sensor has no recent tests" from "none of them are running"
        if in_progress_only and returned_count:
            logging.info(f"No active tests in progress. {returned_count} recent test(s) "
                         "were returned but all have finished.")
        else:
            logging.info("No active tests found for this sensor and test type.")
        return

    if pagination:
        # page is 0-based here, so report it as-is rather than adding one
        logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                     f"({pagination.get('total', '?')} total, 0-based paging)")
    logging.info("-----")

    for item in items:
        logging.info(f"  Test id     : {item.get('testId', 'N/A')}")
        logging.info(f"  Type        : {item.get('testType', 'N/A')}")
        logging.info(f"  Run status  : {item.get('runStatus', 'N/A')}")

        if item.get("sensorName"):
            logging.info(f"  Sensor      : {item.get('sensorName')} ({item.get('sensorId', 'N/A')})")
        if item.get("apId") is not None:
            logging.info(f"  Access point: {item.get('apId')}")
        # "N/A" is a real value in the band enum, so don't render it as a frequency
        if item.get("band") and item.get("band") != "N/A":
            logging.info(f"  Band        : {item.get('band')} GHz")
        if item.get("channel") is not None:
            logging.info(f"  Channel     : {item.get('channel')}")
        if item.get("createdAt"):
            logging.info(f"  Created     : {item.get('createdAt')}")

        # errorCode of 0 means no error, so only report a genuine failure
        if item.get("errorCode"):
            logging.info(f"  Error       : {item.get('errorCode')} "
                         f"{item.get('errorMessage') or ''}".rstrip())

        logging.info("-----")


def main():
    # Ask for the sensor and test type, both of which the API requires
    sensor_input = input("Enter the SENSOR ID: ").strip()
    if not sensor_input:
        logging.error("Sensor id cannot be empty.")
        sys.exit(1)

    try:
        sensor_id = int(sensor_input)
    except ValueError:
        logging.error("Sensor id must be a number.")
        sys.exit(1)

    logging.info(f"Available test types: {', '.join(VALID_TEST_TYPES)}")
    test_type = input("Enter the TEST TYPE: ").strip().upper()
    if test_type not in VALID_TEST_TYPES:
        logging.error(f"Test type must be one of: {', '.join(VALID_TEST_TYPES)}")
        sys.exit(1)

    only_running = input("Show only tests still in progress? (yes/no): ").strip().lower() == "yes"

    # Optionally bound the query by time
    now_ms = int(time.time() * 1000)
    default_start_ms = now_ms - (24 * 60 * 60 * 1000)

    start_input = input(f"Enter the START time in epoch ms (press Enter for {default_start_ms}): ").strip()

    try:
        start_ms = int(start_input) if start_input else default_start_ms
    except ValueError:
        logging.error("Start time must be a whole number of milliseconds.")
        sys.exit(1)

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Fetch and display the test metadata
    data = list_active_tests(token, sensor_id, test_type, start=start_ms, end=now_ms)
    if data:
        display_active_tests(data, in_progress_only=only_running)


if __name__ == "__main__":
    main()
