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

# Fetch a list of API keys
def list_api_keys(token):
    url = f"https://{API_HOST}/apikeys"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    # GET request to /apikeys endpoint
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    # Returns a list of API key dictionaries from the 'results' key.
    return response.json().get("results", [])


# Fetch detailed information about a specific API key by ID
def get_api_key_details(token, apiKeyId):
    url = f"https://{API_HOST}/apikeys/{apiKeyId}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    # GET request to /apikeys/{apiKeyId}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    # Returns the full API key details as a dictionary.
    return response.json()


# Main Function
def main():
    # Get authentication token
    token, _ = get_token()

    # Step 1: List API keys
    api_keys = list_api_keys(token)
    print("Available API Keys:")
    for key in api_keys:
        # Show only a compact summary (ID, description, createdBy)
        print(f"- ID: {key['id']} | Description: {key.get('description', 'N/A')} | CreatedBy: {key.get('createdBy', 'N/A')}")

    if not api_keys:
        # Exit script if no API keys exist
        print("No API keys found.")
        sys.exit(0)

    # Step 2: Ask if user wants details
    choice = input("\nWould you like to see detailed information for an API key? (yes/no): ").strip().lower()
    if choice == "yes":
        chosen_id = input("Enter the ID of the API key you want details for: ").strip()
        details = get_api_key_details(token, chosen_id)

        # Print main info
        print("\nDetailed API Key Information:")
        print(f"- ID: {details.get('id', 'N/A')} | Description: {details.get('description', 'N/A')} | CreatedBy: {details.get('createdBy', 'N/A')}")

        # Print other fields if they exist
        for field in ["apiKey", "createdAt", "isSystem", "clientSecret"]:
            value = details.get(field)
            if value is not None:
                print(f"  {field}: {value}")

        # Print organization/group IDs
        if "organization" in details and details["organization"].get("id"):
            print(f"  organizationId: {details['organization']['id']}")
        if "group" in details and details["group"].get("id"):
            print(f"  groupId: {details['group']['id']}")

        # Print permissions if present
        permissions = details.get("permissions", [])
        if permissions:
            print("  permissions:")
            for p in permissions:
                print(f"    - ID: {p.get('id', 'N/A')} | Key: {p.get('key', 'N/A')} | Description: {p.get('description', 'N/A')} | Public: {p.get('isPublic', 'N/A')}")
    else:
        # User chose not to see details
        print("Exiting without fetching details.")


if __name__ == "__main__":
    main()
