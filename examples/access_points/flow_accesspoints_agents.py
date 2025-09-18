# This script demonstrates how to make authenticated API calls to fetch Access Point.
# It shows how to:
#  - Make a GET request to the /access-points/agents endpoint using a bearer token
#  - Print a summary of each access point (ID, name, controller)
#  - Prompt the user to optionally view detailed information for a specific access point
#  - Fetch and display details from /access-points/agents/{accessPointId}, including BSSIDs

import os
import requests
import logging
import sys

# Allow importing get_token from two levels up
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Load environment variables
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

# Fetch a list of access points
def list_access_point_agents(token):
    # Construct endpoint URL
    url = f"https://{API_HOST}/access-points/agents"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    # GET request
    response = requests.get(url, headers=headers)
    # Raise exception if HTTP status indicates error
    response.raise_for_status()
    # Return 'results' list or empty list
    return response.json().get("results", [])

# Fetch detailed information about a specific access points by ID
def get_agent_details(token, accessPointId):
    # Construct endpoint URL
    url = f"https://{API_HOST}/access-points/agents/{accessPointId}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # GET request
    response = requests.get(url, headers=headers)
    # Raise exception if HTTP status indicates error
    response.raise_for_status()
    return response.json()


# Main Function
def main():
    # Get authentication token
    token, _ = get_token()

    # Step 1: List access points
    access_points = list_access_point_agents(token)
    print("Available Access Points:")
    for access_point in access_points:
        # Print a compact summary of each access point (ID, Name, Controller)
        print(f"- ID: {access_point['id']} | Name: {access_point.get('name', 'N/A')} | Controller: {access_point.get('controller', 'N/A')}")

    if not access_points:
        # Exit if no access points found
        print("No Access Points found.")
        sys.exit(0)

    # Step 2: Ask if user wants details
    choice = input("\nWould you like to see detailed information for an access points? (yes/no): ").strip().lower()
    if choice == "yes":
        # Ask for the specific access point ID
        chosen_id = input("Enter the ID of the access point you want details for: ").strip()
        details = get_agent_details(token, chosen_id)

        # Print main info
        print("\nDetailed Access Point Information:")
        print(f"- ID: {details.get('id', 'N/A')} | Name: {details.get('name', 'N/A')} | Controller: {details.get('controller', 'N/A')}")

        # Print other fields if they exist
        for field in ["overTheAirName", "modifiedBy", "macAddress", "locationId"]:
            value = details.get(field)
            if value is not None:
                print(f"  {field}: {value}")

        # Print BSSIDs if present
        bssids = details.get("bssids", [])
        if bssids:
            print("  bssids:")
            for b in bssids:
                print(f"    - ID: {b.get('id', 'N/A')} | BSSID: {b.get('bssid', 'N/A')} | Band: {b.get('band', 'N/A')}")
    else:
        # User chose not to fetch detailed info
        print("Exiting without fetching details.")

if __name__ == "__main__":
    main()
