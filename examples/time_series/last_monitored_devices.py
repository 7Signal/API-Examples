# This script demonstrates how to generate SLA charts for recently monitored devices.
# It shows how to:
#  - Fetch the last 3 monitored devices from the Eyes Agents API
#  - Query the /time-series/agents/numeric/{groupByDimension} endpoint for SLA metrics
#  - Generate charts (0–100% scale) for SEVEN_MCS, ROAMING, COVERAGE, CONGESTION, and INTERFERENCE
#  - Embed the charts as base64 images into a single HTML report for easy viewing

import os
import sys
import logging
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import io
import base64

# Allow importing get_token from two levels up
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Load environment variables and constants
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")
METRICS = [
    "APPLICATION_CONNECTIVITY",
    "NETWORK_CONNECTIVITY",
    "ROAMING",
    "COVERAGE",
    "CONGESTION",
    "INTERFERENCE",
]
TIME_BUCKET = "10_MIN"
AGGREGATE_FUNCTION = ["AVG"]
groupByDimension = "deviceId"

# Fetches the last monitored devices from the Eyes Agents API.
def fetch_devices(token, limit=3):
    # Construct the API URL to fetch Eyes Agents
    url = f"https://{API_HOST}/eyes/agents?limit={limit}&sort=lastTestSeen&order=desc"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    # Send GET request to the Eyes Agents endpoint
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # Devices may be listed under the "results" key OR under "agents".
    devices = data.get("results") or data.get("agents") or []
    # If no devices are found, log an error to alert the user
    if not devices:
        logging.error("No devices found in response.")
    # Return only up to the requested number of devices
    return devices[:limit]


# Fetches SLA-related numeric metrics for a single device over a time window.
def fetch_time_series(token, device_id, from_time, to_time):
    # Construct numeric endpoint URL
    url = f"https://{API_HOST}/time-series/agents/numeric/{groupByDimension}"
    params = {
    "from": from_time,
    "to": to_time,
    "timeBucket": TIME_BUCKET,
    "aggregateFunctions": AGGREGATE_FUNCTION,
    "metrics": ",".join(METRICS),
    "deviceId": device_id,
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Send GET request to numeric endpoint
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()

    # Returns a list of aggregated metric results with time series points.
    return resp.json().get("results", [])


# Creates a chart for one metric and returns it as a base64-encoded PNG.
def plot_chart_base64(time_series, metric):
    # Warn and exit if no data points are provided
    if not time_series:
        logging.warning(f"No data for {metric}")
        return None

    # Sort the data points by timestamp to ensure proper plotting
    time_series.sort(key=lambda x: x["ts"])
    # Convert timestamps from milliseconds to datetime objects (UTC)
    times = [datetime.utcfromtimestamp(p["ts"] / 1000) for p in time_series]
    # Extract SLA values and convert decimals (0–1) into percentages (0–100)
    values = [p.get("avg", 0) * 100 for p in time_series]

    # Create the chart
    plt.figure(figsize=(6, 3))
    plt.plot(times, values, marker="o", linestyle="-")
    plt.title(f"{metric} SLA % (last 8 hours)")
    plt.ylim(0, 100)
    plt.xlabel("Time")
    plt.ylabel("SLA %")
    plt.xticks(fontsize=8)  # Smaller font for readability
    plt.grid(True)
    plt.tight_layout()

    # Save chart into memory buffer as PNG
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)

    # Convert the PNG buffer to a base64-encoded string for embedding in HTML
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    # Returns a base64 string representing the PNG image.
    return img_base64


# Builds an HTML report containing charts for each device and metric.
def build_html_report(devices_charts, output_file="sla_report.html"):
    # Open the output HTML file for writing
    with open(output_file, "w") as f:
        # Write the HTML head and main heading
        f.write("<html><head><title>Device SLA Report</title></head><body>\n")
        f.write("<h1>Device SLA Report (Last 8 Hours)</h1>\n")

        # Iterate through each device in the provided chart dictionary
        for device_name, charts in devices_charts.items():
            # Write the device name as a subheading
            f.write(f"<h2>{device_name}</h2>\n")
            # Only include charts that have data
            for metric, img_base64 in charts.items():
                if img_base64:
                    # Write the metric title
                    f.write(f"<h4>{metric}</h4>\n")
                    # Embed the chart as a base64 image, set width for readability
                    f.write(f'<img src="data:image/png;base64,{img_base64}" width="500"><br>\n')
            f.write("<hr>\n")
        # Close the HTML tags
        f.write("</body></html>")
    logging.info(f"Report generated: {output_file}")


# Main fucntion
def main():
    # Authenticate and get API token
    token, _ = get_token()
    logging.info("Fetching last 3 monitored devices...")
    devices = fetch_devices(token, limit=3)

    # If no devices are returned, exit the function
    if not devices:
        return

    # Define 8-hour window ending now
    to_time = int(datetime.utcnow().timestamp() * 1000)
    from_time = int((datetime.utcnow() - timedelta(hours=8)).timestamp() * 1000)

    # Dictionary to hold chart images for each device
    devices_charts = {}

    # Loop through each device to fetch metrics and generate charts
    for device in devices:
        device_id = device.get("id")
        device_name = device.get("name", f"Device {device_id}")
        logging.info(f"Fetching SLA metrics for device: {device_name} ({device_id})")

        # Get numeric SLA metrics for this device
        results = fetch_time_series(token, device_id, from_time, to_time)

        # Generate charts for each metric
        charts = {}
        for res in results:
            for agg in res.get("metricAggregates", []):
                metric = agg.get("metric")
                # Create a chart and encode it in base64
                img_base64 = plot_chart_base64(agg.get("timeSeries", []), metric)
                charts[metric] = img_base64

        # Store charts under the device's name
        devices_charts[f"{device_name} ({device_id})"] = charts

    # Store charts under the device's name
    build_html_report(devices_charts)


if __name__ == "__main__":
    main()
