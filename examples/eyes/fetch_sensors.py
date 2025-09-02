# This script demonstrates how to make an authenticated API call to fetch Eyes Sensors.
# It shows how to:
#  - Retrieve sensor details from the /eyes/v2/sensors endpoint
#  - Log all key-value pairs of each sensor information

import os
import requests
import sys
import logging

# Make sure we can import get_token
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define API Host from environment
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

def fetch_sensors(token):
    # Construct the full API URL for fetching all Eyes Sensors
    sensors_url = f"https://{API_HOST}/eyes/sensors"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(sensors_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # calls the helper function to log each sensor's details
        for sensor in data.get("results", []):
            log_sensor_summary(sensor)

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

def log_sensor_summary(sensor):
    # Logs all key-value pairs from a sensor dictionary.
    logging.info("===== Sensor Summary =====")
    for key, value in sensor.items():
        logging.info(f"{key}: {value}")

def main():
    # fetches the token from the auth_utils.py file
    token, _ = get_token()
    # calls the API using that token
    fetch_sensors(token)

if __name__ == "__main__":
    main()
