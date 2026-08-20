# API-Examples
Example Code for 7SIGNAL's API

## Getting an API KEY
1. https://start.7signal.com
2. Click Users
3. Click API Keys tab 
4. Click Add button
5. Choose your Organization, Role, and Sapphire Group
6. Add a description if needed
7. Submit

## Set up Python
1. https://www.python.org/downloads/
2. Download python 
3. Verify version
   
    `python --version`

## Install Dependencies
1. Install the Requests library
    
    `pip install requests`

2. For examples/eyes/last_monitored_devices.py

    `pip install matplotlib`

## Logging
By default these scripts will print INFO statements and above. 
To see DEBUG statements set the `LOG_LEVEL=DEBUG` environment variable.

## Windows
### If you are using Command Line:
These files require 2 main environment variables:

```
set API_KEY=your_api_key_here
set API_SECRET=your_api_secret_here
```
### If you are using Powershell:
These files require 2 main environment variables:

```
$env:API_KEY="your_api_key_here"
$env:API_SECRET="your_api_secret_here"
```

## macOS
### Configure Settings
These files require 2 main environment variables:

```
export API_KEY=“your-client-id”
export API_SECRET=“your-client-secret”
```

## Additional Variables
Depending on the script you want to run, you will be asked to set a couple of additional variables:

Eyes Endpoint

    Enter the Agent ID: "your-agent-id"
    

KPI Endpoint
    
    Enter the KPI code: "your-kpi-code"


Packet Capture Endpoint
    
    Enter the SENSOR ID: "your-sensor-id"


Time Series Endpoint
    
    Enter from_time timestamp (milliseconds): "your-epoch-time-you’re-measuring-from-in-milliseconds"
    Enter to_time timestamp (milliseconds): "your-current-epoch-time-in-milliseconds"


Alerting Endpoints

    Enter the ALERT RULE ID: "your-alert-rule-uuid"
    Enter the INCIDENT ID: "your-incident-uuid"


Eyeris Endpoints

    Enter the AGENT ID (UUID): "your-agent-id"
    Enter the ANALYSIS TYPE: "ROAMING, CONGESTION, COVERAGE, or INTERFERENCE"


Sensor Configuration Endpoints

    Enter the TARGET ID (a number): "your-sensor-target-id"
    Enter the NETWORK KEY ID (a number): "your-network-key-id"
    Enter the SERVICE AREA ID (UUID): "your-service-area-id"


On-Demand Test Metadata

    Enter the SENSOR ID: "your-sensor-id"
    Enter the TEST TYPE: "SPEEDTEST, PING, TRACEROUTE, ..."


Getting current epoch time using Python:

    import time

    # Current time in milliseconds
    current_time_ms = int(time.time() * 1000)
    print("Current time:", current_time_ms)

    # 1 hour ago
    one_hour_ms = current_time_ms - (1 * 60 * 60 * 1000)
    print("1 hour ago:", one_hour_ms)

    # 24 hours ago
    twenty_four_hours_ms = current_time_ms - (24 * 60 * 60 * 1000)
    print("24 hours ago:", twenty_four_hours_ms)


## Run the Python Script
ex: Time Series - Last Monitored Devices

    
    cd examples/time_series
    python last_monitored_devices.py
    
    # For macOS
    open sla_report.html

    # For Windows
    start sla_report.html


ex: Eyes - CSV Licensing


    cd examples/eyes
    python csv_licensing.py agents.csv


ex: Eyes - CSV Modifying Nickname


    cd examples/eyes
    python csv_nickname.py agents.csv


ex: API Keys
    

    cd examples/api_keys
    python get_apikeys.py


ex: Topologies
    

    cd topologies
    python topologyAgents.py


ex: Alerting - Alert Rules


    cd examples/alerting
    python flow_alert_rules.py


ex: Eyeris - Client Analysis


    cd examples/eyeris
    python client_analysis.py


## API Documentation

Reference documentation for the endpoints these examples call is in the [docs](docs/README.md)
directory. See [What's New](docs/WHATS-NEW.md) for recently documented endpoints.

> **Note:** Some examples change live configuration — creating or deleting alert rules,
> sensor targets, and network keys, or stopping automated testing on a sensor. Those
> scripts ask you to type `yes` before sending anything. Read the prompt before
> confirming, and prefer a non-production organization while you are learning.
