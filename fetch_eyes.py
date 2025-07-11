# This script demonstrates how to call the /eyes API endpoint using an OAuth2 access token.
# It shows how to:
#   - Import and reuse the access token logic from authenticate.py
#   - Send a GET request to the /eyes endpoint with the parameters
#   - Log and handle both successful and failed responses (e.g., 400 Bad Request)

#!/usr/bin/env python3

import os
import logging
import requests
from authenticate import get_token # Allows us to fetch a JWT token using API key and secret

# Configure the logging for the script
logging.basicConfig(
    level = logging.DEBUG,
    format = "%(asctime)s [%(levelname)s] %(message)s"
)

# Reads the API URL for the /eyes endpoint from the environment variables
# This allows the script to be flexible with it's target.
eyes_url = os.environ.get("EYES_URL")
if not eyes_url:
    raise EnvironmentError("eyes_url must be set in environment variables")


def fetch_eyes_summary(token, organizationId=None, organization=None, eyesType=None):
    # Uses a valid token to query the /eyes endpoint with optional filters.
    # This function abstracts away the request logic and logs either a summary
    # of the returned data or details of an error response.
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Builds the parameters dynamically
    parameters = {}
    if organizationId:
        parameters["organizationId"] = organizationId
    if organization:
        parameters["organization"] = organization
    if eyesType:
        parameters["eyesType"] = eyesType

    logging.info(f"Calling GET /eyes with parameters: {parameters}")

    response = requests.get(eyes_url, headers=headers, params=parameters)

    # If the request is successful, it will log and display this formatted summary
    if response.status_code == 200:
        data = response.json()
        logging.info("Successfully fetched eyes summary")
        logging.info(data)
        log_summary(data)

    # If request failed, this will print this error message
    else:
        data = response.json()
        logging.error(f"API call failed with status code {response.status_code}")
        logging.debug(f"Timestamp: {data.get('timestamp')}")
        logging.debug(f"Error: {data.get('error')}")
        logging.debug(f"Message: {data.get('message')}")
        logging.debug(f"Path: {data.get('path')}")
        logging.debug(f"Request ID: {data.get('requestId')}")


def log_summary(data):
    # Logs a readable summary of the response structure from the /eyes endpoint.
    # Useful for human inspection or troubleshooting API behavior.

    # This logs the agent related info
    logging.info("=== Agents Summary ===")
    agents = data.get("agents", {})
    logging.info(f"Organization: {agents.get('organizationName')}")
    logging.info(f"Device Count: {agents.get('deviceCount')}")

    license_info = agents.get("licenseSummary", {})
    logging.info("License Summary:")
    logging.info(f"  Package: {license_info.get('packageName')}")
    logging.info(f"  Total: {license_info.get('totalLicenses')}")
    logging.info(f"  Used: {license_info.get('usedLicenses')}")
    logging.info(f"  Free: {license_info.get('freeLicenses')}")

    platform_info = agents.get("platformSummary", {})
    logging.info("Platform Summary:")
    for platform, count in platform_info.items():
        logging.info(f"  {platform.capitalize()}: {count}")

    # This logs the sensor related info
    logging.info("=== Sensors Summary ===")
    sensors = data.get("sensors", {})
    logging.info(f"Device Count: {sensors.get('deviceCount')}")

    status_summary = sensors.get("deviceStatusSummary", {})
    logging.info("Device Status:")
    for status, count in status_summary.items():
        logging.info(f"  {status.capitalize()}: {count}")

    model_summary = sensors.get("modelSummary", {})
    logging.info("Model Summary:")
    for model, count in model_summary.items():
        logging.info(f"  Model {model}: {count}")


def main():
    # Main program logic. Fetches a bearer token and uses it to retrieve
    # summary information from the /eyes API.
    token, expires_at = get_token()

    # You can pass organizationId, organization, and eyesType here
    if token:
        fetch_eyes_summary(token, organizationId = None, organization = None, eyesType = None)

if __name__ == "__main__":
    main()