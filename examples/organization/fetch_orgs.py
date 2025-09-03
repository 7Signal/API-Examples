# This script demonstrates how to fetch and log organization data from the API.
# It shows how to:
#  - Retrieve all accessible organizations from the /organizations endpoint
#  - Log each organization's ID, name, connection ID, MobileEye code, and suspension status

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

# Define API host from environment
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

def fetch_organizations(token):
    # Fetch organization data from the API.

    # Construct the request URL
    url = f"https://{API_HOST}/organizations"

    # Set HTTP headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logging.info("Fetching organizations from %s", url)

    try:
        # Make a GET request to the API
        response = requests.get(url, headers=headers)
        # Raise an error if the status code failed
        response.raise_for_status()

        # Parse JSON response into a Python dictionary
        data = response.json()
        logging.info("Organizations fetched successfully.")
        return data
    
    # Log any network or request errors
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching organizations: %s", e)
        return None

def log_organizations(data):
    # Log each organization in a readable format.

    # Check if data is present and contains "results"
    if not data or "results" not in data:
        logging.warning("No results found in organizations data.")
        return

    # Iterate through each organization entry and log its details
    for org in data["results"]:
        logging.info(
            "ID: %s | Name: %s | Connection ID: %s | MobileEye Code: %s | Suspended: %s",
            org.get("id"),
            org.get("name"),
            org.get("connection", {}).get("id"),
            org.get("mobileEyeOrgCode"),
            org.get("isSuspended")
        )

def main():
    # Main function to get authentication token, fetch organizations, and log them.
    token, _ = get_token()
    data = fetch_organizations(token)
    log_organizations(data)

if __name__ == "__main__":
    main()
