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

# Get the full endpoint from APIKEYS
APIKEYS_URL = "https://api-v2-integration.dev.7signal.com/apikeys"
if not APIKEYS_URL:
    raise ValueError("APIKEYS_URL variable not set")

# GET request function
def get_apikeys(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logging.info(f"Sending GET request to {APIKEYS_URL}")

    response = requests.get(APIKEYS_URL, headers=headers)

    if response.ok:
        logging.info("Request successful.")
        return response.json()
    else:
        logging.error(f"Request failed: {response.status_code} - {response.text}")
        return None

# New function to log response details nicely
def log_response_data(response_data):
    if not response_data:
        logging.warning("No response data to log.")
        return

    pagination = response_data.get("pagination", {})
    results = response_data.get("results", [])

    logging.info("Pagination:")
    logging.info(f"  perPage: {pagination.get('perPage')}")
    logging.info(f"  page: {pagination.get('page')}")
    logging.info(f"  total: {pagination.get('total')}")
    logging.info(f"  pages: {pagination.get('pages')}")

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
    token, _ = get_token()
    result = get_apikeys(token)

    if result:
        logging.info("Response received:")
        log_response_data(result)
    else:
        logging.error("No data returned from API.")

if __name__ == "__main__":
    main()
