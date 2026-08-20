# This script demonstrates how to manage 7SIGNAL sensor network keys.
# It shows how to:
#  - List network keys and the pre-built templates
#  - Create a key, with the type deciding which other fields apply
#  - Replace a key safely, without writing masked secrets back over real ones
#  - Delete a key, with a confirmation prompt first
#
# Network keys hold the credentials sensors use to associate to a wireless network.
# The API returns every secret masked as "********" and never returns the real value,
# so a fetch-modify-send round trip will overwrite the real secret with the mask
# unless you re-supply it. This script refuses to send a masked value.

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

VALID_KEY_TYPES = [
    "WPA1", "WPA2", "WPA3", "WPA3_OWE", "WPA_EAP", "WPA_EAP_SCEP",
    "IEEE_802_1X", "OPEN_HTTP", "HTTP_AUTHENTICATION", "RAW",
]

# The value the API substitutes for any secret it will not return
SECRET_MASK = "********"

# Fields the API masks. Sending the mask back would set it as the literal secret.
SECRET_FIELDS = [
    "passphraseOrPsk",
    "password",
    "preSharedKey",
    "privateKeyPassword",
    "innerPrivateKeyPassword",
    "challengePassword",
]


def list_network_keys(token, page=1, per_page=10):
    # Fetches a page of sensor network keys.
    # Note: the OpenAPI specification declares no query parameters for this endpoint,
    # even though the response carries a pagination object. Paging is sent here because
    # that envelope implies support, but it is unconfirmed - check pagination.page in the
    # response before relying on a paging loop.
    url = f"https://{API_HOST}/network-keys/sensors"
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


def list_templates(token):
    # Fetches the pre-built templates. These are the practical starting point for
    # HTTP_AUTHENTICATION (captive portal) keys, whose login page definitions are
    # tedious to build from scratch.
    url = f"https://{API_HOST}/network-keys/sensors/templates"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def get_network_key(token, network_key_id):
    # Fetches a single network key. Returns None when it does not exist.
    url = f"https://{API_HOST}/network-keys/sensors/{network_key_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            logging.info(f"No sensor network key found with id {network_key_id}.")
            return None

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def contains_masked_secret(payload):
    # Reports whether any secret field still holds the API's mask rather than a
    # real value.
    for field in SECRET_FIELDS:
        if payload.get(field) == SECRET_MASK:
            return True

    return False


def create_network_key(token, key_type, name, extra_fields=None):
    # Creates a network key. Only type and name are required; which other fields
    # apply is decided entirely by type. See the Swagger UI for the per-type list.
    if key_type not in VALID_KEY_TYPES:
        logging.error(f"Unsupported network key type: {key_type}")
        logging.error(f"Valid values are: {', '.join(VALID_KEY_TYPES)}")
        return None

    url = f"https://{API_HOST}/network-keys/sensors"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {"type": key_type, "name": name}
    if extra_fields:
        payload.update(extra_fields)

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        created = response.json()
        logging.info(f"Sensor network key created with id {created.get('id')}.")
        return created
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def replace_network_key(token, network_key_id, payload):
    # Replaces a network key. This is a full replace, so the payload must carry the
    # complete desired state, including real values for any secret.
    if contains_masked_secret(payload):
        logging.error(f"Refusing to send a payload containing the mask {SECRET_MASK}.")
        logging.error("The API masks secrets on read and never returns the real value, so "
                      "sending a fetched object back would overwrite the real secret with "
                      "the mask.")
        logging.error(f"Re-supply the real value for one of: {', '.join(SECRET_FIELDS)}")
        return None

    if not confirm_action(f"Replace network key {network_key_id}? Sensors using this key "
                          "will pick up the new settings."):
        logging.info("Aborted; the network key was not changed.")
        return None

    url = f"https://{API_HOST}/network-keys/sensors/{network_key_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Sensor network key {network_key_id} updated.")
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


def delete_network_key(token, network_key_id):
    # Deletes a network key after confirming with the user.
    if not confirm_action(f"Delete sensor network key {network_key_id}?"):
        logging.info("Aborted; the sensor network key was not deleted.")
        return False

    url = f"https://{API_HOST}/network-keys/sensors/{network_key_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.delete(url, headers=headers)

        # The API returns 409 while the key is still in use
        if response.status_code == 409:
            logging.info(f"Network key {network_key_id} is still bound to a wireless "
                         "network or a sensor and cannot be deleted.")
            logging.info("Remove those bindings first, then try again.")
            return False

        if response.status_code == 404:
            logging.info(f"No sensor network key found with id {network_key_id}.")
            return False

        response.raise_for_status()
        logging.info(f"Sensor network key {network_key_id} deleted.")
        return True
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return False


def display_network_keys(data, heading="Sensor Network Keys"):
    # Logs a readable summary of network keys. Secrets are already masked by the API.
    keys = data.get("results", [])
    pagination = data.get("pagination", {})

    logging.info(f"===== {heading} =====")

    if not keys:
        logging.info("No sensor network keys found.")
        return

    if pagination:
        logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                     f"({pagination.get('total', '?')} total)")
    logging.info("-----")

    for key in keys:
        logging.info(f"  Id       : {key.get('id', 'N/A')}")
        logging.info(f"  Name     : {key.get('name', 'N/A')}")
        logging.info(f"  Type     : {key.get('type', 'N/A')}")

        if key.get("eapMethod"):
            logging.info(f"  EAP      : {key.get('eapMethod')}")

        # Show whether a secret is configured without echoing anything sensitive
        configured = [f for f in SECRET_FIELDS if key.get(f)]
        if configured:
            logging.info(f"  Secrets  : configured ({', '.join(configured)})")

        logging.info("-----")


def main():
    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Show what already exists
    keys = list_network_keys(token)
    if keys:
        display_network_keys(keys)

    # Step 3: Offer the lifecycle actions
    logging.info("What would you like to do?")
    logging.info("  1) Fetch a single network key")
    logging.info("  2) List the pre-built templates")
    logging.info("  3) Create a WPA2 network key")
    logging.info("  4) Rename a WPA2 key (needs the real passphrase re-supplied)")
    logging.info("  5) Delete a network key")
    logging.info("  6) Exit")

    choice = input("Enter a number (1-6): ").strip()

    if choice == "1":
        key_id = input("Enter the NETWORK KEY ID (a number): ").strip()
        if not key_id:
            logging.error("Network key id cannot be empty.")
            sys.exit(1)

        key = get_network_key(token, key_id)
        if key:
            display_network_keys({"results": [key]})

            if contains_masked_secret(key):
                logging.info("Note: this key's secret is masked. To change any field with "
                             "PUT you must re-supply the real secret value.")

    elif choice == "2":
        templates = list_templates(token)
        if templates:
            display_network_keys(templates, heading="Network Key Templates")

    elif choice == "3":
        name = input("Enter a NAME for the key: ").strip()
        if not name:
            logging.error("Name cannot be empty.")
            sys.exit(1)

        passphrase = input("Enter the WPA2 PASSPHRASE: ").strip()
        if not passphrase:
            logging.error("Passphrase cannot be empty.")
            sys.exit(1)

        if passphrase == SECRET_MASK:
            logging.error(f"{SECRET_MASK} is the API's mask for a hidden secret, not a "
                          "usable passphrase.")
            sys.exit(1)

        if not confirm_action(f"Create WPA2 network key '{name}'?"):
            logging.info("Aborted; no network key was created.")
            return

        created = create_network_key(
            token, "WPA2", name,
            extra_fields={"usePassphrase": True, "passphraseOrPsk": passphrase},
        )
        if created:
            display_network_keys({"results": [created]})

    elif choice == "4":
        key_id = input("Enter the NETWORK KEY ID (a number): ").strip()
        if not key_id:
            logging.error("Network key id cannot be empty.")
            sys.exit(1)

        existing = get_network_key(token, key_id)
        if not existing:
            return

        if existing.get("type") != "WPA2":
            logging.error(f"This example only renames WPA2 keys; {key_id} is "
                          f"{existing.get('type')}.")
            logging.error("Other key types have type-specific fields a full replace "
                          "would need to carry - see the Swagger UI for the field list.")
            return

        new_name = input("Enter the NEW NAME: ").strip()
        if not new_name:
            logging.error("Name cannot be empty.")
            sys.exit(1)

        # PUT is a full replace and the fetched passphrase is masked, so the real
        # value has to be supplied again or it would be overwritten with the mask
        logging.info("A full replace needs the real passphrase; the API never returns it.")
        passphrase = input("Re-enter the WPA2 PASSPHRASE: ").strip()
        if not passphrase or passphrase == SECRET_MASK:
            logging.error("A real passphrase is required to rename this key safely.")
            sys.exit(1)

        payload = dict(existing)
        payload["name"] = new_name
        payload["passphraseOrPsk"] = passphrase

        updated = replace_network_key(token, key_id, payload)
        if updated:
            display_network_keys({"results": [updated]})

    elif choice == "5":
        key_id = input("Enter the NETWORK KEY ID (a number): ").strip()
        if not key_id:
            logging.error("Network key id cannot be empty.")
            sys.exit(1)

        delete_network_key(token, key_id)

    else:
        logging.info("Nothing to do.")


if __name__ == "__main__":
    main()
