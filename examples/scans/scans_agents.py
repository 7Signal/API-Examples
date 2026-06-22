# This script demonstrates how to retrieve RF scan data collected by a 7SIGNAL agent.
# It shows how to:
#  - Fetch paginated scan records from the /scans/agents endpoint
#  - Display detected access points for each scan timestamp, sorted by signal strength

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


def fetch_agent_scans(token, agent_id, start_time, end_time):
    # Fetches RF scan records captured by the specified agent within the time range.
    url = f"https://{API_HOST}/scans/agents"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "agentId": agent_id,
        "start": start_time,
        "end": end_time,
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        log_agent_scans(data)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")


def log_agent_scans(data):
    # Logs agent scan records with detected AP details
    pagination = data.get("pagination", {})
    scans = data.get("scans", [])

    logging.info("===== Agent RF Scan Data =====")

    if not scans:
        logging.info("No scan data available for the selected time range.")
        return

    logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                 f"({pagination.get('total', '?')} total scan timestamps, {pagination.get('perPage', '?')} per page)")
    logging.info("-----")

    for scan in scans:
        timestamp = scan.get("timestamp", "N/A")
        connected_bssid = scan.get("agentConnectedBssid") or "Not connected"
        connected_ssid = scan.get("agentConnectedSsid") or "N/A"
        detected_aps = scan.get("data", [])

        logging.info(f"  Timestamp       : {timestamp}")
        logging.info(f"  Connected BSSID : {connected_bssid}")
        logging.info(f"  Connected SSID  : {connected_ssid}")
        logging.info(f"  Detected APs    : {len(detected_aps)}")

        # Sort detected APs by signal strength (strongest first) and show top 5
        sorted_aps = sorted(detected_aps, key=lambda ap: ap.get("signalStrength", -999), reverse=True)
        for ap in sorted_aps[:5]:
            ssid = ap.get("ssid") or "(hidden)"
            bssid = ap.get("bssid", "N/A")
            signal = ap.get("signalStrength", "N/A")
            channel = ap.get("channel", "N/A")
            band = ap.get("band", "N/A")
            logging.info(f"    [{signal:>4} dBm] {ssid} ({bssid}) Ch {channel} @ {band} GHz")

        if len(detected_aps) > 5:
            logging.info(f"    ... and {len(detected_aps) - 5} more")
        logging.info("-----")


def main():
    # Ask user for the agent UUID
    agent_id = input("Enter the AGENT ID (UUID): ").strip()
    if not agent_id:
        logging.error("agent_id cannot be empty.")
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

    # Step 2: Fetch and display agent scan data
    fetch_agent_scans(token, agent_id, start_time, end_time)


if __name__ == "__main__":
    main()
