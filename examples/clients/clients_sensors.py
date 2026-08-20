# This script demonstrates how to retrieve the client devices 7SIGNAL sensors observed.
# It shows how to:
#  - List sensor clients over a time window
#  - Filter by partial MAC address or vendor name
#  - Handle the many fields that are only populated for labelled devices
#
# This endpoint is bounded by its time window rather than paged: it returns a `range`
# object instead of a `pagination` object, and takes no page/perPage parameters.

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

# The API rejects a window wider than this. Note the default window is shorter still:
# omitting from/to returns the previous 30 days, not the full 90.
MAX_WINDOW_DAYS = 90
MAX_WINDOW_MS = MAX_WINDOW_DAYS * 24 * 60 * 60 * 1000


def list_clients(token, from_ms=None, to_ms=None, mac=None, vendor=None):
    # Fetches the clients sensors observed in the window. When from/to are omitted the
    # API defaults to the previous 30 days.
    if from_ms is not None and to_ms is not None and (to_ms - from_ms) > MAX_WINDOW_MS:
        logging.error(f"The time window cannot be wider than {MAX_WINDOW_DAYS} days.")
        logging.error("Split a longer retrospective into shorter chunks.")
        return None

    url = f"https://{API_HOST}/clients/sensors"
    headers = {"Authorization": f"Bearer {token}"}

    params = {}
    if from_ms is not None:
        params["from"] = from_ms
    if to_ms is not None:
        params["to"] = to_ms
    # Both filters are partial and case-insensitive, so an OUI prefix works
    if mac:
        params["mac"] = mac
    if vendor:
        params["vendor"] = vendor

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


def display_clients(data):
    # Logs a readable summary of the observed clients.
    clients = data.get("results", [])
    window = data.get("range", {})

    logging.info("===== Sensor Clients =====")

    if not clients:
        logging.info("No sensor clients found for this window.")
        return

    if window:
        logging.info(f"Window: {window.get('durationAsString', 'N/A')} "
                     f"({window.get('total', '?')} clients)")
    logging.info("-----")

    for client in clients:
        # name, description, and user are only set for devices someone has labelled,
        # so fall back to the MAC address rather than showing an empty value
        label = client.get("name") or client.get("macAddress") or "(unknown)"

        logging.info(f"  Client      : {label}")
        logging.info(f"  MAC address : {client.get('macAddress') or '(unknown)'}")
        logging.info(f"  Vendor      : {client.get('vendor') or '(unknown vendor)'}")

        if client.get("user"):
            logging.info(f"  User        : {client.get('user')}")
        if client.get("description"):
            logging.info(f"  Description : {client.get('description')}")

        logging.info("-----")


def main():
    # Ask for an optional filter so the output stays manageable
    logging.info("Leave a filter blank to skip it.")
    mac = input("Filter by MAC address (partial is fine): ").strip() or None
    vendor = input("Filter by vendor name (partial is fine): ").strip() or None

    # Ask for the time range, defaulting to the last 7 days
    now_ms = int(time.time() * 1000)
    default_from_ms = now_ms - (7 * 24 * 60 * 60 * 1000)

    from_input = input(f"Enter the START time in epoch ms (press Enter for {default_from_ms}): ").strip()
    to_input = input(f"Enter the END time in epoch ms (press Enter for {now_ms}): ").strip()

    try:
        from_ms = int(from_input) if from_input else default_from_ms
        to_ms = int(to_input) if to_input else now_ms
    except ValueError:
        logging.error("Start and end times must be whole numbers of milliseconds.")
        sys.exit(1)

    if from_ms >= to_ms:
        logging.error("The start time must be earlier than the end time.")
        sys.exit(1)

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Fetch and display the observed clients
    clients = list_clients(token, from_ms=from_ms, to_ms=to_ms, mac=mac, vendor=vendor)
    if clients:
        display_clients(clients)


if __name__ == "__main__":
    main()
