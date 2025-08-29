# This script demonstrates how to make an authenticated API call to fetch KPI data for sensors by organization.
# It shows how to:
#  - Retrieve KPI data from the /kpis/sensors/organizations endpoint
#  - Log key KPI summary details instead of raw JSON

import os
import requests
import sys
import logging

# Make sure we can import get_token
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define API Host and KPI Code from environment
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")
KPI_CODE = os.getenv("KPI_CODE")

# Check that required environment variable is set
if not KPI_CODE:
    raise EnvironmentError("KPI_CODE environment variable not set")

# Construct the API URL for fetching sensor KPI data by organization
kpi_url = f"https://{API_HOST}/kpis/sensors/organizations"


def fetch_sensor_kpis_by_org(token):
    # This function fetches KPI data for sensors by organization using the token
    headers = { 
        "Authorization": f"Bearer {token}"
    }
    params = {
        "kpiCodes": KPI_CODE
    }

    try:
        # Send the GET request to the KPI endpoint
        response = requests.get(kpi_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Calls the helper function to log KPI summary details
        log_kpi_summary(data)

    # Log HTTP error details and response body for troubleshooting
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    # Log any other unexpected exceptions
    except Exception as err:
        logging.error(f"Unexpected error: {err}")


def log_kpi_summary(data):
    # Logs a readable KPI summary instead of raw JSON
    logging.info("===== KPI Summary (Sensors by Organization) =====")

    # Log time range details
    rng = data.get("range", {})
    logging.info("Time Range:")
    logging.info(f"  From : {rng.get('fromAsDateString')}")
    logging.info(f"  To   : {rng.get('toAsDateString')}")
    logging.info(f"  Duration: {rng.get('durationAsString')} (Total: {rng.get('total')})")

    # Log KPI results
    for result in data.get("results", []):
        logging.info("-----")
        logging.info(f"KPI: {result.get('name')} ({result.get('kpiCode')})")
        logging.info(f"Description: {result.get('description')}")

        for m in result.get("measurements24GHz", []):
            logging.info("  Measurement @ 2.4GHz:")
            logging.info(f"    Status: {m.get('status')}")
            logging.info(f"    KPI Value: {m.get('kpiValue')}")
            logging.info(f"    SLA Value: {m.get('slaValue')}")
            logging.info(f"    Target Value: {m.get('targetValue')}")
            logging.info(f"    Samples: {m.get('samples')}")
            logging.info(f"    Created At: {m.get('created_at')}")
            logging.info(f"    Worst KPI: {m.get('worstKpiName')} ({m.get('worstKpiCode')})")
            logging.info(f"    Worst KPI Description: {m.get('worstKpiDescription')}")

            sla_params = m.get("slaParameters", {})
            logging.info("    SLA Parameters:")
            logging.info(f"      Comparator: {sla_params.get('comparator')} ({sla_params.get('comparatorOperator')})")
            logging.info(f"      Target Editable: {sla_params.get('targetEditable')}")
            thresholds = sla_params.get("thresholdMap", {})
            logging.info(f"      Thresholds: GREEN={thresholds.get('GREEN')}, YELLOW={thresholds.get('YELLOW')}, RED={thresholds.get('RED')}")


def main():
    # Fetches the token from the auth_utils.py file
    token, _ = get_token()
    # Calls the API using that token
    fetch_sensor_kpis_by_org(token)


if __name__ == "__main__":
    main()
