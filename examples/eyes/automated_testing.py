# This script demonstrates how to check and control automated testing on a 7SIGNAL sensor.
# It shows how to:
#  - Read a sensor's current automated testing state
#  - Start or stop automated testing, with a confirmation prompt first
#  - Confirm the sensor actually reached the state that was requested
#
# Stopping automated testing halts the scheduled measurements that KPIs, SLAs, and
# alerting are calculated from, and gaps will appear in the data until it is started
# again. The change is therefore confirmation-gated.

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

START_ACTION = "START_AUTOMATED_TESTING"
STOP_ACTION = "STOP_AUTOMATED_TESTING"
VALID_ACTIONS = [START_ACTION, STOP_ACTION]

# STOPPING is transient: a stop was requested but the sensor has not finished yet.
TRANSIENT_STATUS = "STOPPING"


def get_automated_testing_status(token, sensor_id):
    # Fetches the sensor's automated testing state. Returns None when the sensor is
    # not found.
    url = f"https://{API_HOST}/eyes/sensors/{sensor_id}/automated-testing"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            logging.info(f"No sensor found with id {sensor_id}.")
            return None

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def confirm_action(message):
    # Asks the user to type 'yes' before a change is sent to the API.
    choice = input(f"{message} Type 'yes' to confirm: ").strip().lower()
    return choice == "yes"


def set_automated_testing(token, sensor_id, action):
    # Starts or stops automated testing on the sensor, after confirming.
    if action not in VALID_ACTIONS:
        logging.error(f"Unsupported action: {action}")
        logging.error(f"Valid values are: {', '.join(VALID_ACTIONS)}")
        return None

    if action == STOP_ACTION:
        logging.info("Stopping automated testing halts the scheduled measurements that "
                     "KPIs, SLAs, and alerting are built from.")
        logging.info("Data gaps will appear for as long as it stays stopped.")

    if not confirm_action(f"Send {action} to sensor {sensor_id}?"):
        logging.info("Aborted; automated testing was not changed.")
        return None

    url = f"https://{API_HOST}/eyes/sensors/{sensor_id}/automated-testing"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json={"action": action})

        if response.status_code == 404:
            logging.info(f"No sensor found with id {sensor_id}.")
            return None

        response.raise_for_status()
        result = response.json()

        # `result` reports that the request was accepted, not that the sensor has
        # finished transitioning
        logging.info(f"{action} accepted with result: {result.get('result', 'N/A')}")
        logging.info("Check the status to confirm the sensor reached the new state.")
        return result
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def display_automated_testing_status(status):
    # Logs the sensor's automated testing state.
    logging.info("===== Automated Testing Status =====")

    if not status:
        logging.info("No automated testing status was returned.")
        return

    test_status = status.get("testStatus", "N/A")

    logging.info(f"  Sensor        : {status.get('eyeName') or '(unknown)'}")
    logging.info(f"  Test profile  : {status.get('testProfileName') or '(none)'}")
    logging.info(f"  Status        : {test_status}")

    if status.get("currentTestRunning"):
        logging.info(f"  Running now   : {status.get('currentTestRunning')}")
    if status.get("currentAccessPoint"):
        logging.info(f"  Access point  : {status.get('currentAccessPoint')}")
    if status.get("currentTestStatus"):
        logging.info(f"  Progress      : {status.get('currentTestStatus')}")

    if test_status == "RUNNING":
        logging.info("  Note: on-demand tests will not start while automated testing "
                     "is running on this sensor.")
    elif test_status == TRANSIENT_STATUS:
        logging.info("  Note: STOPPING is transient - the sensor is still winding down. "
                     "Poll again until it reports STOPPED.")


def main():
    # Ask for the sensor to inspect
    sensor_id = input("Enter the SENSOR ID: ").strip()
    if not sensor_id:
        logging.error("Sensor id cannot be empty.")
        sys.exit(1)

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Show the current state
    status = get_automated_testing_status(token, sensor_id)
    if status is None:
        sys.exit(1)

    display_automated_testing_status(status)

    # Step 3: Offer to change it
    logging.info("What would you like to do?")
    logging.info("  1) Start automated testing")
    logging.info("  2) Stop automated testing")
    logging.info("  3) Exit without changing anything")

    choice = input("Enter a number (1-3): ").strip()

    if choice == "1":
        action = START_ACTION
    elif choice == "2":
        action = STOP_ACTION
    else:
        logging.info("Nothing to do.")
        return

    if set_automated_testing(token, sensor_id, action) is None:
        return

    # Step 4: Confirm the sensor actually reached the requested state
    logging.info("Waiting a moment before re-checking the status...")
    time.sleep(5)

    display_automated_testing_status(get_automated_testing_status(token, sensor_id))


if __name__ == "__main__":
    main()
