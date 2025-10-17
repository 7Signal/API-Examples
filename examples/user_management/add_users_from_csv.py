# This script demonstrates how to create new users in bulk from a CSV file.
# It shows how to:
#  - Read user data from a CSV file with first_name, last_name, and email columns
#  - Fetch the "Reporter" role UUID from the /roles endpoint
#  - Send POST requests to create each user with the Reporter role

# Example usage:
#   python3 add_users_from_csv.py users.csv

import os
import csv
import logging
import requests
import sys

# Make sure we can import get_token
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

def fetch_reporter_role_id(token):
    # Fetch the Reporter role UUID from the /roles endpoint
    # If you wish to create users with more privledge you can
    # search for roles of:
    #   customer:reporter (read only)
    #   customer:configurator (ability to create test profiles, modify settings, etc)
    #   customer:organization-admin (ability to modify all, including users and permissions)

    url = f"https://{API_HOST}/roles"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Find the Reporter role (try multiple possible keys)
        for role in data.get("results", []):
            role_key = role.get("key", "")
            if role_key in ["Reporter", "customer:reporter", "reporter"]:
                logging.info(f"Found Reporter role with ID: {role.get('id')}, key: {role_key}")
                return role.get("id")
        
        logging.error("Reporter role not found")
        return None
        
    except Exception as e:
        logging.error(f"Failed to fetch roles: {e}")
        return None

def fetch_organization_id(token):
    # Fetch your organization ID from the /organizations endpoint
    # This is required when creating new users. Most users will have
    # only one possible organization.

    url = f"https://{API_HOST}/organizations"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Get the first organization
        results = data.get("results", [])
        if results:
            org_id = results[0].get("id")
            org_name = results[0].get("name")
            logging.info(f"Found organization: {org_name} with ID: {org_id}")
            return org_id
        
        logging.error("No organizations found")
        return None
        
    except Exception as e:
        logging.error(f"Failed to fetch organizations: {e}")
        return None

def create_user(token, first_name, last_name, email, role_id, organization_id):
    # Create a new user via POST to /users endpoint
    url = f"https://{API_HOST}/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "organizationId": organization_id,
        "role": {
            "id": role_id
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Created user: {first_name} {last_name} ({email})")
        return True
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to create user {email}: HTTP {response.status_code}")
        logging.error(f"Response: {response.text}")
        return False
    except Exception as e:
        logging.error(f"Failed to create user {email}: {e}")
        return False

def main():
    # Get API token
    token, _ = get_token()
    
    # CSV file provided as command-line argument
    if len(sys.argv) < 2:
        logging.error("Usage: python3 add_users_from_csv.py <csv_file>")
        return
    csv_file = sys.argv[1]
    
    # Fetch Reporter role ID
    role_id = fetch_reporter_role_id(token)
    if not role_id:
        logging.error("Cannot proceed without Reporter role ID")
        return
    
    # Fetch Organization ID
    organization_id = fetch_organization_id(token)
    if not organization_id:
        logging.error("Cannot proceed without Organization ID")
        return
    
    # Read CSV file
    try:
        with open(csv_file) as f:
            csv_rows = csv.DictReader(f)
            rows = list(csv_rows)
    except Exception as e:
        logging.error(f"Error reading CSV {csv_file}: {e}")
        return
    
    # Process each row
    success_count = 0
    for row in rows:
        first_name = row.get("first_name", "").strip()
        last_name = row.get("last_name", "").strip()
        email = row.get("email", "").strip()
        
        if not all([first_name, last_name, email]):
            logging.warning(f"Skipping incomplete row: {row}")
            continue
        
        if create_user(token, first_name, last_name, email, role_id, organization_id):
            success_count += 1
    
    logging.info(f"Successfully created {success_count} users from {len(rows)} rows")

if __name__ == "__main__":
    main()
