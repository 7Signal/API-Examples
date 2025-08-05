import os
import requests
import sys
import logging

# Make sure we can import get_token
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# # Define API Host and Agent ID from environment
API_HOST = os.getenv("API_HOST")
AGENT_ID = os.getenv("AGENT_ID")

# Check that required environment variables are set, otherwise raise errors
if not API_HOST:
    raise EnvironmentError("API_HOST environment variable not set")
if not AGENT_ID:
    raise EnvironmentError("AGENT_ID environment variable not set")

# Construct the full API URL for fetching the agent by its ID
agent_url = f"https://{API_HOST}/eyes/agents/{AGENT_ID}"

def fetch_agent_by_id(token):
    # This function fetches the agent info from the /eyes/agents/{agentId} endpoint using the token
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        # send the GET request to the agents endpoint
        response = requests.get(agent_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # calls the helper function to log the agent details
        log_agent_summary(data)

    # Log HTTP error details and response body for troubleshooting
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    # Log any other unexpected exceptions
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

def log_agent_summary(data):
    # Logs all key-value pairs from the agent data dictionary.
    logging.info("===== Agent Summary =====")
    for key, value in data.items():
        logging.info(f"{key}: {value}")

def main():
    # fetches the token from the auth_utils.py file
    token, _ = get_token()
    # calls the API using that token
    fetch_agent_by_id(token)

if __name__ == "__main__":
    main()
