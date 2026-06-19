# This script demonstrates how to retrieve RF scan data collected by a 7SIGNAL sensor.
# It shows how to:
#  - Fetch paginated scan records from the /scans/sensors endpoint
#  - Display detected access points with signal strength and noise floor for each scan

import os
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


def fetch_sensor_scans(token, sensor_id, start_time, end_time):
    # Fetches RF scan records captured by the specified sensor within the time range.
    url = f"https://{API_HOST}/scans/sensors"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "sensorId": sensor_id,
        "start": start_time,
        "end": end_time,
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        log_sensor_scans(data)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")


def log_sensor_scans(data):
    # Logs sensor scan records with detected AP details including noise floor
    pagination = data.get("pagination", {})
    scans = data.get("scans", [])

    logging.info("===== Sensor RF Scan Data =====")

    if not scans:
        logging.info("No scan data available for the selected time range.")
        return

    logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                 f"({pagination.get('total', '?')} total scan timestamps, {pagination.get('perPage', '?')} per page)")
    logging.info("-----")

    for scan in scans:
        timestamp = scan.get("timestamp", "N/A")
        detected_aps = scan.get("data", [])

        logging.info(f"  Timestamp    : {timestamp}")
        logging.info(f"  Detected APs : {len(detected_aps)}")

        # Sort detected APs by signal strength (strongest first) and show top 5
        sorted_aps = sorted(detected_aps, key=lambda ap: ap.get("signalStrength", -999), reverse=True)
        for ap in sorted_aps[:5]:
            ssid = ap.get("ssid") or "(hidden)"
            bssid = ap.get("bssid", "N/A")
            signal = ap.get("signalStrength", "N/A")
            noise = ap.get("noise", "N/A")
            channel = ap.get("channel", "N/A")
            band = ap.get("band", "N/A")
            stations = ap.get("stationCount", "N/A")
            logging.info(f"    [{signal:>4} dBm / noise {noise:>4} dBm] {ssid} ({bssid}) "
                         f"Ch {channel} @ {band} GHz  Stations: {stations}")

        if len(detected_aps) > 5:
            logging.info(f"    ... and {len(detected_aps) - 5} more")
        logging.info("-----")


def main():
    # Ask user for the sensor ID
    sensor_input = input("Enter the SENSOR ID: ").strip()
    if not sensor_input:
        logging.error("sensor_id cannot be empty.")
        sys.exit(1)

    try:
        sensor_id = int(sensor_input)
    except ValueError:
        logging.error("sensor_id must be a valid integer.")
        sys.exit(1)

    # Ask user for the time range in epoch milliseconds
    start_input = input("Enter the START time (epoch milliseconds): ").strip()
    if not start_input:
        logging.error("start_time cannot be empty.")
        sys.exit(1)

    end_input = input("Enter the END time (epoch milliseconds): ").strip()
    if not end_input:
        logging.error("end_time cannot be empty.")
        sys.exit(1)

    try:
        start_time = int(start_input)
        end_time = int(end_input)
    except ValueError:
        logging.error("start_time and end_time must be valid integers (epoch milliseconds).")
        sys.exit(1)

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Fetch and display sensor scan data
    fetch_sensor_scans(token, sensor_id, start_time, end_time)


if __name__ == "__main__":
    main()
