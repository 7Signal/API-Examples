# This script demonstrates how to retrieve agent impact metrics from 7SIGNAL.
# It shows how to:
#  - Fetch an overall impact summary from the /impact/agents/summary endpoint
#  - Fetch per-agent impact details from the /impact/agents endpoint
#  - Fetch an impact breakdown by status from the /impact/agents/by-status endpoint

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


def fetch_impact_summary(token, from_time, to_time):
    # Fetches an aggregate impact summary for all agents within the time range.
    url = f"https://{API_HOST}/impact/agents/summary"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"from": from_time, "to": to_time}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        log_impact_summary(data)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")


def fetch_impact_agents(token, from_time, to_time):
    # Fetches per-agent impact metrics within the time range.
    url = f"https://{API_HOST}/impact/agents"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"from": from_time, "to": to_time}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        log_impact_agents(data)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")


def fetch_impact_by_status(token, from_time, to_time):
    # Fetches agent impact metrics grouped by impacted-minutes status buckets.
    url = f"https://{API_HOST}/impact/agents/by-status"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"from": from_time, "to": to_time}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        log_impact_by_status(data)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")


def log_impact_summary(data):
    # Logs a readable impact summary instead of raw JSON
    logging.info("===== Agent Impact Summary =====")
    results = data.get("results", [])
    if not results:
        logging.info("No impact summary data available for the selected time range.")
        return
    for summary in results:
        logging.info(f"  Devices Monitored      : {summary.get('deviceCount', 'N/A')}")
        logging.info(f"  Minutes Monitored      : {summary.get('minutesMonitored', 'N/A')}")
        logging.info(f"  Impacted (Experience)  : {summary.get('minutesImpactedExperienceScore', 'N/A')} min")
        logging.info(f"  Impacted (Connectivity): {summary.get('minutesImpactedConnectivity', 'N/A')} min")
        logging.info(f"  Impacted (Coverage)    : {summary.get('minutesImpactedCoverage', 'N/A')} min")
        logging.info(f"  Impacted (Congestion)  : {summary.get('minutesImpactedCongestion', 'N/A')} min")
        logging.info(f"  Impacted (Interference): {summary.get('minutesImpactedInterference', 'N/A')} min")
        logging.info(f"  Impacted (Roaming)     : {summary.get('minutesImpactedRoaming', 'N/A')} min")


def log_impact_agents(data):
    # Logs per-agent impact details
    logging.info("===== Per-Agent Impact Details =====")
    results = data.get("results", [])
    pagination = data.get("pagination", {})

    if not results:
        logging.info("No per-agent impact data available for the selected time range.")
        return

    logging.info(f"Showing {len(results)} of {pagination.get('total', '?')} agents (page {pagination.get('page', '?')} of {pagination.get('pages', '?')}):")
    logging.info("-----")
    for agent in results:
        logging.info(f"  Agent: {agent.get('deviceName', 'Unknown')} ({agent.get('deviceId', 'N/A')})")
        logging.info(f"    Minutes Monitored      : {agent.get('minutesMonitored', 'N/A')}")
        logging.info(f"    Impacted (Experience)  : {agent.get('minutesImpactedExperienceScore', 'N/A')} min")
        logging.info(f"    Impacted (Connectivity): {agent.get('minutesImpactedConnectivity', 'N/A')} min")
        logging.info(f"    Impacted (Coverage)    : {agent.get('minutesImpactedCoverage', 'N/A')} min")
        logging.info(f"    Impacted (Congestion)  : {agent.get('minutesImpactedCongestion', 'N/A')} min")
        logging.info(f"    Impacted (Interference): {agent.get('minutesImpactedInterference', 'N/A')} min")
        logging.info(f"    Impacted (Roaming)     : {agent.get('minutesImpactedRoaming', 'N/A')} min")
        logging.info("-----")


def log_impact_by_status(data):
    # Logs impact data grouped by impacted-minutes status
    logging.info("===== Agent Impact by Status =====")
    results = data.get("results", [])
    if not results:
        logging.info("No impact-by-status data available for the selected time range.")
        return
    for entry in results:
        logging.info(f"  Status Bucket:")
        logging.info(f"    Devices         : {entry.get('deviceCount', 'N/A')}")
        logging.info(f"    Minutes Monitored: {entry.get('minutesMonitored', 'N/A')}")
        logging.info(f"    Impacted (Experience)  : {entry.get('minutesImpactedExperienceScore', 'N/A')} min")
        logging.info(f"    Impacted (Connectivity): {entry.get('minutesImpactedConnectivity', 'N/A')} min")
        logging.info(f"    Impacted (Coverage)    : {entry.get('minutesImpactedCoverage', 'N/A')} min")
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

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Fetch the overall impact summary
    fetch_impact_summary(token, from_time, to_time)

    # Step 3: Fetch per-agent impact details
    fetch_impact_agents(token, from_time, to_time)

    # Step 4: Fetch impact grouped by status
    fetch_impact_by_status(token, from_time, to_time)


if __name__ == "__main__":
    main()
