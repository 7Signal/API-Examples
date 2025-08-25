# This script demonstrates how to fetch and log group data from the API.
# It shows how to:
#  - Retrieve all accessible groups from the /groups endpoint
#  - Log each group's ID, key, display name, organization ID, and instance ID

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
API_HOST = os.getenv("API_HOST")
if not API_HOST:
    raise ValueError("API_HOST environment variable not set")

def fetch_groups(token):
    # Fetch group data from the API.

    # Construct the request URL
    url = f"https://{API_HOST}/groups"

    # Set HTTP headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logging.info("Fetching groups from %s", url)

    try:
        # Make a GET request to the API
        response = requests.get(url, headers=headers)
        # Raise an error if the status code shows failure
        response.raise_for_status()

        # Parse JSON response into a Python dictionary
        data = response.json()
        logging.info("Groups fetched successfully.")
        return data
    
    # Log any network or request errors
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching groups: %s", e)
        return None

def log_groups(data):
    # Log each group in a readable format.

    # Check if data is present and contains "results"
    if not data or "results" not in data:
        logging.warning("No results found in groups data.")
        return

    # Iterate through each group entry and log its details
    for group in data["results"]:
        logging.info(
            "ID: %s | Key: %s | Display Name: %s | Organization ID: %s | Instance ID: %s",
            group.get("id"),
            group.get("key"),
            group.get("displayName"),
            group.get("organization", {}).get("id"),
            group.get("instance", {}).get("id")
        )

def main():
    # Main function to get authentication token, fetch groups, and log them.
    token, _ = get_token()
    data = fetch_groups(token)
    log_groups(data)

if __name__ == "__main__":
    main()
