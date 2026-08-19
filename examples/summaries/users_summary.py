# This script demonstrates how to read the 7SIGNAL user summary for an organization.
# It shows how to:
#  - Fetch the user counts, optionally for a specific organization
#  - Interpret the overlapping login windows correctly
#
# Note this endpoint takes `organizationId`, not the `organization` parameter used by
# most 7SIGNAL endpoints. An unrecognised parameter is ignored rather than rejected, so
# using the wrong name silently returns the primary organization's numbers instead.

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


def get_user_summary(token, organization_id=None):
    # Fetches the user summary. Omitting organization_id returns the summary for the
    # primary organization associated with the token.
    url = f"https://{API_HOST}/summaries/users"
    headers = {"Authorization": f"Bearer {token}"}

    params = {}
    if organization_id:
        params["organizationId"] = organization_id

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


def display_user_summary(summary):
    # Logs the user counts and a dormant-account estimate.
    logging.info("===== User Summary =====")

    if not summary:
        logging.info("No user summary was returned.")
        return

    total = summary.get("total")
    last_30 = summary.get("loginLast30Days")
    last_90 = summary.get("loginLast90Days")

    logging.info(f"  Total users            : {total if total is not None else 'N/A'}")
    logging.info(f"  Logged in last 30 days : {last_30 if last_30 is not None else 'N/A'}")
    logging.info(f"  Logged in last 90 days : {last_90 if last_90 is not None else 'N/A'}")

    # The two login windows overlap, so they must not be added together. Anyone in the
    # 30 day count is also in the 90 day count.
    if total is not None and last_90 is not None:
        dormant = total - last_90
        logging.info(f"  No login in 90 days    : {dormant}")
        logging.info("  (The 30 and 90 day counts overlap; do not add them together.)")


def main():
    # Ask which organization to report on
    organization_id = input("Enter an ORGANIZATION ID (press Enter for your primary org): ").strip()

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Fetch and display the summary
    summary = get_user_summary(token, organization_id=organization_id or None)
    display_user_summary(summary)


if __name__ == "__main__":
    main()
