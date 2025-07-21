
# This script demonstrates how to make an authenticated API call with rate limit handling.
# It shows how to:
#  - Use a wrapper function to automatically retry on 429 Too Many Requests
#  - Calculate wait time based on the replenish rate before retrying
#  - Enforce a maximum retry limit using a circuit breaker
#  - Log and interpret rate limiting headers

import requests
import time
import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Configures logging
logging.basicConfig(
    level=logging.DEBUG,
    format= "%(asctime)s [%(levelname)s] %(message)s"
)

# Get the API endpoint from the environment
EYES_URL = "https://api-v2-integration.dev.7signal.com/eyes"

# If the API URL isn’t set, crash early with a clear error
if not EYES_URL:
    raise ValueError("API_URL environment variable not set")

# Get a valid bearer token from the authenticate file
token = get_token()

# Include the token in the request headers
HEADERS = {
    "Authorization": f"Bearer {token}"
}

max_retries=5

# Rate-Limited API Call
def handle_rate_limits(api_func):
    attempt = 0

    while attempt < max_retries:
        response = api_func()

        # Extract rate limit data from the response headers
        remaining = response.headers.get("x-ratelimit-remaining")
        burst = response.headers.get("x-ratelimit-burst-capacity")
        replenish = response.headers.get("x-ratelimit-replenish-rate")
        requested = response.headers.get("x-ratelimit-requested-tokens")

        logging.info(f"ratelimit-remaining: {remaining}")
        logging.info(f"ratelimit-burst-capacity: {burst}")
        logging.info(f"ratelimit-replenish-rate: {replenish}")
        logging.info(f"ratelimit-requested-tokens: {requested}")

        # Handle rate limiting if we get a 429 Too Many Requests response
        if response.status_code == 429:
            logging.warning("Rate limit exceeded (429). Retrying after delay...")

            print("You’ve hit the rate limit. Please wait while the system backs off and retries...")

            try:
                # Calculate a wait time 
                wait_time = 1 / int(replenish or 1) + 1 

            # If replenish rate is missing, default to 2 seconds
            except ValueError:
                wait_time = 2
        
            logging.info(f"Sleeping for {wait_time:.2f} seconds.")

            # Retry the request after waiting
            time.sleep(wait_time)
            continue

        # Success
        if response.ok:
            logging.info("Request successful.")
            return response.json()

        # Other errors
        logging.error(f"Request failed: {response.status_code} - {response.text}")
        return None

# Main Execution
def main():

    def get_eyes_summary():
        return requests.get(EYES_URL, headers=HEADERS)

    result = handle_rate_limits(get_eyes_summary)

    if result:
        logging.info(f"Response Data: {result}")
    else:
        logging.error("No data returned from API.")

if __name__ == "__main__":
    main()
