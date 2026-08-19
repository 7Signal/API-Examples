# This script demonstrates how to manage 7SIGNAL agent service areas.
# It shows how to:
#  - List service areas, including the search, multi-column sort, and score sort
#  - Create and update service areas in bulk
#  - Update or delete a single service area
#  - Delete several service areas in one call, after confirming
#
# Agent service areas are named sub-divisions of a location. This resource offers both
# bulk operations on the collection and single-record operations on /{serviceAreaId},
# and the two take different payload shapes - see the notes on each function.

import os
import time
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

# Sorting by this special value orders by average experience score, which needs a
# time window to be meaningful.
SCORE_SORT_VALUE = "score"


def list_service_areas(token, search_value=None, service_area_ids=None, sort=None,
                       score_sort_start=None, score_sort_end=None, page=1, per_page=10):
    # Fetches a page of agent service areas.
    #
    # Note this endpoint uses a combined `sort` parameter ("name,asc") rather than the
    # sortField/order pair most other endpoints use, and supports several sort keys by
    # repeating the parameter. Params are therefore built as a list of pairs, because a
    # dict would silently keep only the last `sort` value.
    sort_keys = list(sort) if sort else []

    if SCORE_SORT_VALUE in sort_keys and (score_sort_start is None or score_sort_end is None):
        logging.error("Sorting by score requires both scoreSortStart and scoreSortEnd "
                      "(epoch milliseconds).")
        return None

    url = f"https://{API_HOST}/service-areas/agents"
    headers = {"Authorization": f"Bearer {token}"}

    params = [("page", page), ("perPage", per_page)]

    if search_value:
        params.append(("searchValue", search_value))
    # The GET filter takes one comma-separated string, unlike the bulk delete's
    # repeated `ids` parameter
    if service_area_ids:
        params.append(("serviceAreaIds", ",".join(service_area_ids)))
    for sort_key in sort_keys:
        params.append(("sort", sort_key))
    if score_sort_start is not None:
        params.append(("scoreSortStart", score_sort_start))
    if score_sort_end is not None:
        params.append(("scoreSortEnd", score_sort_end))

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


def get_service_area(token, service_area_id):
    # Fetches a single agent service area. Returns None when it does not exist.
    url = f"https://{API_HOST}/service-areas/agents/{service_area_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            logging.info(f"No agent service area found with id {service_area_id}.")
            return None

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def create_service_areas(token, areas):
    # Creates one or more service areas. Entries carry name and address; the server
    # assigns the ids.
    url = f"https://{API_HOST}/service-areas/agents"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json={"serviceAreas": areas})
        response.raise_for_status()
        logging.info(f"Created {len(areas)} agent service area(s).")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def update_service_areas(token, areas):
    # Updates several service areas at once. Each entry must carry its own id, which
    # is how the server matches it to an existing record. Without an id the call would
    # create duplicates rather than update.
    missing_ids = [area for area in areas if not area.get("id")]
    if missing_ids:
        logging.error("Every entry in a bulk update must include its id.")
        logging.error(f"{len(missing_ids)} entry/entries had no id.")
        return None

    logging.info(f"About to update {len(areas)} agent service area(s):")
    for area in areas:
        logging.info(f"  - {area.get('id')} -> {area.get('name')}")

    if not confirm_action("Update all of the above?"):
        logging.info("Aborted; nothing was changed.")
        return None

    url = f"https://{API_HOST}/service-areas/agents"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.put(url, headers=headers, json={"serviceAreas": areas})
        response.raise_for_status()
        logging.info(f"Updated {len(areas)} agent service area(s).")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def update_service_area(token, service_area_id, name, address):
    # Updates a single service area. The id belongs in the path here, so the body
    # carries only name and address - including an id would be rejected.
    url = f"https://{API_HOST}/service-areas/agents/{service_area_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"name": name, "address": address}

    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Agent service area {service_area_id} updated.")
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


def delete_service_areas(token, service_area_ids):
    # Deletes several service areas in one call, after confirming. The ids go in the
    # `ids` query parameter, repeated once per id - this endpoint does not read a body.
    if not service_area_ids:
        logging.error("No service area ids were supplied.")
        return False

    logging.info(f"About to delete {len(service_area_ids)} agent service area(s):")
    for service_area_id in service_area_ids:
        logging.info(f"  - {service_area_id}")

    if not confirm_action("Delete all of the above?"):
        logging.info("Aborted; nothing was deleted.")
        return False

    url = f"https://{API_HOST}/service-areas/agents"
    headers = {"Authorization": f"Bearer {token}"}
    params = [("ids", service_area_id) for service_area_id in service_area_ids]

    try:
        response = requests.delete(url, headers=headers, params=params)
        response.raise_for_status()
        logging.info(f"Deleted {len(service_area_ids)} agent service area(s).")
        return True
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return False


def delete_service_area(token, service_area_id):
    # Deletes a single service area after confirming.
    if not confirm_action(f"Delete agent service area {service_area_id}?"):
        logging.info("Aborted; the agent service area was not deleted.")
        return False

    url = f"https://{API_HOST}/service-areas/agents/{service_area_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        logging.info(f"Agent service area {service_area_id} deleted.")
        return True
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return False


def display_service_areas(data):
    # Logs a readable summary of a page of agent service areas.
    areas = data.get("results", [])
    pagination = data.get("pagination", {})

    logging.info("===== Agent Service Areas =====")

    if not areas:
        logging.info("No agent service areas found.")
        return

    if pagination:
        logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                     f"({pagination.get('total', '?')} total)")
    logging.info("-----")

    for area in areas:
        logging.info(f"  Id       : {area.get('id', 'N/A')}")
        logging.info(f"  Name     : {area.get('name') or '(unnamed)'}")

        if area.get("address"):
            logging.info(f"  Address  : {area.get('address')}")
        if area.get("locationId"):
            logging.info(f"  Location : {area.get('locationId')}")
        if area.get("updatedAt"):
            logging.info(f"  Updated  : {area.get('updatedAt')}")

        logging.info("-----")


def main():
    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Show what already exists
    areas = list_service_areas(token, sort=["name,asc"])
    if areas:
        display_service_areas(areas)

    # Step 3: Offer the lifecycle actions
    logging.info("What would you like to do?")
    logging.info("  1) Search service areas by name")
    logging.info("  2) Rank service areas by experience score (last 24 hours)")
    logging.info("  3) Fetch a single service area")
    logging.info("  4) Create service areas in bulk")
    logging.info("  5) Rename a single service area")
    logging.info("  6) Rename service areas in bulk")
    logging.info("  7) Delete service areas in bulk")
    logging.info("  8) Exit")

    choice = input("Enter a number (1-8): ").strip()

    if choice == "1":
        search_value = input("Enter part of the NAME to search for: ").strip()
        if not search_value:
            logging.error("Search value cannot be empty.")
            sys.exit(1)

        found = list_service_areas(token, search_value=search_value)
        if found:
            display_service_areas(found)

    elif choice == "2":
        now_ms = int(time.time() * 1000)
        yesterday_ms = now_ms - (24 * 60 * 60 * 1000)

        ranked = list_service_areas(
            token,
            sort=[SCORE_SORT_VALUE],
            score_sort_start=yesterday_ms,
            score_sort_end=now_ms,
        )
        if ranked:
            display_service_areas(ranked)

    elif choice == "3":
        service_area_id = input("Enter the SERVICE AREA ID (UUID): ").strip()
        if not service_area_id:
            logging.error("Service area id cannot be empty.")
            sys.exit(1)

        area = get_service_area(token, service_area_id)
        if area:
            display_service_areas({"results": [area]})

    elif choice == "4":
        logging.info("Enter one service area per line as 'name|address'. Blank line to finish.")

        new_areas = []
        while True:
            line = input("  name|address: ").strip()
            if not line:
                break

            if "|" not in line:
                logging.error("Please use the form 'name|address'.")
                continue

            name, address = line.split("|", 1)
            new_areas.append({"name": name.strip(), "address": address.strip()})

        if not new_areas:
            logging.info("Nothing to create.")
            return

        if not confirm_action(f"Create {len(new_areas)} service area(s)?"):
            logging.info("Aborted; nothing was created.")
            return

        created = create_service_areas(token, new_areas)
        if created:
            display_service_areas(created)

    elif choice == "5":
        service_area_id = input("Enter the SERVICE AREA ID (UUID): ").strip()
        if not service_area_id:
            logging.error("Service area id cannot be empty.")
            sys.exit(1)

        new_name = input("Enter the NEW NAME: ").strip()
        if not new_name:
            logging.error("Name cannot be empty.")
            sys.exit(1)

        new_address = input("Enter the ADDRESS: ").strip()
        if not new_address:
            logging.error("Address cannot be empty.")
            sys.exit(1)

        if not confirm_action(f"Rename service area {service_area_id} to '{new_name}'?"):
            logging.info("Aborted; nothing was changed.")
            return

        updated = update_service_area(token, service_area_id, new_name, new_address)
        if updated:
            display_service_areas({"results": [updated]})

    elif choice == "6":
        logging.info("Enter one service area per line as 'id|name|address'. Blank line to finish.")
        logging.info("The id is required on every line - a bulk update without one would "
                     "create duplicates instead of updating.")

        updates = []
        while True:
            line = input("  id|name|address: ").strip()
            if not line:
                break

            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3 or not parts[0]:
                logging.error("Please use the form 'id|name|address', with the id filled in.")
                continue

            updates.append({"id": parts[0], "name": parts[1], "address": parts[2]})

        if not updates:
            logging.info("Nothing to update.")
            return

        updated = update_service_areas(token, updates)
        if updated:
            display_service_areas(updated)

    elif choice == "7":
        ids_input = input("Enter the SERVICE AREA IDs to delete (comma separated): ").strip()
        service_area_ids = [i.strip() for i in ids_input.split(",") if i.strip()]

        if not service_area_ids:
            logging.error("At least one service area id is required.")
            sys.exit(1)

        delete_service_areas(token, service_area_ids)

    else:
        logging.info("Nothing to do.")


if __name__ == "__main__":
    main()
