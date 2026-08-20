# This script demonstrates how to retrieve platform-detected agent incidents.
# It shows how to:
#  - List agent incidents for a time window, optionally filtered by location
#  - Fetch a single incident by its id
#  - Read threshold values from either response shape
#
# Agent incidents are detected by the platform when a share of the agent population
# at a location, network, and band falls below service thresholds together. They are
# not configured by you. For incidents raised by your own alert rules, see
# examples/alerting/alert_incidents.py instead.

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

# The API rejects a window wider than this
MAX_WINDOW_DAYS = 30
MAX_WINDOW_MS = MAX_WINDOW_DAYS * 24 * 60 * 60 * 1000


def list_incidents(token, from_ms=None, to_ms=None, location_id=None, order=None):
    # Fetches agent incidents overlapping the given window. When from/to are omitted
    # the API defaults to the last 24 hours.
    if from_ms is not None and to_ms is not None and (to_ms - from_ms) > MAX_WINDOW_MS:
        logging.error(f"The time window cannot be wider than {MAX_WINDOW_DAYS} days.")
        logging.error("Request a shorter window, or page through it in chunks.")
        return None

    url = f"https://{API_HOST}/incidents/agents"
    headers = {"Authorization": f"Bearer {token}"}

    params = {}
    if from_ms is not None:
        params["from"] = from_ms
    if to_ms is not None:
        params["to"] = to_ms
    # This endpoint uses snake_case for the location filter, unlike most others.
    # An unrecognised parameter name is ignored rather than rejected, so a typo
    # here returns unfiltered results with no error.
    if location_id:
        params["location_id"] = location_id
    if order:
        params["order"] = order

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


def get_incident(token, incident_id):
    # Fetches a single agent incident. Returns None when it does not exist.
    url = f"https://{API_HOST}/incidents/agents/{incident_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            logging.info(f"No agent incident found with id {incident_id}.")
            return None

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def get_threshold(incident, name):
    # Reads a threshold value from an incident. The list endpoint nests these under
    # a "thresholds" object while the single-incident endpoint returns them flat, so
    # this handles either shape.
    thresholds = incident.get("thresholds")
    if thresholds is not None:
        return thresholds.get(name)

    return incident.get(name)


def display_incidents(data):
    # Logs a readable summary of agent incidents.
    incidents = data.get("results", [])
    window = data.get("range", {})

    logging.info("===== Agent Incidents =====")

    if not incidents:
        logging.info("No agent incidents found for this window.")
        return

    if window:
        logging.info(f"Window: {window.get('durationAsString', 'N/A')} "
                     f"({window.get('total', '?')} incidents)")
    logging.info("-----")

    for incident in incidents:
        impacted = incident.get("countImpacted")
        population = incident.get("populationCount")

        logging.info(f"  Id           : {incident.get('id', 'N/A')}")
        logging.info(f"  Type         : {incident.get('type', 'N/A')}")
        logging.info(f"  Location     : {incident.get('locationName') or incident.get('location') or 'N/A'}")
        logging.info(f"  Network      : {incident.get('network', 'N/A')}")

        if incident.get("band") is not None:
            logging.info(f"  Band         : {incident.get('band')} GHz")

        # Impact only means something as a share of the measured population
        if impacted is not None and population:
            share = (impacted / population) * 100
            logging.info(f"  Impacted     : {impacted} of {population} agents ({share:.1f}%)")
        elif impacted is not None:
            logging.info(f"  Impacted     : {impacted} agents")

        logging.info(f"  Started      : {incident.get('startTimestamp', 'N/A')}")

        if incident.get("timestampDeterminedToBeIncident"):
            logging.info(f"  Qualified    : {incident.get('timestampDeterminedToBeIncident')}")

        # The API defines no active/resolved flag for agent incidents and does not
        # declare endTimestamp nullable, so an absent value is reported as absent
        # rather than being interpreted as "still running".
        if incident.get("endTimestamp"):
            logging.info(f"  Ended        : {incident.get('endTimestamp')}")
        else:
            logging.info("  Ended        : not reported")

        critical = get_threshold(incident, "criticalThreshold")
        warning = get_threshold(incident, "warningThreshold")
        if critical is not None or warning is not None:
            logging.info(f"  Thresholds   : warning {warning}, critical {critical}")

        logging.info("-----")


def main():
    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    logging.info("What would you like to do?")
    logging.info("  1) List agent incidents from the last 24 hours")
    logging.info("  2) List agent incidents for a location")
    logging.info("  3) List agent incidents for a custom time window")
    logging.info("  4) Fetch a single agent incident")
    logging.info("  5) Exit")

    choice = input("Enter a number (1-5): ").strip()

    if choice == "1":
        # Omitting from/to lets the API apply its 24 hour default
        incidents = list_incidents(token)
        if incidents:
            display_incidents(incidents)

    elif choice == "2":
        location_id = input("Enter the LOCATION ID (UUID): ").strip()
        if not location_id:
            logging.error("location_id cannot be empty.")
            sys.exit(1)

        incidents = list_incidents(token, location_id=location_id)
        if incidents:
            display_incidents(incidents)

    elif choice == "3":
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

        incidents = list_incidents(token, from_ms=from_ms, to_ms=to_ms)
        if incidents:
            display_incidents(incidents)

    elif choice == "4":
        incident_id = input("Enter the INCIDENT ID (UUID): ").strip()
        if not incident_id:
            logging.error("Incident id cannot be empty.")
            sys.exit(1)

        incident = get_incident(token, incident_id)
        if incident:
            display_incidents({"results": [incident]})

    else:
        logging.info("Nothing to do.")


if __name__ == "__main__":
    main()
