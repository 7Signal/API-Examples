# This script demonstrates how to fetch and log role data from the API.
# It shows how to:
#  - Retrieve all accessible roles from the /roles endpoint
#  - Log each role's ID, key, description, Auth0 ID, and whether it is public

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

def fetch_roles(token):
    # Fetch role data from the API.

    # Construct the request URL
    url = f"https://{API_HOST}/roles"

    # Set HTTP headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logging.info("Fetching roles from %s", url)

    try:
        # Make a GET request to the API
        response = requests.get(url, headers=headers)
        # Raise an error if the status code shows failure
        response.raise_for_status()

        # Parse JSON response into a Python dictionary
        data = response.json()
        logging.info("Roles fetched successfully.")
        return data
    
    # Log any network or request errors
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching roles: %s", e)
        return None

def log_roles(data):
    # Log each role in a readable format.

    # Check if data is present and contains "results"
    if not data or "results" not in data:
        logging.warning("No results found in roles data.")
        return

    # Iterate through each role entry and log its details
    for role in data["results"]:
        logging.info(
            "ID: %s | Key: %s | Description: %s | Auth0 ID: %s | Public: %s",
            role.get("id"),
            role.get("key"),
            role.get("description"),
            role.get("auth0Id"),
            role.get("isPublic")
        )

def main():
    # Main function to get authentication token, fetch roles, and log them.
    token, _ = get_token()
    data = fetch_roles(token)
    log_roles(data)

if __name__ == "__main__":
    main()
