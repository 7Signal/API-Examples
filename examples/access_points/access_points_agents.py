# This script demonstrates how to make an authenticated API call to fetch access points.
# It shows how to:
#  - Retrieve access points from the /access-points/agents endpoint
#  - Log details such as ID, name, controller, MAC address, and location ID

import os
import logging
import requests
import sys

# Add parent directory to path so we can import auth_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define API host from environment
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

def fetch_accesspoints(token):
    # Fetch access points from the API and log them.

    # Construct the request URL for access points
    url = f"https://{API_HOST}/access-points/agents"

    # Set HTTP headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logging.info("Fetching access points from %s", url)

    try:
        # Send GET request to the API
        response = requests.get(url, headers=headers)
        # Raise an error if the response status code is not 200
        response.raise_for_status()

        # Parse the JSON response into a dictionary
        data = response.json()
        logging.info("Access points fetched successfully.")

        # Log the access point details in a readable format
        log_accesspoints_summary(data)

    # Handle network or HTTP errors
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching access points: %s", e)

def log_accesspoints_summary(data):
    # Logs access point details in a readable format.

    # Check if data exists and contains the "results" key
    if not data or "results" not in data:
        logging.warning("No access points data found.")
        return

    # Iterate through each access point and log its details
    for ap in data["results"]:
        logging.info(
                "Access Point - ID: %s | Name: %s | Controller: %s | MAC: %s | Location ID: %s",
            ap.get("id"),
            ap.get("name"),
            ap.get("controller"),
            ap.get("macAddress"),
            ap.get("locationId")
       )

def main():
    # Main function to authenticate and fetch access points.
    token, _ = get_token()
    fetch_accesspoints(token)

if __name__ == "__main__":
    main()




