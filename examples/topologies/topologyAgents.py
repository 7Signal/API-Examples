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
API_HOST = os.getenv("API_HOST")
if not API_HOST:
    raise ValueError("API_HOST environment variable not set")

def fetch_topologies_agents_locations(token):
   # Fetch topology agent location data from the API.

    # Construct the request URL
    url = f"https://{API_HOST}/topologies/agents/locations"

    # Set HTTP headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logging.info("Fetching topologies agents locations from %s", url)

    try:
        # Make a GET request to the API
        response = requests.get(url, headers=headers)
        # Raise an error if the status code shows failure
        response.raise_for_status()

        # Parse JSON response into a Python dictionary
        data = response.json()
        logging.info("Topologies Agents Locations fetched successfully.")
        return data
    
    # Log any network or request errors
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching topologies agents locations: %s", e)
        return None

def log_topologies_agents_locations(data):
    # Log each agent location in a readable format.

    # Check if data is present and contains "results"
    if not data or "results" not in data:
        logging.warning("No results found in topologies agents locations data.")
        return

    # Iterate through each location entry and log its details
    for location in data["results"]:
        logging.info(
            "ID: %s | Name: %s | Address: %s | Created: %s | Updated: %s",
            location.get("id"),
            location.get("name"),
            location.get("address"),
            location.get("createdAt"),
            location.get("updatedAt")
       )

def main():
    # Main function to get authentication token, fetch topology agent locations, and log them.
    token, _ = get_token()
    data = fetch_topologies_agents_locations(token)
    log_topologies_agents_locations(data)

if __name__ == "__main__":
    main()


