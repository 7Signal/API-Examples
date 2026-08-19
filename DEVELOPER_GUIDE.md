# Developer Guide

## Overview
This repository contains Python-based examples for interacting with the 7SIGNAL API. All examples demonstrate OAuth2 authentication and various API endpoint interactions.

## Important: Audience and Purpose

**These scripts are exemplary and educational.** They are designed to:
- Demonstrate best practices for API integration
- Serve as learning resources for developers of varying skill levels
- Provide copy-paste starting points for custom integrations

### Keep Non-Developer Users in Mind

When creating or modifying examples, remember that **many users may not be experienced Python developers**. Always:

1. **Write clear, self-documenting code** - Use descriptive variable names and avoid overly complex patterns
2. **Include comprehensive comments** - Explain the "why" behind non-obvious decisions
3. **Add helpful header documentation** - Clearly state what the script does and what it demonstrates
4. **Provide clear error messages** - Help users understand what went wrong and how to fix it
5. **Keep dependencies minimal** - Only require libraries that are truly necessary
6. **Use standard Python patterns** - Avoid advanced features that require deep Python knowledge
7. **Include usage examples** - Show exactly how to run the script with sample inputs
8. **Validate user input gracefully** - Provide friendly prompts and helpful validation messages

### Example Audience Scenarios
- **System administrators** learning to automate 7SIGNAL tasks
- **Network engineers** with basic scripting knowledge
- **IT professionals** integrating 7SIGNAL into existing workflows
- **Technical support staff** using scripts for troubleshooting

**Remember**: If a user can't understand what a script does or how to modify it for their needs, the example has failed its purpose. Clarity and accessibility are paramount.

## Project Structure

```
API-Examples/
├── README.md                      # User-facing setup and usage instructions
├── DEVELOPER_GUIDE.md             # This file: conventions for writing examples
├── auth_utils.py                  # Shared authentication module (OAuth2)
├── docs/                          # API reference documentation (see docs/README.md)
│   ├── 01-authentication.md ...   # Numbered reference chapters
│   ├── WHATS-NEW.md               # Recently documented endpoints + OpenAPI version reviewed
│   └── migration/                 # Deprecated endpoints and their replacements
├── examples/                      # All example scripts organized by category
│   ├── access_points/             # Access point and agent interactions
│   ├── alerting/                  # Alert rules and alert incidents
│   ├── api_keys/                  # API key management and retrieval
│   ├── audits/                    # Agent audit trail
│   ├── authentication/            # Authentication examples
│   ├── change_events/             # Sensor-side configuration change events
│   ├── clients/                   # Client devices observed by sensors
│   ├── default_configurations/    # Sensor default configuration bundles (read-only)
│   ├── eyeris/                    # Eyeris AI analysis (polling and streaming)
│   ├── eyes/                      # Eyes Agents (licensing, sensors, CSV ops, automated testing)
│   ├── groups/                    # Group management
│   ├── impact/                    # Agent and location impact metrics
│   ├── incidents/                 # Platform-detected agent incidents
│   ├── kpi/                       # KPI endpoint examples
│   ├── network_keys/              # Sensor network keys (WPA/EAP/captive portal)
│   ├── networks/                  # Network operations
│   ├── on_demand_tests/           # Requesting on-demand tests and polling for results
│   ├── organization/              # Organization management
│   ├── rate_limiting/             # Rate limit handling utilities
│   ├── roles/                     # Role management
│   ├── scans/                     # RF scan data from agents and sensors
│   ├── service_areas/             # Agent service areas (bulk and single operations)
│   ├── summaries/                 # User summary counts
│   ├── targets/                   # Sensor test targets
│   ├── time_series/               # Time series data and SLA reports
│   ├── topologies/                # Topology operations
│   └── user_management/           # User CRUD operations
├── tests/                         # Test files (mirrors examples structure)
└── venv/                          # Python virtual environment
```

## Core Components

### 1. Authentication Module (`auth_utils.py`)

**Purpose**: Centralized OAuth2 authentication with token caching

**Key Features**:
- OAuth2 Client Credentials flow
- Token caching and automatic reuse until expiration
- Environment variable configuration
- Configurable logging

**Environment Variables**:
```bash
API_KEY         # Required: OAuth2 client ID
API_SECRET      # Required: OAuth2 client secret
API_HOST        # Optional: API hostname (default: api-v2.7signal.com)
LOG_LEVEL       # Optional: Logging level (default: INFO, can set to DEBUG)
```

**Main Function**:
```python
def get_token() -> tuple[str, float]:
    """
    Returns: (access_token, expires_at)
    - Reuses cached token if still valid
    - Fetches new token if expired or missing
    """
```

**Usage Pattern**:
```python
from auth_utils import get_token

token, expires_at = get_token()
headers = {"Authorization": f"Bearer {token}"}
```

### 2. Rate Limiting Module (`examples/rate_limiting/rate_limit.py`)

**Purpose**: Handle API rate limits with automatic retry logic

**Key Function**:
```python
def handle_rate_limits(api_func, max_retries=5):
    """
    Wrapper function that:
    - Executes the provided API function
    - Checks for 429 status code
    - Calculates wait time based on x-ratelimit-replenish-rate header
    - Retries with exponential backoff
    - Returns JSON response or None
    """
```

**Rate Limit Headers**:
- `x-ratelimit-remaining`: Tokens remaining in bucket
- `x-ratelimit-burst-capacity`: Maximum burst capacity
- `x-ratelimit-replenish-rate`: Tokens added per second
- `x-ratelimit-requested-tokens`: Tokens needed for request

**Usage Pattern**:
```python
from rate_limit import handle_rate_limits

def api_call():
    return requests.get(url, headers=headers)

result = handle_rate_limits(api_call)
```

## Common Code Patterns

### Standard Script Structure

Every example script follows this pattern:

```python
# 1. Header comment explaining what the script does
# This script demonstrates how to [purpose].
# It shows how to:
#  - [Key feature 1]
#  - [Key feature 2]
#  - [Key feature 3]

# 2. Imports
import os
import sys
import logging
import requests

# 3. Path setup for importing auth_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth_utils import get_token

# 4. Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 5. Environment variable setup
API_HOST = os.getenv("API_HOST", "api-v2.7signal.com")

# 6. Helper functions
def fetch_data(token, param):
    url = f"https://{API_HOST}/endpoint/{param}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")
    
    return None

# 7. Main function
def main():
    # Get token
    token, _ = get_token()
    
    # Get user input if needed
    param = input("Enter parameter: ").strip()
    
    # Call API
    data = fetch_data(token, param)
    
    # Process results
    if data:
        logging.info(f"Success: {data}")

# 8. Entry point
if __name__ == "__main__":
    main()
```

### API Request Patterns

#### GET Request (Read)
```python
def fetch_resource(token, resource_id):
    url = f"https://{API_HOST}/endpoint/{resource_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
```

#### POST Request (Create)
```python
def create_resource(token, data):
    url = f"https://{API_HOST}/endpoint"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"field": data}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
```

#### PATCH Request (Update)
```python
def update_resource(token, resource_id, data):
    url = f"https://{API_HOST}/endpoint/{resource_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"field": data}
    
    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
```

### CSV Processing Pattern

For bulk operations using CSV files:

```python
import csv

def main():
    # Get token
    token, _ = get_token()
    
    # Get CSV filename from command line
    if len(sys.argv) < 2:
        logging.error("Usage: python script.py <csv_file>")
        return
    csv_file = sys.argv[1]
    
    # Read CSV
    try:
        with open(csv_file) as f:
            csv_rows = csv.DictReader(f)
            rows = list(csv_rows)
    except Exception as e:
        logging.error(f"Error reading CSV {csv_file}: {e}")
        return
    
    # Process each row
    for row in rows:
        value = row.get("column_name", "").strip()
        if not value:
            continue
        # Process the row
        process_row(token, value)
```

### Error Handling Pattern

```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    # Process data
except requests.exceptions.HTTPError as http_err:
    logging.error(f"HTTP error occurred: {http_err}")
    logging.error(f"Response: {response.text}")
except Exception as err:
    logging.error(f"Unexpected error: {err}")
```

### User Input Pattern

```python
# Prompt for required input
resource_id = input("Enter the Resource ID: ").strip()
if not resource_id:
    logging.error("Resource ID cannot be empty.")
    sys.exit(1)

# Optional input with default
choice = input("Continue? (yes/no): ").strip().lower()
if choice == "yes":
    # Proceed
    pass
```

## Script Categories and Examples

### Basic API Operations
- **List resources**: Fetch paginated lists (`examples/api_keys/get_apikeys.py`)
- **Get by ID**: Fetch single resource (`examples/eyes/fetch_agents.py`)
- **Flow pattern**: List → Select → Get details (`examples/api_keys/flow_apikeys.py`)

### Bulk Operations
- **CSV licensing**: Read CSV → Match records → Update (`examples/eyes/csv_licensing.py`)
- **CSV nicknames**: Read CSV → Update agent nicknames (`examples/eyes/csv_nickname.py`)
- **Create users**: Read CSV → Create users with role assignment (`examples/user_management/add_users_from_csv.py`)

### Data Visualization
- **SLA Reports**: Fetch time series → Generate matplotlib charts → Create HTML report (`examples/time_series/last_monitored_devices.py`)

### Advanced Features
- **Rate limiting**: Automatic retry with backoff (`examples/rate_limiting/rate_limit.py`)
- **Pagination**: Handle multi-page results (pagination fields in response)
- **Filtering**: Query parameters for filtering results

## API Response Patterns

### Paginated List Response
```json
{
  "pagination": {
    "perPage": 30,
    "page": 1,
    "total": 150,
    "pages": 5
  },
  "results": [
    { "id": "...", "name": "...", ... }
  ]
}
```

### Single Resource Response
```json
{
  "id": "...",
  "name": "...",
  "field1": "...",
  "field2": "..."
}
```

### Time Series Response
```json
{
  "results": [
    {
      "metricAggregates": [
        {
          "metric": "METRIC_NAME",
          "timeSeries": [
            { "ts": 1234567890000, "avg": 0.95 }
          ]
        }
      ]
    }
  ]
}
```

## Dependencies

### Required
- `requests` - HTTP library for API calls
- Python 3.x standard library (os, sys, logging, time, csv, io, base64)

### Optional
- `matplotlib` - For charting/visualization examples (time_series)

### Installation
```bash
pip install requests
pip install matplotlib  # Only for visualization examples
```

## Best Practices

### 1. Token Management
- Always use `get_token()` from `auth_utils.py`
- Token is automatically cached and reused
- Never hardcode credentials

### 2. Logging
- Use `logging` module, not `print()` for status messages
- Use `INFO` for normal operations
- Use `DEBUG` for detailed troubleshooting
- Use `ERROR` for failures
- Use `WARNING` for non-fatal issues

### 3. Error Handling
- Always wrap API calls in try/except
- Use `response.raise_for_status()` to catch HTTP errors
- Log response text on failures for debugging
- Return `None` or appropriate default on error

### 4. Environment Configuration
- Use `os.getenv()` with sensible defaults
- Document all required environment variables in script header
- Use `API_HOST` for environment flexibility (dev/prod)

### 5. User Input
- Validate all user input
- Strip whitespace from input
- Provide clear error messages
- Exit with `sys.exit(1)` on fatal input errors

### 6. Code Comments
- Add header comment explaining script purpose
- Use inline comments for complex logic only
- Don't over-comment obvious code
- Document non-obvious API behaviors

## Testing Structure

The `tests/` directory mirrors the `examples/` structure, with test files for each category. Tests validate API interactions and error handling.

### Running the tests

`auth_utils.py` raises `EnvironmentError` at **import** time when its credentials are missing, so the environment variables must be set even for tests that never make a real call. Any placeholder value works:

```bash
API_KEY=fake API_SECRET=fake pytest tests/ -v
```

To check coverage on the example scripts:

```bash
API_KEY=fake API_SECRET=fake pytest tests/ --cov=examples --cov-report=term-missing
```

### What a test file covers

Tests never make real HTTP calls — patch `requests` with `unittest.mock` instead. Each example's test file typically covers:

1. The expected functions exist
2. The success path for each API call, asserting the request was built correctly (URL, params, body)
3. Error handling — a `404` returning `None` rather than raising, and any documented `409`
4. Input validation that happens before a request is sent
5. The display helper, including partial data and an empty result set

### Destructive operations

Where an example can change or remove live configuration, it must confirm before sending. Two placements are in use, and which one you pick decides how the test is written:

- **Inside the function** — for operations whose danger is inherent to the call: `DELETE`, a `PUT` that fully replaces, disabling an alert rule, stopping automated testing. Callers importing the function get the guard for free. These return a falsy value (`False`, or `None` where the success path returns an object) when the user declines.
- **In `main()`** — for operations where the prompt needs context the function doesn't have, such as echoing the assembled payload back before creating something.

Test both branches — that a declined prompt issues **no** request, and that a confirmed one does:

```python
@patch("examples.targets.flow_targets_sensors.requests.delete")
@patch("builtins.input", return_value="no")
def test_delete_aborts_without_confirmation(mock_input, mock_delete):
    assert flow_targets_sensors.delete_target("fake-token", 412) is False
    mock_delete.assert_not_called()
```

## Common Pitfalls to Avoid

1. **Don't fetch token in loops** - Get once at start, reuse
2. **Don't ignore rate limits** - Use `handle_rate_limits()` wrapper
3. **Don't hardcode API_HOST** - Use environment variable
4. **Don't use raw prints** - Use logging module
5. **Don't forget error handling** - Always catch exceptions
6. **Don't skip input validation** - Validate before API calls

## Creating New Examples

When creating a new example script:

1. Choose appropriate category directory (or create new one)
2. Follow standard script structure (see above)
3. Include comprehensive header comment
4. Import and use `get_token()` from `auth_utils.py`
5. Configure logging consistently
6. Add proper error handling
7. Test with both success and failure cases
8. Document any special requirements (roles, permissions)
9. Add usage example in script header if it takes arguments
10. Prompt for confirmation before any call that changes or removes live configuration, and say in the header what the change affects
11. Validate enum values and required-field combinations before sending, so the user gets a clear message instead of a `400`

## Example Script Templates

See existing examples for reference:
- **Simple GET**: `examples/eyes/fetch_agents.py`
- **Flow (list → details)**: `examples/api_keys/flow_apikeys.py`
- **CSV bulk operation**: `examples/eyes/csv_licensing.py`
- **Rate limiting**: `examples/rate_limiting/rate_limit.py`
- **Visualization**: `examples/time_series/last_monitored_devices.py`
- **User management**: `examples/user_management/add_users_from_csv.py`
