# This script demonstrates how to review 7SIGNAL alert incidents.
# It shows how to:
#  - List incidents with status and time-range filters
#  - Read the incidents summary and the per-rule incident counts
#  - Fetch one incident and read the rule snapshot it was raised under
#  - Manually resolve an active incident, with a confirmation prompt first
#
# Incidents are raised by the alert rules in your organization. See
# flow_alert_rules.py in this directory for managing the rules themselves.

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

VALID_STATUSES = ["active", "resolved"]


def list_incidents(token, status=None, metric=None, rule_id=None,
                   started_after=None, started_before=None, page=1, per_page=10):
    # Fetches a page of alert incidents. Optional arguments filter the results.
    url = f"https://{API_HOST}/alerting/incidents"
    headers = {"Authorization": f"Bearer {token}"}

    # The first page is 1 for this endpoint, not 0
    params = {"page": page, "perPage": per_page}
    if status:
        params["status"] = status
    if metric:
        params["metric"] = metric
    if rule_id:
        params["ruleId"] = rule_id
    if started_after is not None:
        params["startedAfter"] = started_after
    if started_before is not None:
        params["startedBefore"] = started_before

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


def get_incidents_summary(token):
    # Fetches total and active incident counts.
    url = f"https://{API_HOST}/alerting/incidents/summary"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def get_incidents_by_rule(token, from_ms=None, to_ms=None):
    # Fetches incident counts grouped by the rule that produced them.
    # This endpoint returns a bare JSON array, not a {results, pagination} object.
    #
    # It accepts only a time window - there is no per-rule filter here. To look at a
    # single rule's incidents, use list_incidents(rule_id=...) instead.
    url = f"https://{API_HOST}/alerting/incidents/by-rule"
    headers = {"Authorization": f"Bearer {token}"}

    params = {}
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


def get_incident(token, incident_id):
    # Fetches a single incident. Returns None when the incident does not exist.
    url = f"https://{API_HOST}/alerting/incidents/{incident_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            logging.info(f"No incident found with id {incident_id}.")
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


def resolve_incident(token, incident_id):
    # Manually resolves an active incident after confirming with the user.
    if not confirm_action(f"Resolve incident {incident_id}?"):
        logging.info("Aborted; the incident was not resolved.")
        return False

    url = f"https://{API_HOST}/alerting/incidents/{incident_id}/resolve"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(url, headers=headers)

        # The API returns 409 when the metric already recovered on its own
        if response.status_code == 409:
            logging.info(f"Incident {incident_id} is already resolved; nothing to do.")
            return False

        if response.status_code == 404:
            logging.info(f"No incident found with id {incident_id}.")
            return False

        response.raise_for_status()
        logging.info(f"Incident {incident_id} resolved.")
        return True
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return False


def display_incidents(data):
    # Logs a readable summary of a page of incidents.
    incidents = data.get("results", [])
    pagination = data.get("pagination", {})

    logging.info("===== Alert Incidents =====")

    if not incidents:
        logging.info("No incidents found.")
        return

    logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                 f"({pagination.get('total', '?')} total)")
    logging.info("-----")

    for incident in incidents:
        # An incident with no resolvedAt is still ongoing
        resolved_at = incident.get("resolvedAt")
        state = "resolved" if resolved_at else "active"

        logging.info(f"  Id           : {incident.get('id', 'N/A')}")
        logging.info(f"  Metric       : {incident.get('metric', 'N/A')}")
        logging.info(f"  State        : {state}")

        if incident.get("dimensionKey"):
            logging.info(f"  Dimension    : {incident.get('dimensionKey')}")
        if incident.get("startedAt"):
            logging.info(f"  Started      : {format_timestamp(incident.get('startedAt'))}")
        if resolved_at:
            logging.info(f"  Resolved     : {format_timestamp(resolved_at)}")
        if incident.get("resolutionReason"):
            logging.info(f"  Reason       : {incident.get('resolutionReason')}")
        if incident.get("triggerValue") is not None:
            logging.info(f"  Trigger value: {incident.get('triggerValue')}")

        # The snapshot records the rule as it was when the incident was raised
        snapshot = incident.get("snapshot") or {}
        aggregation = snapshot.get("aggregationFunction")
        operator = snapshot.get("thresholdOperator")
        threshold = snapshot.get("thresholdValue")
        if aggregation and operator and threshold is not None:
            logging.info(f"  Rule at time : {aggregation} {operator} {threshold}")

        logging.info("-----")


def display_incidents_summary(summary):
    # Logs the aggregate incident counts.
    if not summary:
        return

    logging.info("===== Incidents Summary =====")
    logging.info(f"  Total  : {summary.get('totalCount', 'N/A')}")
    logging.info(f"  Active : {summary.get('activeCount', 'N/A')}")


def display_incidents_by_rule(rows):
    # Logs incident counts grouped by rule, noisiest first.
    if not rows:
        logging.info("No incidents grouped by rule for this window.")
        return

    logging.info("===== Incidents by Rule =====")

    for row in sorted(rows, key=lambda r: r.get("incidentCount", 0), reverse=True):
        rule = row.get("rule") or {}
        operator = rule.get("thresholdOperator", "")
        threshold = rule.get("thresholdValue", "")

        logging.info(f"  Rule id   : {row.get('ruleId', 'N/A')}")
        logging.info(f"  Metric    : {rule.get('metric', 'N/A')} {operator} {threshold}".rstrip())
        logging.info(f"  Incidents : {row.get('incidentCount', 0)} "
                     f"({row.get('activeCount', 0)} still active)")
        logging.info("-----")


def format_timestamp(epoch_ms):
    # Renders an epoch-milliseconds value as a readable UTC timestamp.
    if epoch_ms is None:
        return "N/A"

    try:
        seconds = int(epoch_ms) / 1000
    except (TypeError, ValueError):
        return str(epoch_ms)

    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(seconds))


def main():
    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Show the overall incident picture
    display_incidents_summary(get_incidents_summary(token))

    # Step 3: Offer the review actions
    logging.info("What would you like to do?")
    logging.info("  1) List recent incidents")
    logging.info("  2) List only active incidents")
    logging.info("  3) Show incident counts by rule (last 24 hours)")
    logging.info("  4) Fetch a single incident")
    logging.info("  5) Resolve an active incident")
    logging.info("  6) Exit")

    choice = input("Enter a number (1-6): ").strip()

    if choice == "1":
        incidents = list_incidents(token)
        if incidents:
            display_incidents(incidents)

    elif choice == "2":
        incidents = list_incidents(token, status="active")
        if incidents:
            display_incidents(incidents)

    elif choice == "3":
        now_ms = int(time.time() * 1000)
        yesterday_ms = now_ms - (24 * 60 * 60 * 1000)

        rows = get_incidents_by_rule(token, from_ms=yesterday_ms, to_ms=now_ms)
        if rows is not None:
            display_incidents_by_rule(rows)

    elif choice == "4":
        incident_id = input("Enter the INCIDENT ID: ").strip()
        if not incident_id:
            logging.error("Incident id cannot be empty.")
            sys.exit(1)

        incident = get_incident(token, incident_id)
        if incident:
            display_incidents({"results": [incident]})

    elif choice == "5":
        incident_id = input("Enter the INCIDENT ID to resolve: ").strip()
        if not incident_id:
            logging.error("Incident id cannot be empty.")
            sys.exit(1)

        resolve_incident(token, incident_id)

    else:
        logging.info("Nothing to do.")


if __name__ == "__main__":
    main()
