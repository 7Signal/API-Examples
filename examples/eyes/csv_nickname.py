# This script demonstrates how to update the "nickname" of Eyes Agents in bulk using a CSV file.
# It shows how to:
#  - Fetch all Eyes Agents from the /eyes/agents endpoint
#  - Read hostnames and nicknames from a CSV file (passed as a command-line argument)
#  - Match agents by hostname using a dictionary lookup
#  - Send a PATCH request to update each matched agent's "nickname"

# Example usage:
#   python3 csv_nickname.py agents.csv

import os
import csv
import logging
import requests
import sys

# Make sure we can import get_token
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# API host url
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

# Fetch all Eyes Agents from API
def fetch_agents(token):
    url = f"https://{API_HOST}/eyes/agents"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # GET request to fetch agents
        resp = requests.get(url, headers=headers)
        # Raise error if status is not 200
        resp.raise_for_status()
        # Return list of agents
        return resp.json().get("results", [])
    except Exception as e:
        logging.error(f"Failed to fetch agents: {e}")
        return []

# Update nickname for a specific agent
def update_nickname(token, agent_id, nickname):
    url = f"https://{API_HOST}/eyes/agents/{agent_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Data to update
    payload = {
        "nickname": nickname
        }

    try:
        # Send a PATCH request to update the agent's nickname
        resp = requests.patch(url, headers=headers, json=payload)
        # Raise error if response is not OK
        resp.raise_for_status()
        # Log success
        logging.info(f"Updated agent {agent_id} nickname -> {nickname}")
    except Exception as e:
        # Log failure
        logging.error(f"Failed to update nickname for agent {agent_id}: {e}")

# Main function that runs the script
def main():
    # Get authentication token
    token, _ = get_token()

    # CSV file provided as a command-line prompt
    if len(sys.argv) < 2:
        logging.error("Usage: python3 csv_nickname.py <csv_file>")
        return
    csv_file = sys.argv[1]

    # Read CSV file with columns: hostname,nickname
    try:
        with open(csv_file) as f:
            # Each row is a dict: hostname,nickname
            rows = list(csv.DictReader(f))  # Each row is a dict: hostname,nickname
    except Exception as e:
        logging.error(f"Error reading CSV {csv_file}: {e}")
        return

    # Get current agents from the API
    agents = fetch_agents(token)

    # Build dictionary for quick lookup
    agents_dict = {(a.get("name") or "").lower(): a for a in agents}

    # Loop through CSV rows
    for row in rows:
        hostname = (row.get("hostname") or "").strip().lower()
        nickname = (row.get("nickname") or "").strip()

        # Skip if hostname or nickname missing
        if not hostname or not nickname:
            continue 

        # Lookup agent directly
        match = agents_dict.get(hostname)
        if match:
            # If match found, update nickname
            update_nickname(token, match["id"], nickname)
        else:
            # If no match, log a warning
            logging.warning(f"No match for hostname: {hostname}")
        
if __name__ == "__main__":
    main()
