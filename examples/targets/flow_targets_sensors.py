# This script demonstrates how to manage 7SIGNAL sensor test targets.
# It shows how to:
#  - List and fetch sensor targets
#  - Create a target, honouring the address rules that differ by target type
#  - Replace a target, and delete one after confirming
#
# Targets are the endpoints sensors test toward. Test profiles reference them by id,
# so changing or removing one affects live monitoring.

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

VALID_TARGET_TYPES = ["SONAR", "WEB_SERVER", "PING_ENDPOINT", "IPERF3_SERVER"]

# These types must be given a DNS name; an IP address alone is not accepted.
TYPES_REQUIRING_DNS = ["WEB_SERVER", "IPERF3_SERVER"]

# These types accept any one of dnsName, ipV4Address, or ipV6Address.
TYPES_ACCEPTING_ANY_ADDRESS = ["SONAR", "PING_ENDPOINT"]


def list_targets(token, page=1, per_page=10):
    # Fetches a page of sensor targets.
    # Note: the OpenAPI specification declares no query parameters for this endpoint,
    # even though the response carries a pagination object. Paging is sent here because
    # that envelope implies support, but it is unconfirmed - check pagination.page in the
    # response before relying on a paging loop.
    url = f"https://{API_HOST}/targets/sensors"
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


def get_target(token, target_id):
    # Fetches a single sensor target. Returns None when it does not exist.
    url = f"https://{API_HOST}/targets/sensors/{target_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            logging.info(f"No sensor target found with id {target_id}.")
            return None

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def validate_address(target_type, dns_name, ipv4_address, ipv6_address):
    # Checks the address rules the API applies per target type. Returns an error
    # message, or None when the combination is acceptable.
    if target_type in TYPES_REQUIRING_DNS and not dns_name:
        return f"{target_type} targets require a dnsName; an IP address alone is not accepted."

    if target_type in TYPES_ACCEPTING_ANY_ADDRESS and not any([dns_name, ipv4_address, ipv6_address]):
        return (f"{target_type} targets require at least one of "
                f"dnsName, ipV4Address, or ipV6Address.")

    return None


def create_target(token, target_type, name, description=None, dns_name=None,
                  ipv4_address=None, ipv6_address=None, tcp_port=None):
    # Creates a sensor target. targetType cannot be changed later, so it is worth
    # getting right the first time.
    if target_type not in VALID_TARGET_TYPES:
        logging.error(f"Unsupported target type: {target_type}")
        logging.error(f"Valid values are: {', '.join(VALID_TARGET_TYPES)}")
        return None

    problem = validate_address(target_type, dns_name, ipv4_address, ipv6_address)
    if problem:
        logging.error(problem)
        return None

    url = f"https://{API_HOST}/targets/sensors"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {"targetType": target_type, "name": name}
    if description:
        payload["description"] = description
    if dns_name:
        payload["dnsName"] = dns_name
    if ipv4_address:
        payload["ipV4Address"] = ipv4_address
    if ipv6_address:
        payload["ipV6Address"] = ipv6_address
    # tcpPort only applies to SONAR and IPERF3_SERVER; the API ignores it otherwise
    if tcp_port is not None:
        payload["tcpPort"] = tcp_port

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        created = response.json()
        logging.info(f"Sensor target created with id {created.get('id')}.")
        return created
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def replace_target(token, target_id, payload):
    # Replaces a sensor target. dnsName, ipV4Address, and ipV6Address fully replace
    # their previous values, so any address field left out of the payload is cleared -
    # confirm before sending, so callers importing this function get the guard too.
    if not confirm_action(f"Replace sensor target {target_id}? Any address field left "
                          "out of the payload will be cleared."):
        logging.info("Aborted; the sensor target was not changed.")
        return None

    url = f"https://{API_HOST}/targets/sensors/{target_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Sensor target {target_id} updated.")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def confirm_action(message):
    # Asks the user to type 'yes' before a change is sent to the API.
    choice = input(f"{message} Type 'yes' to confirm: ").strip().lower()
    return choice == "yes"


def delete_target(token, target_id):
    # Deletes a sensor target after confirming with the user. The API refuses the
    # delete while a test profile still references the target.
    if not confirm_action(f"Delete sensor target {target_id}?"):
        logging.info("Aborted; the sensor target was not deleted.")
        return False

    url = f"https://{API_HOST}/targets/sensors/{target_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        logging.info(f"Sensor target {target_id} deleted.")
        return True
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
        # A 400 here usually means something still depends on the target
        if response.status_code == 400:
            logging.error("A target still referenced by a test profile cannot be deleted. "
                          "Detach it from the profile first.")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return False


def display_targets(data):
    # Logs a readable summary of a page of sensor targets.
    targets = data.get("results", [])
    pagination = data.get("pagination", {})

    logging.info("===== Sensor Targets =====")

    if not targets:
        logging.info("No sensor targets found.")
        return

    if pagination:
        logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                     f"({pagination.get('total', '?')} total)")
    logging.info("-----")

    for target in targets:
        logging.info(f"  Id          : {target.get('id', 'N/A')}")
        logging.info(f"  Name        : {target.get('name', 'N/A')}")
        logging.info(f"  Type        : {target.get('targetType', 'N/A')}")

        if target.get("description"):
            logging.info(f"  Description : {target.get('description')}")
        if target.get("dnsName"):
            logging.info(f"  DNS name    : {target.get('dnsName')}")
        if target.get("ipV4Address"):
            logging.info(f"  IPv4        : {target.get('ipV4Address')}")
        if target.get("ipV6Address"):
            logging.info(f"  IPv6        : {target.get('ipV6Address')}")
        if target.get("tcpPort") is not None:
            logging.info(f"  TCP port    : {target.get('tcpPort')}")

        logging.info("-----")


def main():
    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Show what already exists
    targets = list_targets(token)
    if targets:
        display_targets(targets)

    # Step 3: Offer the lifecycle actions
    logging.info("What would you like to do?")
    logging.info("  1) Fetch a single target")
    logging.info("  2) Create a new target")
    logging.info("  3) Rename an existing target")
    logging.info("  4) Delete a target")
    logging.info("  5) Exit")

    choice = input("Enter a number (1-5): ").strip()

    if choice == "1":
        target_id = input("Enter the TARGET ID (a number): ").strip()
        if not target_id:
            logging.error("Target id cannot be empty.")
            sys.exit(1)

        target = get_target(token, target_id)
        if target:
            display_targets({"results": [target]})

    elif choice == "2":
        logging.info(f"Available target types: {', '.join(VALID_TARGET_TYPES)}")
        target_type = input("Enter the TARGET TYPE: ").strip().upper()
        if target_type not in VALID_TARGET_TYPES:
            logging.error(f"Target type must be one of: {', '.join(VALID_TARGET_TYPES)}")
            sys.exit(1)

        name = input("Enter a NAME for the target: ").strip()
        if not name:
            logging.error("Name cannot be empty.")
            sys.exit(1)

        if target_type in TYPES_REQUIRING_DNS:
            logging.info(f"{target_type} targets require a DNS name.")
        else:
            logging.info(f"{target_type} targets need a DNS name or an IP address.")

        dns_name = input("Enter the DNS name (optional if an IP is given): ").strip() or None
        ipv4_address = input("Enter the IPv4 address (optional): ").strip() or None

        port_input = input("Enter the TCP port (optional, SONAR/IPERF3_SERVER only): ").strip()
        tcp_port = None
        if port_input:
            try:
                tcp_port = int(port_input)
            except ValueError:
                logging.error("TCP port must be a number.")
                sys.exit(1)

        if not confirm_action(f"Create {target_type} target '{name}'?"):
            logging.info("Aborted; no target was created.")
            return

        created = create_target(
            token, target_type, name,
            dns_name=dns_name, ipv4_address=ipv4_address, tcp_port=tcp_port,
        )
        if created:
            display_targets({"results": [created]})

    elif choice == "3":
        target_id = input("Enter the TARGET ID (a number): ").strip()
        if not target_id:
            logging.error("Target id cannot be empty.")
            sys.exit(1)

        # Fetch first so the address fields can be resent; omitting one clears it
        existing = get_target(token, target_id)
        if not existing:
            return

        new_name = input("Enter the NEW NAME: ").strip()
        if not new_name:
            logging.error("Name cannot be empty.")
            sys.exit(1)

        payload = {"name": new_name}
        for field in ("description", "dnsName", "ipV4Address", "ipV6Address", "tcpPort"):
            if existing.get(field) is not None:
                payload[field] = existing[field]

        # replace_target() prompts for confirmation itself
        updated = replace_target(token, target_id, payload)
        if updated:
            display_targets({"results": [updated]})

    elif choice == "4":
        target_id = input("Enter the TARGET ID (a number): ").strip()
        if not target_id:
            logging.error("Target id cannot be empty.")
            sys.exit(1)

        delete_target(token, target_id)

    else:
        logging.info("Nothing to do.")


if __name__ == "__main__":
    main()
