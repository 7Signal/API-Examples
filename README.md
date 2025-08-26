# API-Examples
Example Code for 7SIGNAL's API

## Getting an API KEY
1. https://start-dev.7signal.com/
2. Click Users
3. Click API Keys tab 
4. Click Add button
5. Choose your Organization, Role, and Sapphire Group
6. Add a description if needed
7. Submit

# MAC
## Set up Python
1. https://www.python.org/downloads/
2. Download python 
3. Verify version
    `python --version`

## Install Dependencies
1. Install the Requests library
    `pip install requests`

## Configure Settings
These files require 3 main environment variables
1. `export API_KEY=“your-client-id”`
2. `export API_SECRET=“your-client-secret”`
3. `export API_HOST="api-v2-integration.dev.7signal.com"`

Eyes Endpoint
    `export AGENT_ID="your-agent-id"`

KPI Endpoint
    `export KPI_CODE="your-kpi-code"`

Packet Capture Endpoint
    `export SENSOR_ID="your-sensor-id"`

Time Series Endpoint
    `export TO="your-current-epoch-time-in-milliseconds"`
    `export FROM="your-epoch-time-you’re-measuring-from-in-milliseconds"`

## Run the Python Script
ex: API Keys
    `cd examples/api_keys`
    `python3 get_apikeys.py`

ex: Topologies
    `cd topologies`
    `python3 topologyAgents.py`

# Windows
If you are using Powershell:
## Configure Settings
These files require 3 main environment variables
1. `$env:API_KEY="your_api_key_here"`
2. `$env:API_SECRET="your_api_secret_here"`
3. `$env:API_HOST="api-v2-integration.dev.7signal.com"`

Eyes Endpoint
    `$env:AGENT_ID="your-agent-id"`

KPI Endpoint
    `$env:KPI_CODE="your-kpi-code"`

Packet Capture Endpoint
    `$env:SENSOR_ID="your-sensor-id"`

Time Series Endpoint
    `$env:TO="your-current-epoch-time-in-milliseconds"`
    `$env:FROM="your-epoch-time-you’re-measuring-from-in-milliseconds"`
