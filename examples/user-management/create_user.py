# This script demonstrates how to make an authenticated API call to fetch a list of users.
# It shows how to:
#  - Make a GET request to the /users endpoint with query parameters
#  - Log the total number of users returned and basic info per user
#  - Handle cases where the response structure may vary or be missing expected keys

import os
import requests
import logging
from authenticate import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Fetch users endpoint URL from environment variable
users_url = os.environ.get("USERS_URL")
if not users_url:
    raise EnvironmentError("USERS_URL must be set in environment variables")


def fetch_users(token, organization_id=None):
    # This function fetches the users from the /users endpoint using the token

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {}

    # logs the request details
    logging.info(f"GET /users with params: {params}")

    # send the GET request to the users endpoints
    response = requests.get(users_url, headers=headers, params=params)

    try:
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

    data = response.json()


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

    # fetches the token from the authenticate.py file
    token, expires_at = get_token()
    # calls the API using that token
    fetch_users(token)

if __name__ == "__main__":
    main()
