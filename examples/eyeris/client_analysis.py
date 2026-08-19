# This script demonstrates how to request an Eyeris AI analysis for a 7SIGNAL agent.
# It shows how to:
#  - Start an analysis and capture the identifiers needed to retrieve it
#  - Poll for the result, treating a 404 as "not ready yet"
#  - Display the returned analysis text
#
# Eyeris returns a plain-language explanation of an agent's Wi-Fi experience rather
# than raw metrics. Analysis takes time to generate, so the API accepts the request
# immediately and you poll for the result.
#
# For an interactive alternative that shows text as it is generated, see
# analysis_stream.py in this directory.

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

# Unlike the alerting endpoints, these enum values must be UPPERCASE.
VALID_ANALYSIS_TYPES = ["ROAMING", "CONGESTION", "COVERAGE", "INTERFERENCE"]

# How long to wait between polls, and how many times to try before giving up
POLL_INTERVAL_SECONDS = 5
POLL_RETRIES = 60

# get_analysis returns this instead of a result when the request itself failed, so
# polling can stop rather than mistaking a failure for "still working".
ANALYSIS_FAILED = "ANALYSIS_FAILED"


def start_analysis(token, agent_id, analysis_type, from_ms, to_ms):
    # Requests a new analysis. Returns the requestId, requestQueueId, and responseId
    # needed to retrieve the result later.
    if analysis_type not in VALID_ANALYSIS_TYPES:
        logging.error(f"Unsupported analysis type: {analysis_type}")
        logging.error(f"Valid values are: {', '.join(VALID_ANALYSIS_TYPES)}")
        return None

    url = f"https://{API_HOST}/eyeris/agents/client-analysis"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # The API expects the epoch-millisecond bounds as strings, not numbers
    payload = {
        "agentId": agent_id,
        "type": analysis_type,
        "from": str(from_ms),
        "to": str(to_ms),
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        started = response.json()
        logging.info(f"{analysis_type} analysis requested for agent {agent_id}.")
        logging.info(f"  Request id      : {started.get('requestId')}")
        logging.info(f"  Request queue id: {started.get('requestQueueId')}")
        return started
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def get_analysis(token, request_id, request_queue_id, response_id=None):
    # Fetches an analysis result. There are three outcomes:
    #   - a result dict   : the analysis is ready
    #   - None            : not ready yet, which the API signals with a 404
    #   - ANALYSIS_FAILED : the call itself failed, so there is no point retrying
    url = f"https://{API_HOST}/eyeris/agents/client-analysis/{request_id}"
    headers = {"Authorization": f"Bearer {token}"}

    # requestQueueId is required even though only requestId appears in the path
    params = {"requestQueueId": request_queue_id}
    if response_id:
        params["responseId"] = response_id

    try:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return ANALYSIS_FAILED


def poll_for_analysis(token, request_id, request_queue_id, response_id=None,
                      interval=POLL_INTERVAL_SECONDS, retries=POLL_RETRIES):
    # Polls until the analysis is ready, the request fails, or the retry ceiling is
    # reached. Stopping on a failure matters: otherwise a rejected request would be
    # retried for the full ceiling while reporting "not ready yet".
    for attempt in range(1, retries + 1):
        result = get_analysis(token, request_id, request_queue_id, response_id)

        if result == ANALYSIS_FAILED:
            logging.error("The analysis request failed; not retrying.")
            return None

        if result is not None:
            return result

        # The last attempt has nothing left to wait for
        if attempt == retries:
            break

        logging.info(f"Analysis not ready yet (attempt {attempt} of {retries}); waiting...")
        time.sleep(interval)

    logging.error("Gave up waiting for the analysis to finish.")
    return None


def display_analysis(result):
    # Logs the analysis text returned by Eyeris.
    logging.info("===== EYERIS ANALYSIS =====")

    if not result:
        logging.info("No analysis text was returned.")
        return

    text = result.get("response")
    if not text:
        logging.info("No analysis text was returned.")
        return

    # The response is Markdown, so log it line by line to keep it readable
    for line in text.splitlines():
        logging.info(line)

    logging.info("-----")
    logging.info(f"Request id : {result.get('requestId', 'N/A')}")
    logging.info(f"Response id: {result.get('responseId', 'N/A')}")


def main():
    # Ask the user for the agent to analyse
    agent_id = input("Enter the AGENT ID (UUID): ").strip()
    if not agent_id:
        logging.error("agent_id cannot be empty.")
        sys.exit(1)

    # Ask which kind of analysis to run
    logging.info(f"Available analysis types: {', '.join(VALID_ANALYSIS_TYPES)}")
    analysis_type = input("Enter the ANALYSIS TYPE: ").strip().upper()
    if analysis_type not in VALID_ANALYSIS_TYPES:
        logging.error(f"Analysis type must be one of: {', '.join(VALID_ANALYSIS_TYPES)}")
        sys.exit(1)

    # Ask for the time range, defaulting to the last two hours
    now_ms = int(time.time() * 1000)
    default_from_ms = now_ms - (2 * 60 * 60 * 1000)

    from_input = input(f"Enter the START time in epoch ms (press Enter for {default_from_ms}): ").strip()
    to_input = input(f"Enter the END time in epoch ms (press Enter for {now_ms}): ").strip()

    try:
        from_ms = int(from_input) if from_input else default_from_ms
        to_ms = int(to_input) if to_input else now_ms
    except ValueError:
        logging.error("Start and end times must be whole numbers of milliseconds.")
        sys.exit(1)

    if from_ms >= to_ms:
        logging.error("The start time must be earlier than the end time.")
        sys.exit(1)

    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Request the analysis
    started = start_analysis(token, agent_id, analysis_type, from_ms, to_ms)
    if not started:
        sys.exit(1)

    # Step 3: Poll until Eyeris has finished generating it
    result = poll_for_analysis(
        token,
        started.get("requestId"),
        started.get("requestQueueId"),
        started.get("responseId"),
    )

    # Step 4: Show the analysis
    if result:
        display_analysis(result)


if __name__ == "__main__":
    main()
