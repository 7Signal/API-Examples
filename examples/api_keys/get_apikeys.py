# This script demonstrates how to make an authenticated API call to fetch a list of API keys.
# It shows how to:
#  - Make a GET request to the /apikeys endpoint using a bearer token
#  - Parse and log pagination metadata and key details for each API key in the response

import requests
import logging
import os
import sys

# Add path to import shared auth logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Define API host from environment
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

# Construct the full API URL
APIKEYS_URL = f"https://{API_HOST}/apikeys"

# Makes a GET request to /apikeys using the provided token
def get_apikeys(token):
    # Add the Bearer token to the request headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logging.info(f"Sending GET request to {APIKEYS_URL}")

    # Make the HTTP GET request
    response = requests.get(APIKEYS_URL, headers=headers)

    # If the request is successful, it will log and display the formatted summary
    if response.ok:
        logging.info("Request successful.")
        return response.json()
    else:
        # Log error status code and response content
        logging.error(f"Request failed: {response.status_code} - {response.text}")
        return None

# Logs details from the response in a structured way
def log_response_data(response_data):
    if not response_data:
        logging.warning("No response data to log.")
        return

    # Extract pagination data and result entries from the response
    pagination = response_data.get("pagination", {})
    results = response_data.get("results", [])

    # Log pagination info
    logging.info("Pagination:")
    logging.info(f"  perPage: {pagination.get('perPage')}")
    logging.info(f"  page: {pagination.get('page')}")
    logging.info(f"  total: {pagination.get('total')}")
    logging.info(f"  pages: {pagination.get('pages')}")

    # Log each result (API key entry)
    logging.info(f"Results ({len(results)} items):")
    for i, item in enumerate(results, start=1):
        logging.info(f"  Result #{i}:")
        logging.info(f"    id: {item.get('id')}")
        logging.info(f"    apiKey: {item.get('apiKey')}")
        logging.info(f"    createdBy: {item.get('createdBy')}")
        logging.info(f"    description: {item.get('description')}")
        logging.info(f"    createdAt: {item.get('createdAt')}")
        org = item.get('organization', {})
        logging.info(f"    organization.id: {org.get('id')}")
        logging.info(f"    isSystem: {item.get('isSystem')}")

# Main logic
def main():
    # Main program logic. Fetches a bearer token and uses it to retrieve
    # summary information from /apikeys.
    token, _ = get_token()
    result = get_apikeys(token)

    if result:
        logging.info("Response received:")
        log_response_data(result)
    else:
        logging.error("No data returned from API.")

if __name__ == "__main__":
    main()
