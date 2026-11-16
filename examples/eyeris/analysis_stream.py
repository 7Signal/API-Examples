# This script demonstrates how to consume a streaming Eyeris analysis.
# It shows how to:
#  - Open a streaming request so text arrives as it is generated
#  - Read Server-Sent Events frame by frame, telling answer text apart from named events
#  - Report a stream that ends early, because the text received up to then is incomplete
#  - Capture the identifiers Eyeris returns as response headers
#
# This endpoint takes a different request body from the request-and-poll endpoint:
# promptTypeKey plus an inputData object whose shape depends on the prompt type,
# rather than explicit agentId/type/from/to fields. Both known prompt types take an
# agent time-series query (see build_input_data). See client_analysis.py for the
# polling approach.

import json
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
#
# This is deliberately laxer than client_analysis.py, which rejects an unknown `type`
# outright: there, the specification does define an enum, so an unlisted value is known
# to be invalid. Here it isn't, so refusing one would block input the API may accept.
#
# Each known prompt type reads an agent time-series query as its inputData; these are
# the metrics its analysis looks at.
PROMPT_TYPE_METRICS = {
    "WIFI_CONGESTION_ANALYSIS": ["CONGESTION", "CHANNEL_UTILIZATION", "CLIENT_COUNT", "SIGNAL_STRENGTH", "SEVEN_MCS"],
    "WIFI_COVERAGE_ANALYSIS": ["COVERAGE", "SIGNAL_STRENGTH", "BEST_NEIGHBOR_SIGNAL_STRENGTH", "SEVEN_MCS"],
}
KNOWN_PROMPT_TYPES = list(PROMPT_TYPE_METRICS)

# Metrics sent for a prompt type this script doesn't know
DEFAULT_METRICS = sorted({m for metrics in PROMPT_TYPE_METRICS.values() for m in metrics})

# Server-Sent Events fields. Each frame ends with a blank line; a frame with no
# "event:" field carries answer text, and a named frame carries a JSON status.
SSE_DATA_PREFIX = "data:"
SSE_EVENT_PREFIX = "event:"


class StreamEndedEarly(Exception):
    # Raised when Eyeris stops the analysis after the stream has started. The
    # status code was already 200 by then, so the failure arrives as an "error"
    # event instead, and the text received before it is incomplete.
    def __init__(self, reason, partial_text):
        super().__init__(f"Eyeris stream ended early: {reason}")
        self.reason = reason
        self.partial_text = partial_text


def read_sse_events(response):
    # Groups the stream's lines into (event name, data) pairs. A frame's data
    # lines are joined with newlines, nothing after the colon is trimmed (Eyeris
    # writes "data:" with no space, so a leading space belongs to the text), and
    # comment lines such as ":keepalive" are skipped.
    event_name = None
    data_lines = []

    for line in response.iter_lines(decode_unicode=True):
        if line:
            if line.startswith(SSE_DATA_PREFIX):
                data_lines.append(line[len(SSE_DATA_PREFIX):])
            elif line.startswith(SSE_EVENT_PREFIX):
                event_name = line[len(SSE_EVENT_PREFIX):].strip()
            continue

        if data_lines:
            yield event_name, "\n".join(data_lines)
        event_name = None
        data_lines = []

    if data_lines:
        yield event_name, "\n".join(data_lines)


def error_reason(data):
    # "timeout" when the analysis ran out of time, "failed" for anything else
    try:
        reason = json.loads(data).get("reason")
    except (ValueError, AttributeError):
        reason = None
    return "timeout" if reason == "timeout" else "failed"


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
    # assembled text once the stream closes, or raises StreamEndedEarly with the
    # partial text if Eyeris stopped the analysis part way through.
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
    ended_early_reason = None

    try:
        # stream=True is essential. Without it the response body is buffered in full
        # before being handed back, which defeats the point of a streaming endpoint.
        with requests.post(url, headers=headers, json=payload, stream=True) as response:
            response.raise_for_status()
            log_stream_identifiers(response)

            for event_name, data in read_sse_events(response):
                if event_name in (None, "message"):
                    chunks.append(data)
                    logging.info(data)
                elif event_name == "progress":
                    # Sent once the model has been called; a cached analysis skips it
                    logging.info("Eyeris is generating the analysis...")
                elif event_name == "error":
                    ended_early_reason = error_reason(data)
                # Other named events are status updates, never answer text, so skip them
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    text = "".join(chunks)

    if ended_early_reason is not None:
        raise StreamEndedEarly(ended_early_reason, text)

    if not chunks:
        logging.info("No analysis text was streamed back.")

    return text


def build_input_data(prompt_type_key, agent_id, from_ms, to_ms):
    # The known prompt types read an agent time-series query: one agent's per-minute
    # averages, split by the BSSID it was connected to. from/to are epoch-millisecond
    # numbers, and the agent goes in deviceIds.
    return {
        "groupByDimension": "BSSID",
        "from": from_ms,
        "to": to_ms,
        "timeBucket": "ONE_MIN",
        "aggregateFunctions": ["AVG"],
        "metrics": PROMPT_TYPE_METRICS.get(prompt_type_key, DEFAULT_METRICS),
        "deviceIds": [agent_id],
    }


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

    # Step 2: Stream the analysis
    input_data = build_input_data(prompt_type_key, agent_id, from_ms, to_ms)

    logging.info("===== EYERIS ANALYSIS (streaming) =====")
    try:
        stream_analysis(token, prompt_type_key, input_data)
    except StreamEndedEarly as ended_early:
        logging.error(f"The analysis stopped early ({ended_early.reason}); "
                      "the text above is incomplete.")
        sys.exit(1)


if __name__ == "__main__":
    main()
