# This script demonstrates how to retrieve 7SIGNAL sensor-side change events.
# It shows how to:
#  - List configuration and state changes for a sensor or network element
#  - Respect the API's supported filter combinations
#  - Correlate a change with the time a metric shifted
#
# Change events answer "did something get reconfigured when the numbers moved?" They
# cover sensors (Eyes), access points, networks, and service areas.

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


def validate_filter_combination(sensor_id=None, access_point_id=None,
                                network_id=None, service_area_id=None):
    # The API only accepts certain element filter combinations: Access Point alone,
    # Eye alone, Access Point with Eye, Network alone, or Network with Service Area.
    # Returns an error message, or None when the combination is acceptable.
    has_ap_or_sensor = bool(access_point_id or sensor_id)
    has_network = bool(network_id)

    if service_area_id and not network_id:
        return ("serviceAreaId is only valid together with networkId. "
                "Supply the networkId the service area belongs to.")

    if has_network and has_ap_or_sensor:
        return ("A network filter cannot be combined with an access point or sensor "
                "filter. Supported combinations are: access point; sensor; access point "
                "with sensor; network; or network with service area.")

    return None


def list_change_events(token, sensor_id=None, access_point_id=None, network_id=None,
                       service_area_id=None, from_ms=None, to_ms=None):
    # Fetches change events for the specified element. When from/to are omitted the
    # API defaults to the last 24 hours.
    problem = validate_filter_combination(
        sensor_id=sensor_id,
        access_point_id=access_point_id,
        network_id=network_id,
        service_area_id=service_area_id,
    )
    if problem:
        logging.error(problem)
        return None

    url = f"https://{API_HOST}/change-events/sensors"
    headers = {"Authorization": f"Bearer {token}"}

    params = {}
    if sensor_id is not None:
        params["sensorId"] = sensor_id
    if access_point_id is not None:
        params["accessPointId"] = access_point_id
    if network_id is not None:
        params["networkId"] = network_id
    if service_area_id is not None:
        params["serviceAreaId"] = service_area_id
    if from_ms is not None:
        params["from"] = from_ms
    if to_ms is not None:
        params["to"] = to_ms

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


def format_timestamp(epoch_ms):
    # Renders an epoch-milliseconds value as a readable UTC timestamp.
    if epoch_ms is None:
        return "N/A"

    try:
        seconds = int(epoch_ms) / 1000
    except (TypeError, ValueError):
        return str(epoch_ms)

    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(seconds))


def display_change_events(data):
    # Logs a readable summary of the change events, oldest first.
    events = data.get("results", [])
    pagination = data.get("pagination", {})

    logging.info("===== Sensor Change Events =====")

    if not events:
        logging.info("No change events found for this element and window.")
        return

    if pagination:
        logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                     f"({pagination.get('total', '?')} total)")
    logging.info("-----")

    for event in sorted(events, key=lambda e: e.get("timestamp") or 0):
        logging.info(f"  When    : {format_timestamp(event.get('timestamp'))}")
        logging.info(f"  Event   : {event.get('name', 'N/A')}")

        # element and parentElement are display names, not ids
        if event.get("element"):
            logging.info(f"  Element : {event.get('element')}")
        if event.get("parentElement"):
            logging.info(f"  Parent  : {event.get('parentElement')}")
        if event.get("description"):
            logging.info(f"  Details : {event.get('description')}")

        logging.info("-----")


def main():
    logging.info("Supported filter combinations:")
    logging.info("  1) Sensor (Eye) only")
    logging.info("  2) Access point only")
    logging.info("  3) Access point with sensor")
    logging.info("  4) Network only")
    logging.info("  5) Network with service area")

    choice = input("Enter a number (1-5): ").strip()

    sensor_id = None
    access_point_id = None
    network_id = None
    service_area_id = None

    if choice == "1":
        sensor_id = input("Enter the SENSOR ID: ").strip()
    elif choice == "2":
        access_point_id = input("Enter the ACCESS POINT ID: ").strip()
    elif choice == "3":
        access_point_id = input("Enter the ACCESS POINT ID: ").strip()
        sensor_id = input("Enter the SENSOR ID: ").strip()
    elif choice == "4":
        network_id = input("Enter the NETWORK ID: ").strip()
    elif choice == "5":
        network_id = input("Enter the NETWORK ID: ").strip()
        service_area_id = input("Enter the SERVICE AREA ID: ").strip()
    else:
        logging.error("Please choose a number between 1 and 5.")
        sys.exit(1)

    # Any element id the user was asked for has to be filled in
    if not any([sensor_id, access_point_id, network_id]):
        logging.error("An element id is required for the chosen combination.")
        sys.exit(1)

    # Ask for the time range, defaulting to the last 24 hours
    now_ms = int(time.time() * 1000)
    default_from_ms = now_ms - (24 * 60 * 60 * 1000)

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

    # Step 2: Fetch and display the change events
    events = list_change_events(
        token,
        sensor_id=sensor_id or None,
        access_point_id=access_point_id or None,
        network_id=network_id or None,
        service_area_id=service_area_id or None,
        from_ms=from_ms,
        to_ms=to_ms,
    )
    if events:
        display_change_events(events)


if __name__ == "__main__":
    main()
