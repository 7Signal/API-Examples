# What's New

Newly documented 7SIGNAL API endpoints, with links to their reference pages and the
example scripts.

This release adds **16 new endpoints** across 2 areas of the API.

---

## Alerting

Configure what you get notified about, and review what has fired.

**Reference:** [Alerting](16-alerting.md) · **Examples:**
[`flow_alert_rules.py`](../examples/alerting/flow_alert_rules.py),
[`alert_incidents.py`](../examples/alerting/alert_incidents.py)

| Endpoint | Methods | What it does |
|----------|---------|--------------|
| `/alerting/alert-rules` | GET, POST | List and create alert rules |
| `/alerting/alert-rules/summary` | GET | Total, active, and disabled rule counts |
| `/alerting/alert-rules/{id}` | GET, PUT, DELETE | Read, fully replace, or delete a rule |
| `/alerting/alert-rules/{id}/enabled` | PATCH | Toggle a rule on or off |
| `/alerting/incidents` | GET | List incidents, filtered by status, metric, rule, or time |
| `/alerting/incidents/summary` | GET | Total and currently-active incident counts |
| `/alerting/incidents/by-rule` | GET | Incident counts grouped by rule — finds your noisiest rules |
| `/alerting/incidents/{id}` | GET | One incident, with the rule that created it |
| `/alerting/incidents/{id}/resolve` | POST | Manually resolve an active incident |

Worth knowing: a rule is evaluated once per combination of the dimensions in its
`dimensionSet`. The dimension set is what controls how granular the alerts are.
Enum values on these endpoints are lowercase (`avg`, `ignore`, `<`).


## Sensor Targets, Network Keys & Default Configurations

Configure network topology elements, network keys, and more.

**Reference:** [Sensor Targets, Network Keys & Default Configurations](19-sensor-targets-and-network-keys.md) ·
**Examples:** [`flow_targets_sensors.py`](../examples/targets/flow_targets_sensors.py),
[`flow_network_keys.py`](../examples/network_keys/flow_network_keys.py),
[`default_configurations_sensors.py`](../examples/default_configurations/default_configurations_sensors.py)

| Endpoint | Methods | What it does |
|----------|---------|--------------|
| `/targets/sensors` | GET, POST | List and create sensor test targets |
| `/targets/sensors/{targetId}` | GET, PUT, DELETE | Read, replace, or delete a target |
| `/network-keys/sensors` | GET, POST | List and create sensor network keys |
| `/network-keys/sensors/templates` | GET | Pre-built templates, mainly for captive portals |
| `/network-keys/sensors/{networkKeyId}` | GET, PUT, DELETE | Read, replace, or delete a network key |
| `/default-configurations/sensors` | GET | List the configuration bundles (read-only) |
| `/default-configurations/sensors/{configurationId}` | GET | Fetch one bundle (read-only) |

**IMPORTANT**: **network key secrets are returned masked as `********` and the real
value is never returned.** Since `PUT` is a full replace, echoing a fetched key back
writes the mask as the literal secret. Deletes are reference-checked — a key that is still 
bound to a network returns `409`.

