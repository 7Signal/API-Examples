# This script demonstrates how to make an authenticated API call to the numeric endpoint.
# It shows how to:
#  - Make a GET request to the /time-series/agents/numeric/{groupByDimension} endpoint with query parameters
#  - Log aggregated metric data and time series details
#  - Handle cases where the response structure may vary or be missing expected keys

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
FROM = os.getenv("FROM")
TO = os.getenv("TO")
API_HOST = os.getenv("API_HOST", "api-v2-integration.dev.7signal.com")

# Error response if environment variables are missing
if not FROM:
    raise EnvironmentError("The FROM environment variable may not be set. Ex: 1755537748000 (must be in milliseconds).")

if not TO:
    raise EnvironmentError("The TO environment variable may not be set. Ex: 1755537748000 (must be in milliseconds).")

# Hardcoded values
METRICS = ["EXPERIENCE_SCORE"]
groupByDimension = "locationId"
TIME_BUCKET = "2_HOUR"
AGGREGATE_FUNCTION = ["AVG"]

# Construct numeric endpoint URL
url = f"https://{API_HOST}/time-series/agents/numeric/{groupByDimension}"


def fetch_numeric_metrics(token):
    # Fetches aggregated metric data from the numeric endpoint

    # HTTP headers with authorization
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Query parameters for the GET request
    params = {
        "from": FROM,
        "to": TO,
        "metrics": METRICS,
        "aggregateFunctions": AGGREGATE_FUNCTION,
        "timeBucket": TIME_BUCKET
    }

    # Log the request details
    logging.info(f"GET {url} with params: {params}")

    try:
        # Send GET request to the numeric endpoint
        response = requests.get(url, headers=headers, params=params)
        # Raise exception for HTTP error codes
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Log summary of numeric metric data
        log_numeric_summary(data)

    except requests.exceptions.HTTPError as e:
        # Log HTTP errors
        logging.error(f"HTTP error occurred: {e}")
        logging.error(f"Response content: {response.text}")
    except Exception as e:
        # Log any other unexpected errors
        logging.error(f"Unexpected error occurred: {e}")


def log_numeric_summary(data):
    #  Logs a readable summary of numeric metric data from the numeric endpoint

    # Extract 'results' list from JSON
    results = data.get("results", [])

    if not results:
        logging.warning("No results found in response.")
        return

    logging.info(f"Total Result Groups: {len(results)}")

    for result in results:
        location_id = result.get("locationId", "N/A")
        metric_aggregates = result.get("metricAggregates", [])

        logging.info(f"LocationId: {location_id}")
        for agg in metric_aggregates:
            # Extract main metric info
            metric = agg.get("metric", "N/A")
            avg = agg.get("avg", "N/A")
            threshold = agg.get("threshold", "N/A")

            logging.info(f"  Metric: {metric} | Avg: {avg} | Threshold: {threshold}")

            # Log time series details if present
            time_series = agg.get("timeSeries", [])
            if time_series:
                logging.info("  Time Series:")
                for point in time_series:
                    ts = point.get("ts")
                    ts_avg = point.get("avg", "N/A")
                    logging.info(f"    - Timestamp: {ts} | Avg: {ts_avg}")
            else:
                logging.info("  No time series data available.")



def main():
    # # Main function to get authentication token, and call numeric metrics API
    token, _ = get_token()
    fetch_numeric_metrics(token)

if __name__ == "__main__":
    main()
