# This script demonstrates how to make an authenticated API call to fetch a list of users.
# It shows how to:
#  - Make a GET request to the /users endpoint with query parameters
#  - Log the total number of users returned and basic info per user
#  - Handle cases where the response structure may vary or be missing expected keys

import os
import requests
import logging
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
) 

# Define API host from environment
API_HOST = os.getenv("API_HOST", "api-v2-integration.dev.7signal.com")

# Fetch users endpoint URL
users_url = f"https://{API_HOST}/users"

def fetch_users(token):
    # This function fetches the users from the /users endpoint using the token

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {}

    # logs the request details
    logging.info(f"GET /users with params: {params}")

    try:
        # send the GET request to the users endpoints
        response = requests.get(users_url, headers=headers, params=params)
        response.raise_for_status()

        # parses the JSON response
        data = response.json()
        logging.debug(f"Response: {data}")

        # calls the helper function to log the users information
        log_users_summary(data)

    # logs HTTP specific errors
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred: {e}")
        logging.error(f"Response content: {response.text}")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")


def log_users_summary(data):
    # Logs a summary of user details from the response data

    users = data.get("results", [])

    # warning if no users were found in the response
    if not users:
        # logs how many users were returned
        logging.warning("No users found in 'results' key.")
    else:
        logging.info(f"Total Users: {len(users)}")
        for user in users:
            name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
            email = user.get("email")
            user_id = user.get("id")
            role = user.get("roleKey", user.get("role", {}).get("name"))
            logging.info(f"- {name} | {email} | ID: {user_id} | Role: {role}")


def main():

    # fetches the token from the auth_utils.py file
    token, _ = get_token()
    # calls the API using that token
    fetch_users(token)

if __name__ == "__main__":
    main()

