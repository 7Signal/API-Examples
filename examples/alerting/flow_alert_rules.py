# This script demonstrates how to manage 7SIGNAL alert rules through their full lifecycle.
# It shows how to:
#  - List alert rules and read the aggregate rules summary
#  - Create an alert rule with the five required fields
#  - Fully replace a rule, and toggle one on or off without rewriting it
#  - Delete a rule, with a confirmation prompt first
#
# Alert rules decide when an incident is raised. Creating, changing, or deleting one
# changes what your organization gets notified about, so every write operation here
# asks for confirmation before it sends anything.

import os
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

# The API rejects these enum values unless they are lowercase exactly as listed.
VALID_AGGREGATIONS = ["avg", "min", "max"]
VALID_OPERATORS = ["<", "<=", ">", ">="]
VALID_DIMENSIONS = ["device_id", "bssid", "network", "band", "location_id", "target"]

JSON_CONTENT_TYPE = "application/json"


def json_headers(token):
    # Headers for the calls that send a JSON body.
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": JSON_CONTENT_TYPE,
    }


def list_alert_rules(token, page=1, per_page=10, metric=None, enabled=None, name=None):
    # Fetches a page of alert rules. Optional arguments filter the results.
    url = f"https://{API_HOST}/alerting/alert-rules"
    headers = {"Authorization": f"Bearer {token}"}

    # The first page is 1 for this endpoint, not 0
    params = {"page": page, "perPage": per_page}
    if metric:
        params["metric"] = metric
    if enabled is not None:
        params["enabled"] = enabled
    if name:
        params["name"] = name

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def get_alert_rules_summary(token):
    # Fetches total/active/disabled counts without paging the whole list.
    url = f"https://{API_HOST}/alerting/alert-rules/summary"
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


def get_alert_rule(token, rule_id):
    # Fetches a single alert rule. Returns None when the rule does not exist.
    url = f"https://{API_HOST}/alerting/alert-rules/{rule_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            logging.info(f"No alert rule found with id {rule_id}.")
            return None

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def create_alert_rule(token, metric, dimension_set, aggregation_function,
                      threshold_value, threshold_operator, name=None,
                      pending_period_seconds=None, missing_data_policy=None,
                      notification_config=None, enabled=None):
    # Creates an alert rule. The first five arguments are the API's required fields.
    #
    # The enum values are validated here rather than only at the prompt, so calling
    # this function directly gives a clear message instead of a bare 400.
    if aggregation_function not in VALID_AGGREGATIONS:
        logging.error(f"Unsupported aggregation function: {aggregation_function}")
        logging.error(f"Valid values are: {', '.join(VALID_AGGREGATIONS)} (lowercase)")
        return None

    if threshold_operator not in VALID_OPERATORS:
        logging.error(f"Unsupported threshold operator: {threshold_operator}")
        logging.error(f"Valid values are: {' '.join(VALID_OPERATORS)}")
        return None

    if not dimension_set:
        logging.error("At least one dimension is required in dimensionSet.")
        return None

    unsupported = [d for d in dimension_set if d not in VALID_DIMENSIONS]
    if unsupported:
        logging.error(f"Unsupported dimension(s): {', '.join(unsupported)}")
        logging.error(f"Valid values are: {', '.join(VALID_DIMENSIONS)}")
        return None

    url = f"https://{API_HOST}/alerting/alert-rules"
    headers = json_headers(token)

    payload = {
        "metric": metric,
        "dimensionSet": dimension_set,
        "aggregationFunction": aggregation_function,
        "thresholdValue": threshold_value,
        "thresholdOperator": threshold_operator,
    }

    # Only send the optional fields the caller actually set, so the server
    # applies its own defaults for the rest.
    if name:
        payload["name"] = name
    if pending_period_seconds is not None:
        payload["pendingPeriodSeconds"] = pending_period_seconds
    if missing_data_policy:
        payload["missingDataPolicy"] = missing_data_policy
    if notification_config:
        payload["notificationConfig"] = notification_config
    if enabled is not None:
        payload["enabled"] = enabled

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        created = response.json()
        logging.info(f"Alert rule created with id {created.get('id')}.")
        return created
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def replace_alert_rule(token, rule_id, payload):
    # Replaces an alert rule. This is a full replace: any optional field left out
    # of the payload reverts to its default instead of keeping its current value,
    # so confirm before sending.
    if not confirm_action(f"Replace alert rule {rule_id}? Omitted optional fields "
                          "will revert to their defaults."):
        logging.info("Aborted; the alert rule was not changed.")
        return None

    url = f"https://{API_HOST}/alerting/alert-rules/{rule_id}"
    headers = json_headers(token)

    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Alert rule {rule_id} replaced.")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def set_alert_rule_enabled(token, rule_id, enabled):
    # Turns a rule on or off. Preferred over a full replace for a simple toggle.
    # Disabling a rule stops it being evaluated, so no incidents are raised and no
    # notifications are sent while it is off - confirm before sending.
    action = "Enable" if enabled else "Disable"
    if not confirm_action(f"{action} alert rule {rule_id}?"):
        logging.info("Aborted; the alert rule was not changed.")
        return None

    url = f"https://{API_HOST}/alerting/alert-rules/{rule_id}/enabled"
    headers = json_headers(token)

    try:
        response = requests.patch(url, headers=headers, json={"enabled": enabled})
        response.raise_for_status()
        state = "enabled" if enabled else "disabled"
        logging.info(f"Alert rule {rule_id} is now {state}.")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return None


def confirm_action(message):
    # Asks the user to type 'yes' before a change is sent to the API.
    choice = input(f"{message} Type 'yes' to confirm: ").strip().lower()
    return choice == "yes"


def delete_alert_rule(token, rule_id):
    # Deletes an alert rule after confirming with the user. Returns True only when
    # the delete was actually sent and accepted.
    if not confirm_action(f"Delete alert rule {rule_id}?"):
        logging.info("Aborted; the alert rule was not deleted.")
        return False

    url = f"https://{API_HOST}/alerting/alert-rules/{rule_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        logging.info(f"Alert rule {rule_id} deleted.")
        return True
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")

    return False


def display_alert_rules(data):
    # Logs a readable summary of a page of alert rules.
    rules = data.get("results", [])
    pagination = data.get("pagination", {})

    logging.info("===== Alert Rules =====")

    if not rules:
        logging.info("No alert rules found.")
        return

    logging.info(f"Page {pagination.get('page', '?')} of {pagination.get('pages', '?')} "
                 f"({pagination.get('total', '?')} total)")
    logging.info("-----")

    for rule in rules:
        state = "enabled" if rule.get("enabled") else "disabled"
        dimensions = ", ".join(rule.get("dimensionSet") or []) or "N/A"

        logging.info(f"  Name       : {rule.get('name') or '(unnamed)'}")
        logging.info(f"  Id         : {rule.get('id', 'N/A')}")
        logging.info(f"  Metric     : {rule.get('metric', 'N/A')}")
        logging.info(f"  Dimensions : {dimensions}")

        # Render the condition the way the rule reads, e.g. "avg < 70.0"
        aggregation = rule.get("aggregationFunction")
        operator = rule.get("thresholdOperator")
        threshold = rule.get("thresholdValue")
        if aggregation and operator and threshold is not None:
            logging.info(f"  Condition  : {aggregation} {operator} {threshold}")

        if rule.get("pendingPeriodSeconds") is not None:
            logging.info(f"  Pending    : {rule.get('pendingPeriodSeconds')} seconds")
        if rule.get("missingDataPolicy"):
            logging.info(f"  Missing    : {rule.get('missingDataPolicy')}")

        logging.info(f"  State      : {state}")
        logging.info("-----")


def display_alert_rule_summary(summary):
    # Logs the aggregate rule counts.
    if not summary:
        return

    logging.info("===== Alert Rules Summary =====")
    logging.info(f"  Total    : {summary.get('totalCount', 'N/A')}")
    logging.info(f"  Active   : {summary.get('activeCount', 'N/A')}")
    logging.info(f"  Disabled : {summary.get('disabledCount', 'N/A')}")


def prompt_for_rule_id():
    # Asks for an alert rule id and exits when nothing is entered. Every action that
    # works on a single rule starts here.
    rule_id = input("Enter the ALERT RULE ID: ").strip()
    if not rule_id:
        logging.error("Alert rule id cannot be empty.")
        sys.exit(1)

    return rule_id


def prompt_for_number(message):
    # Asks for a numeric value and exits when it isn't one.
    value = input(message).strip()
    try:
        return float(value)
    except ValueError:
        logging.error("Threshold must be a number.")
        sys.exit(1)


def prompt_for_new_rule():
    # Collects and validates the fields needed to create a rule. Returns a dict of
    # keyword arguments for create_alert_rule().
    metric = input("Enter the METRIC name: ").strip()
    if not metric:
        logging.error("Metric cannot be empty.")
        sys.exit(1)

    logging.info(f"Available dimensions: {', '.join(VALID_DIMENSIONS)}")
    dimensions_input = input("Enter one or more DIMENSIONS (comma separated): ").strip()
    dimension_set = [d.strip() for d in dimensions_input.split(",") if d.strip()]
    if not dimension_set:
        logging.error("At least one dimension is required.")
        sys.exit(1)

    invalid = [d for d in dimension_set if d not in VALID_DIMENSIONS]
    if invalid:
        logging.error(f"Unsupported dimension(s): {', '.join(invalid)}")
        logging.error(f"Valid values are: {', '.join(VALID_DIMENSIONS)}")
        sys.exit(1)

    aggregation = input(f"Enter the AGGREGATION ({'/'.join(VALID_AGGREGATIONS)}): ").strip().lower()
    if aggregation not in VALID_AGGREGATIONS:
        logging.error(f"Aggregation must be one of: {', '.join(VALID_AGGREGATIONS)}")
        sys.exit(1)

    operator = input(f"Enter the OPERATOR ({' '.join(VALID_OPERATORS)}): ").strip()
    if operator not in VALID_OPERATORS:
        logging.error(f"Operator must be one of: {' '.join(VALID_OPERATORS)}")
        sys.exit(1)

    threshold_value = prompt_for_number("Enter the THRESHOLD value: ")
    name = input("Enter a NAME for the rule (optional): ").strip() or None

    return {
        "metric": metric,
        "dimension_set": dimension_set,
        "aggregation_function": aggregation,
        "threshold_value": threshold_value,
        "threshold_operator": operator,
        "name": name,
    }


def action_fetch_rule(token):
    # Fetches and displays a single rule.
    rule = get_alert_rule(token, prompt_for_rule_id())
    if rule:
        display_alert_rules({"results": [rule]})


def action_create_rule(token):
    # Collects the rule fields, confirms, then creates it.
    fields = prompt_for_new_rule()

    if not confirm_action("Create this alert rule?"):
        logging.info("Aborted; no alert rule was created.")
        return

    created = create_alert_rule(token, **fields)
    if created:
        display_alert_rules({"results": [created]})


def action_toggle_rule(token):
    # Enables or disables a rule without rewriting the rest of it.
    rule_id = prompt_for_rule_id()

    state_input = input("Enable or disable? (enable/disable): ").strip().lower()
    if state_input not in ("enable", "disable"):
        logging.error("Please answer 'enable' or 'disable'.")
        sys.exit(1)

    set_alert_rule_enabled(token, rule_id, state_input == "enable")


def action_replace_threshold(token):
    # Changes a rule's threshold through the full-replace endpoint.
    rule_id = prompt_for_rule_id()

    # Fetch first, because PUT is a full replace: anything left out of the
    # payload reverts to its default rather than keeping its current value.
    existing = get_alert_rule(token, rule_id)
    if not existing:
        return

    new_threshold = prompt_for_number(
        f"Enter the NEW THRESHOLD (currently {existing.get('thresholdValue')}): "
    )

    # Carry every field the API returned back into the replacement payload
    payload = {
        "metric": existing.get("metric"),
        "dimensionSet": existing.get("dimensionSet"),
        "aggregationFunction": existing.get("aggregationFunction"),
        "thresholdValue": new_threshold,
        "thresholdOperator": existing.get("thresholdOperator"),
    }
    for field in ("name", "dimensionFilters", "pendingPeriodSeconds",
                  "missingDataPolicy", "notificationConfig", "locationSelection",
                  "enabled"):
        if existing.get(field) is not None:
            payload[field] = existing[field]

    updated = replace_alert_rule(token, rule_id, payload)
    if updated:
        display_alert_rules({"results": [updated]})


def action_delete_rule(token):
    # Deletes a rule after confirming.
    delete_alert_rule(token, prompt_for_rule_id())


# The menu, in order. Each entry pairs the label shown to the user with the function
# that carries the action out.
MENU_ACTIONS = [
    ("Fetch a single alert rule", action_fetch_rule),
    ("Create a new alert rule", action_create_rule),
    ("Enable or disable an alert rule", action_toggle_rule),
    ("Change an alert rule's threshold (full replace)", action_replace_threshold),
    ("Delete an alert rule", action_delete_rule),
]


def main():
    # Step 1: Authenticate and get a bearer token
    token, _ = get_token()

    # Step 2: Show the current state of the organization's alert rules
    display_alert_rule_summary(get_alert_rules_summary(token))

    rules = list_alert_rules(token)
    if rules:
        display_alert_rules(rules)

    # Step 3: Offer the lifecycle actions
    logging.info("What would you like to do?")
    for number, (label, _action) in enumerate(MENU_ACTIONS, start=1):
        logging.info(f"  {number}) {label}")
    exit_choice = len(MENU_ACTIONS) + 1
    logging.info(f"  {exit_choice}) Exit")

    choice = input(f"Enter a number (1-{exit_choice}): ").strip()

    # Step 4: Run the chosen action
    if choice.isdigit() and 1 <= int(choice) <= len(MENU_ACTIONS):
        MENU_ACTIONS[int(choice) - 1][1](token)
    else:
        logging.info("Nothing to do.")


if __name__ == "__main__":
    main()
