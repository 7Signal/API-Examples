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

# Fetch a list of access point agents
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

# Fetch detailed information about a specific agent by ID
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

    # Step 1: List agents
    agents = list_access_point_agents(token)
    print("Available Access Point Agents:")
    for agent in agents:
        # Print a compact summary of each agent (ID, Name, Controller)
        print(f"- ID: {agent['id']} | Name: {agent.get('name', 'N/A')} | Controller: {agent.get('controller', 'N/A')}")

    if not agents:
        # Exit if no agents found
        print("No agents found.")
        sys.exit(0)

    # Step 2: Ask if user wants details
    choice = input("\nWould you like to see detailed information for an agent? (yes/no): ").strip().lower()
    if choice == "yes":
        # Ask for the specific agent ID
        chosen_id = input("Enter the ID of the agent you want details for: ").strip()
        details = get_agent_details(token, chosen_id)

        # Print main info
        print("\nDetailed Agent Information:")
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
