# This script demonstrates how to license Eyes Agents in bulk using a CSV file.
# It shows how to:
#  - Fetch all Eyes Agents from the /eyes/agents endpoint
#  - Read a list of hostnames from a CSV file
#  - Match agents by hostname using a dictionary lookup for efficiency
#  - Send a PATCH request to update each matched agent's "isLicensed" field to True

# Example usage:
#   python3 csv_licensing.py agents.csv

import os
import csv
import logging
import requests
import sys

# Make sure we can import get_token
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

# Fetch all agents from the Eyes API
def fetch_agents(token):
    url = f"https://{API_HOST}/eyes/agents"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        # GET request to fetch agents
        resp = requests.get(url, headers=headers)
        # Raise error if HTTP request fails
        resp.raise_for_status()
        # Return list of agents
        return resp.json().get("results", [])
    except Exception as e:
        logging.error(f"Failed to fetch agents: {e}")
        return []

# License a specific agent by ID
def license_agent(token, agent_id):
    url = f"https://{API_HOST}/eyes/agents/{agent_id}"

    headers = {
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"
    }

    # Set licensing flag to True
    payload = {
        "isLicensed": True
    }

    try:
        # PATCH request
        resp = requests.patch(url, headers=headers, json=payload)
        # Raise error if request fails
        resp.raise_for_status()
        # Log success
        logging.info(f"Licensed agent {agent_id} successfully")
    except Exception as e:
        # Log failure
        logging.error(f"Failed to license agent {agent_id}: {e}")

# Main function that runs the script
def main():
    # Get API token
    token, _ = get_token()

    # CSV file provided as a command-line prompt
    if len(sys.argv) < 2:
        logging.error("Usage: python3 csv_licensing.py <csv_file>")
        return
    csv_file = sys.argv[1]

    # Read CSV file 
    try:
        with open(csv_file) as f:
            csv_rows = csv.DictReader(f)
            # rows are dictionaries with a "hostname" column
            rows = list(csv_rows)
    except Exception as e:
        logging.error(f"Error reading CSV {csv_file}: {e}")
        return

    # Fetch all agents from API
    agents = fetch_agents(token)

  # Build a lookup dictionary
    agents_dict = { (a.get("name") or "").lower(): a for a in agents }

    # Loop over each row in the CSV
    for row in rows:
        hostname = (row.get("hostname") or "").strip().lower()
        if not hostname:
            # Skip empty rows
            continue

        # Lookup agent directly
        match = agents_dict.get(hostname)
        if match:
            # License the matched agent
            license_agent(token, match["id"])
        else:
            # Warn if no agent found
            logging.warning(f"No match for hostname: {hostname}")

if __name__ == "__main__":
    main()
