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

## Set up Python
1. https://www.python.org/downloads/
2. Download python 
3. Verify version
   
    `python --version`

## Install Dependencies
1. Install the Requests library
    
    `pip install requests`

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

## MAC
### Configure Settings
These files require 2 main environment variables:

```
export API_KEY=“your-client-id”
export API_SECRET=“your-client-secret”
```

## Additional Variables
Depending on the script you want to run, it will ask you to set a couple of additional variables:

Eyes Endpoint

    Enter the Agent ID: "your-agent-id"
    

KPI Endpoint
    
    Enter the KPI code: "your-kpi-code"


Packet Capture Endpoint
    
    Enter the SENSOR ID: "your-sensor-id"


Time Series Endpoint
    
    Enter from_time timestamp (milliseconds): "your-epoch-time-you’re-measuring-from-in-milliseconds"
    Enter to_time timestamp (milliseconds): "your-current-epoch-time-in-milliseconds"


## Run the Python Script
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
