# This script demonstrates how to read 7SIGNAL sensor default configurations.
# It shows how to:
#  - List the configuration bundles available to an organization
#  - Fetch one bundle and see which components it applies
#
# A default configuration groups a test profile template, OTA configuration, alarm
# group, SLA group, and target references together. Service Areas and Organizations
# reference one by its defaultConfigurationId. These endpoints are read-only; the
# bundles themselves are assembled elsewhere in the platform.

import os
import logging
import requests
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Environment variables
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

# The id fields a bundle may apply, paired with a readable label. Every one is
# optional - a bundle that does not apply an alarm group simply omits alarmGroupId.
CONFIGURATION_REFERENCES = [
    ("testProfileTemplateId", "Test profile template"),
    ("otaConfigurationId", "OTA configuration"),
    ("alarmGroupId", "Alarm group"),
    ("sonarId", "Sonar target"),
    ("pingEndPointId", "Ping endpoint"),
    ("webServerId", "Web server target"),
    ("slaGroupId", "SLA group"),
]


def list_default_configurations(token, page=1, per_page=10):
    # Fetches a page of sensor default configurations.
    # Note: the OpenAPI specification declares no query parameters for this endpoint,
    # even though the response carries a pagination object. Paging is sent here because
    # that envelope implies support, but it is unconfirmed - check pagination.page in the
    # response before relying on a paging loop.
    url = f"https://{API_HOST}/default-configurations/sensors"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": page, "perPage": per_page}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def get_default_configuration(token, configuration_id):
    # Fetches a single default configuration. Returns None when it does not exist.
    url = f"https://{API_HOST}/default-configurations/sensors/{configuration_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            logging.info(f"No sensor default configuration found with id {configuration_id}.")
            return None

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def display_default_configurations(data):
    # Logs a readable summary of the configuration bundles.
    configurations = data.get("results", [])
    pagination = data.get("pagination", {})

    logging.info("===== Sensor Default Configurations =====")

    if not configurations:
        logging.info("No sensor default configurations found.")
        return

    if pagination:
        logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                     f"({pagination.get('total', '?')} total)")
    logging.info("-----")

    for configuration in configurations:
        logging.info(f"  Id   : {configuration.get('id', 'N/A')}")
        logging.info(f"  Name : {configuration.get('name') or '(unnamed)'}")

        # Only report the references this bundle actually applies
        applied = [(field, label) for field, label in CONFIGURATION_REFERENCES
                   if configuration.get(field) is not None]

        if applied:
            logging.info("  Applies:")
            for field, label in applied:
                logging.info(f"    {label}: {configuration.get(field)}")
        else:
            logging.info("  Applies: nothing (empty bundle)")

        logging.info("-----")


def main():
    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: List the bundles available to this organization
    configurations = list_default_configurations(token)
    if configurations:
        display_default_configurations(configurations)

    # Step 3: Optionally drill into one of them
    configuration_id = input("Enter a CONFIGURATION ID to fetch (press Enter to skip): ").strip()
    if not configuration_id:
        return

    configuration = get_default_configuration(token, configuration_id)
    if configuration:
        display_default_configurations({"results": [configuration]})


if __name__ == "__main__":
    main()
