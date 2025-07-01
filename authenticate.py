#This script demonstrates how to authenticate to an API using the OAuth2 Client Credentials flow.
#It shows how to:
#  - Read API key and secret from environment variables
#  - Request a bearer token from the authentication server
#  - Store the token and its expiration time in memory
#  - Reuse the token for future API calls until it expires

import os
import time
import logging
import requests

# Configure logging for the script
logging.basicConfig(

    # Level: set the minimum level of messages to DEBUG for more detail
    level = logging.DEBUG,

    # Format for how the log messages will appear: Ti,estamp + log level + message
    format = "%(asctime)s [%(levelname)s] %(message)s"
)

# Get API credentials from environment variables
# These must be set in your shell before running the script
client_id = os.environ.get("API_KEY")
client_secret = os.environ.get("API_SECRET")

# Raises an error if credentials are not provided
if not client_id or not client_secret:
    raise EnvironmentError("API_KEY and API_SECRET must be set in environment variables.")

# Get token endpoint from the environment variable
# This is the endpoint used to request a 0Auth2 access token
token_url = os.environ.get("TOKEN_URL")

# Raises an error if the token_url is not set, so the user knows they must provide it
if not token_url:
    raise EnvironmentError("token_url must be set in environment variables.")

# This stores the token and its expiration in the token_info dictionary
token_info = {
    "access_token": None,
    "expires_at": 0
}

# Retrieve an access token using client_credentials.
# If a valid token is already cached, reuse it.
def get_token():
    # Gets the current time --> used to check if token is still valid
    current_time = time.time()

    # Checks if the token is not expired --> if it is, it prints a message and reuse it
    if token_info["access_token"] and current_time < token_info["expires_at"]:
        logging.info("Reusing cached token")
        return token_info["access_token"]

    # If theres no valid token, it'll print to get a new one
    logging.info("Requesting new token...")

    # The request payload contains the data for the POST request to get the token
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    # Which format we're sending the data in
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Sends a POST request with the payload and headers to the token endpoint
    response = requests.post(token_url, data=payload, headers=headers)

    # if the request succeeded, it extracts the token and how long its valid
    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        expires_in = data["expires_in"]

        # Save token and expiry in the token_info dictionary
        token_info["access_token"] = access_token
        token_info["expires_at"] = current_time + expires_in

        # prints the confirmation and return the token
        logging.info("Token received and stored in memory")
        return access_token
    
    # if request failed, it'll print an error 
    else:
        logging.error("Failed to retrieve token")
        logging.debug(f"Status code: {response.status_code}")
        logging.debug(f"Response body: {response.text}")
        return None

# Main program entry point.
# Gets an access token and makes a follow-up API call.
def main():
    # Calls get_token() to either fetch or reuse an access token
    token = get_token()
    if token:
        logging.info("Ready to use token:")
        logging.debug(f"Access token: {token}")

if __name__ == "__main__":
    main()
