# This script demonstrates how to consume a streaming Eyeris analysis.
# It shows how to:
#  - Open a streaming request so text arrives as it is generated
#  - Read Server-Sent Events line by line and strip the "data:" prefix
#  - Capture the identifiers Eyeris returns as response headers
#
# This endpoint takes a different request body from the request-and-poll endpoint:
# promptTypeKey plus a free-form inputData object, rather than explicit
# agentId/type/from/to fields. See client_analysis.py for the polling approach.

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

# The specification puts no fixed list on promptTypeKey, so these are the keys known to
# work rather than the only ones accepted. Anything else is passed through with a warning.
KNOWN_PROMPT_TYPES = ["ROAMING", "CONGESTION", "COVERAGE", "INTERFERENCE"]

# Server-Sent Events prefix each payload line with this marker
SSE_DATA_PREFIX = "data:"


def log_stream_identifiers(response):
    # Eyeris returns the analysis identifiers as response headers on the stream,
    # rather than in the body. Keep them if you want to re-read the analysis later.
    headers = response.headers or {}

    logging.info("----- Eyeris identifiers -----")
    logging.info(f"  Request id      : {headers.get('Eyeris-Request-Id', 'N/A')}")
    logging.info(f"  Request queue id: {headers.get('Eyeris-Request-Queue-Id', 'N/A')}")
    logging.info(f"  Response id     : {headers.get('Eyeris-Response-Id', 'N/A')}")
    logging.info("------------------------------")


def stream_analysis(token, prompt_type_key, input_data):
    # Requests an analysis and logs the text as it streams back. Returns the
    # assembled text once the stream closes.
    url = f"https://{API_HOST}/eyeris/analysis/stream"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "promptTypeKey": prompt_type_key,
        "inputData": input_data,
    }

    chunks = []

    try:
        # stream=True is essential. Without it the response body is buffered in full
        # before being handed back, which defeats the point of a streaming endpoint.
        with requests.post(url, headers=headers, json=payload, stream=True) as response:
            response.raise_for_status()
            log_stream_identifiers(response)

            for line in response.iter_lines(decode_unicode=True):
                # Keep-alive lines arrive empty and carry no payload
                if not line:
                    continue

                if line.startswith(SSE_DATA_PREFIX):
                    text = line[len(SSE_DATA_PREFIX):]
                    chunks.append(text)
                    logging.info(text)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    if not chunks:
        logging.info("No analysis text was streamed back.")
        return ""

    return "\n".join(chunks)


def main():
    # Ask the user for the agent to analyse
    agent_id = input("Enter the AGENT ID (UUID): ").strip()
    if not agent_id:
        logging.error("agent_id cannot be empty.")
        sys.exit(1)

    # Ask which kind of analysis to run
    logging.info(f"Known prompt types: {', '.join(KNOWN_PROMPT_TYPES)}")
    prompt_type_key = input("Enter the PROMPT TYPE: ").strip().upper()
    if not prompt_type_key:
        logging.error("Prompt type cannot be empty.")
        sys.exit(1)

    if prompt_type_key not in KNOWN_PROMPT_TYPES:
        logging.warning(f"{prompt_type_key} is not one of the known prompt types "
                        f"({', '.join(KNOWN_PROMPT_TYPES)}), but the API does not "
                        "restrict this field - sending it anyway.")

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

    # Step 2: Stream the analysis. inputData is free-form, so the fields below
    # mirror what the request-and-poll endpoint accepts.
    input_data = {
        "agentId": agent_id,
        "from": str(from_ms),
        "to": str(to_ms),
    }

    logging.info("===== EYERIS ANALYSIS (streaming) =====")
    stream_analysis(token, prompt_type_key, input_data)


if __name__ == "__main__":
    main()
