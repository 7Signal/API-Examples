# This script demonstrates how to retrieve time-series and location impact data from 7SIGNAL.
# It shows how to:
#  - Fetch agent impact over time from the /impact/agents/time-series endpoint
#  - Control time-series granularity (HOUR, DAY, or MONTH)
#  - Fetch per-location impact metrics from the /impact/locations endpoint

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

# Valid granularity options for the time-series endpoint
VALID_GRANULARITIES = {"HOUR", "DAY", "MONTH"}


def fetch_impact_time_series(token, from_time, to_time, granularity):
    # Fetches agent impact metrics bucketed by the given granularity (HOUR, DAY, or MONTH).
    url = f"https://{API_HOST}/impact/agents/time-series"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "from": from_time,
        "to": to_time,
        "granularity": granularity,
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        log_time_series(data, granularity)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")


def fetch_impact_locations(token, from_time, to_time):
    # Fetches per-location impact metrics within the time range.
    url = f"https://{API_HOST}/impact/locations"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"from": from_time, "to": to_time}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        log_impact_locations(data)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")


def log_time_series(data, granularity):
    # Logs time-series impact data bucketed by granularity
    logging.info(f"===== Agent Impact Time Series ({granularity}) =====")
    results = data.get("results", [])
    pagination = data.get("pagination", {})

    if not results:
        logging.info("No time-series impact data available for the selected time range.")
        return

    logging.info(f"Showing {len(results)} buckets (page {pagination.get('page', '?')} of {pagination.get('pages', '?')}):")
    logging.info("-----")
    for bucket in results:
        # Timestamp is in epoch milliseconds; display as-is for portability
        logging.info(f"  Timestamp              : {bucket.get('timestamp', 'N/A')}")
        logging.info(f"    Devices              : {bucket.get('deviceCount', 'N/A')}")
        logging.info(f"    Minutes Monitored    : {bucket.get('minutesMonitored', 'N/A')}")
        logging.info(f"    Impacted (Experience): {bucket.get('minutesImpactedExperienceScore', 'N/A')} min")
        logging.info(f"    Impacted (Coverage)  : {bucket.get('minutesImpactedCoverage', 'N/A')} min")
        logging.info(f"    Impacted (Congestion): {bucket.get('minutesImpactedCongestion', 'N/A')} min")
        logging.info(f"    Impacted (Roaming)   : {bucket.get('minutesImpactedRoaming', 'N/A')} min")
        logging.info("-----")


def log_impact_locations(data):
    # Logs per-location impact details
    logging.info("===== Per-Location Impact =====")
    results = data.get("results", [])
    pagination = data.get("pagination", {})

    if not results:
        logging.info("No location impact data available for the selected time range.")
        return

    logging.info(f"Showing {len(results)} of {pagination.get('total', '?')} locations:")
    logging.info("-----")
    for loc in results:
        logging.info(f"  Location: {loc.get('locationName', 'Unknown')} ({loc.get('locationId', 'N/A')})")
        logging.info(f"    Devices               : {loc.get('deviceCount', 'N/A')}")
        logging.info(f"    Minutes Monitored     : {loc.get('minutesMonitored', 'N/A')}")
        logging.info(f"    Impacted (Experience) : {loc.get('minutesImpactedExperienceScore', 'N/A')} min")
        logging.info(f"    Impacted (Connectivity): {loc.get('minutesImpactedConnectivity', 'N/A')} min")
        logging.info(f"    Impacted (Coverage)   : {loc.get('minutesImpactedCoverage', 'N/A')} min")
        logging.info(f"    Impacted (Congestion) : {loc.get('minutesImpactedCongestion', 'N/A')} min")
        logging.info(f"    Impacted (Interference): {loc.get('minutesImpactedInterference', 'N/A')} min")
        logging.info(f"    Impacted (Roaming)    : {loc.get('minutesImpactedRoaming', 'N/A')} min")
        logging.info("-----")


def main():
    # Ask user for the time range in epoch milliseconds
    from_input = input("Enter the FROM time (epoch milliseconds): ").strip()
    if not from_input:
        logging.error("from_time cannot be empty.")
        sys.exit(1)

    to_input = input("Enter the TO time (epoch milliseconds): ").strip()
    if not to_input:
        logging.error("to_time cannot be empty.")
        sys.exit(1)

    try:
        from_time = int(from_input)
        to_time = int(to_input)
    except ValueError:
        logging.error("from_time and to_time must be valid integers (epoch milliseconds).")
        sys.exit(1)

    # Ask user for granularity (defaults to HOUR)
    granularity_input = input("Enter granularity (HOUR, DAY, MONTH) [default: HOUR]: ").strip().upper()
    granularity = granularity_input if granularity_input in VALID_GRANULARITIES else "HOUR"
    if granularity_input and granularity_input not in VALID_GRANULARITIES:
        logging.warning(f"Invalid granularity '{granularity_input}', defaulting to HOUR.")

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Fetch agent impact time series
    fetch_impact_time_series(token, from_time, to_time, granularity)

    # Step 3: Fetch per-location impact
    fetch_impact_locations(token, from_time, to_time)


if __name__ == "__main__":
    main()
