# This script demonstrates how to search the 7SIGNAL agent audit trail.
# It shows how to:
#  - Page through audit records with actor, action, source, and initiated filters
#  - Build the ISO-8601 time range this endpoint expects
#  - Read the free-form details object defensively
#
# Note this endpoint takes ISO-8601 date-time strings for its time range, unlike most
# 7SIGNAL endpoints which take epoch milliseconds. The iso_utc() helper below converts.

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

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def iso_utc(epoch_ms):
    # Converts epoch milliseconds to the ISO-8601 UTC string this endpoint expects.
    seconds = int(epoch_ms) / 1000
    return time.strftime(ISO_FORMAT, time.gmtime(seconds))


def list_audit_records(token, start_time=None, end_time=None, actor=None, action=None,
                       source=None, initiated=None, page=1, per_page=10,
                       sort_field=None, order=None):
    # Fetches a page of agent audit records. start_time and end_time must be ISO-8601
    # strings; use iso_utc() to convert from epoch milliseconds.
    for label, value in (("start_time", start_time), ("end_time", end_time)):
        if value is not None and not isinstance(value, str):
            logging.error(f"{label} must be an ISO-8601 string such as "
                          "'2026-08-01T00:00:00Z', not epoch milliseconds.")
            logging.error("Use iso_utc(epoch_ms) to convert.")
            return None

    url = f"https://{API_HOST}/audit/agents"
    headers = {"Authorization": f"Bearer {token}"}

    params = {"page": page, "perPage": per_page}
    if start_time:
        params["startTimeRange"] = start_time
    if end_time:
        params["endTimeRange"] = end_time
    # These filters are exact-match and case-sensitive
    if actor:
        params["actor"] = actor
    if action:
        params["action"] = action
    if source:
        params["source"] = source
    if initiated:
        params["initiated"] = initiated
    if sort_field:
        params["sortField"] = sort_field
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


def display_audit_records(data):
    # Logs a readable summary of the audit records.
    records = data.get("results", [])
    pagination = data.get("pagination", {})

    logging.info("===== Agent Audit Records =====")

    if not records:
        logging.info("No audit records found.")
        return

    if pagination:
        logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                     f"({pagination.get('total', '?')} total)")
    logging.info("-----")

    for record in records:
        logging.info(f"  When      : {record.get('timestamp', 'N/A')}")
        logging.info(f"  Action    : {record.get('action', 'N/A')}")
        logging.info(f"  Actor     : {record.get('actor') or '(not recorded)'}")

        if record.get("source"):
            logging.info(f"  Source    : {record.get('source')}")
        if record.get("initiated"):
            logging.info(f"  Initiated : {record.get('initiated')}")
        if record.get("organizationName"):
            logging.info(f"  Org       : {record.get('organizationName')}")

        # details is free-form and varies by action and source, so never assume a key
        details = record.get("details") or {}
        if details:
            logging.info("  Details   :")
            for key, value in details.items():
                logging.info(f"    {key}: {value}")

        logging.info("-----")


def summarize_actions(records):
    # Collects the distinct action values seen, which is the practical way to discover
    # what the exact-match `action` filter will accept.
    return sorted({r.get("action") for r in records if r.get("action")})


def main():
    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    logging.info("What would you like to do?")
    logging.info("  1) List the last 7 days of audit records")
    logging.info("  2) Filter by actor")
    logging.info("  3) Filter by action")
    logging.info("  4) Show the distinct actions on the first page of the last 7 days")
    logging.info("  5) Exit")

    choice = input("Enter a number (1-5): ").strip()

    # The last 7 days, converted to the ISO-8601 strings this endpoint wants
    now_ms = int(time.time() * 1000)
    week_ago_ms = now_ms - (7 * 24 * 60 * 60 * 1000)
    start_time = iso_utc(week_ago_ms)
    end_time = iso_utc(now_ms)

    if choice == "1":
        records = list_audit_records(token, start_time=start_time, end_time=end_time)
        if records:
            display_audit_records(records)

    elif choice == "2":
        actor = input("Enter the ACTOR (exact match): ").strip()
        if not actor:
            logging.error("Actor cannot be empty.")
            sys.exit(1)

        records = list_audit_records(
            token, start_time=start_time, end_time=end_time, actor=actor
        )
        if records:
            display_audit_records(records)

    elif choice == "3":
        action = input("Enter the ACTION (exact match, case sensitive): ").strip()
        if not action:
            logging.error("Action cannot be empty.")
            sys.exit(1)

        records = list_audit_records(
            token, start_time=start_time, end_time=end_time, action=action
        )
        if records:
            display_audit_records(records)

    elif choice == "4":
        records = list_audit_records(
            token, start_time=start_time, end_time=end_time, per_page=100
        )
        if records:
            actions = summarize_actions(records.get("results", []))

            logging.info("===== Distinct actions seen (first page only) =====")
            if not actions:
                logging.info("No audit records found.")
            for action in actions:
                logging.info(f"  {action}")

    else:
        logging.info("Nothing to do.")


if __name__ == "__main__":
    main()
