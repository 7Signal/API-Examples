# This script demonstrates how to make an authenticated API call to fetch network agents.
# It shows how to:
#  - Retrieve network agents from the /networks/agents endpoint
#  - Log each agent's ID, name, enabled status, creation date, and last update date

import os
import logging
import requests
import sys

# Ensure we can import get_token from two levels up
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define API host from environment
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

def fetch_networks_agents(token):
    # Fetch network agent data from the API.

    # The API URL for fetching network agents.
    url = f"https://{API_HOST}/networks/agents"

    # Set up request headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logging.info("Fetching networks agents from %s", url)

    try:
        # Send GET request to the API.
        response = requests.get(url, headers=headers)
        # Raise an exception if the response status code is an error.
        response.raise_for_status()

        # Parse the response as JSON.
        data = response.json()
        logging.info("Networks Agents fetched successfully.")
        return data
    
    # Log any request or connection error.
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching networks agents: %s", e)
        return None

def log_networks_agents(data):
    # Log each agent in a readable format.

    # Ensure the data is valid and contains 'results'.
    if not data or "results" not in data:
        logging.warning("No results found in networks agents data.")
        return

    # Iterate through each network agent and log its details.
    for network in data["results"]:
        logging.info(
            "ID: %s | Name: %s | Enabled: %s | Created: %s | Updated: %s",
            network.get("id"),
            network.get("name"),
            network.get("isEnabled"),
            network.get("createdAt"),
            network.get("updatedAt")
       )

def main():
    # Main function to get authentication token, fetch network agents, and log them.
    token, _ = get_token()
    data = fetch_networks_agents(token)
    log_networks_agents(data)

if __name__ == "__main__":
    main()



