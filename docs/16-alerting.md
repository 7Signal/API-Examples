# Alerting (Alert Rules & Incidents)

## 1. Overview

The Alerting endpoints let you monitor a metric continuously and be notified when it degrades past a
threshold you choose. There are two related resources:

- **Alert rules** (`/alerting/alert-rules`) — the configuration. A rule names a metric, the dimensions
  to evaluate it across, how to aggregate samples, the threshold to compare against, how long the
  breach must persist, and where to send notifications.
- **Incidents** (`/alerting/incidents`) — the history. When a rule's condition holds for its full
  pending period, an incident is raised. Incidents record when the breach started, the value that
  triggered it, and — once the metric recovers or the incident is resolved — when and why it ended.

A rule is evaluated independently for every combination of the dimensions in its `dimensionSet`. A rule
keyed on `device_id` raises a separate incident per device; a rule keyed on `network` raises one per
network. Choosing the dimension set is therefore the main lever on how granular your alerting is.

Each incident stores a **snapshot** of the rule configuration as it was when the incident was raised.
That means historical incidents still read correctly after you edit or delete the rule that produced
them.

> **Not to be confused with** `/incidents/agents`, which is a separate, unrelated resource covering
> per-agent connectivity incidents detected by the platform. See
> [Agent Incidents](18-agent-incidents.md). The endpoints on this page all live under `/alerting/`.

## 2. Endpoints

### Alert Rules

#### `GET /alerting/alert-rules`

Pages through the alert rules for an organization.

**Required parameters:** none

**Optional parameters:** `metric`, `enabled`, `name`, `organization`, `page`, `perPage`, `sortField`, `order`

```json
{
  "results": [
    {
      "id": "3f2b9c1e-58a4-4d2f-9b71-2c0e5a7d1f34",
      "name": "Low client health on guest network",
      "metric": "client_health_score",
      "dimensionSet": ["network", "band"],
      "dimensionFilters": null,
      "aggregationFunction": "avg",
      "thresholdValue": 70.0,
      "thresholdOperator": "<",
      "pendingPeriodSeconds": 600,
      "missingDataPolicy": "ignore",
      "notificationConfig": {
        "deliveries": [
          { "kind": "email", "address": "neteng@example.com" }
        ]
      },
      "enabled": true,
      "locationSelection": null,
      "createdAt": "2026-07-14T18:22:05Z",
      "updatedAt": "2026-08-02T11:47:31Z"
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 1,
    "total": 23,
    "pages": 3
  }
}
```

#### `POST /alerting/alert-rules`

Creates an alert rule. Returns `201` with the created rule.

**Required body fields:** `metric`, `dimensionSet`, `aggregationFunction`, `thresholdValue`, `thresholdOperator`

```json
{
  "name": "Low client health on guest network",
  "metric": "client_health_score",
  "dimensionSet": ["network", "band"],
  "aggregationFunction": "avg",
  "thresholdValue": 70.0,
  "thresholdOperator": "<",
  "pendingPeriodSeconds": 600,
  "missingDataPolicy": "ignore",
  "enabled": true,
  "notificationConfig": {
    "deliveries": [
      { "kind": "email", "address": "neteng@example.com" },
      { "kind": "servicenow", "mdsConfigId": "abc-123", "organizationName": "globalcorp" }
    ]
  }
}
```

#### `GET /alerting/alert-rules/summary`

Aggregate counts of the organization's rules — useful for a dashboard header without paging the full list.

```json
{
  "totalCount": 23,
  "activeCount": 19,
  "disabledCount": 4
}
```

#### `GET /alerting/alert-rules/{id}`

Fetches a single rule. Returns `404` if the id does not exist in your organization.

**Required parameters:** `id` (UUID, in path)

#### `PUT /alerting/alert-rules/{id}`

**Fully replaces** the rule. This is a replace, not a merge — any optional field you omit reverts to its
default rather than keeping its previous value. Fetch the rule first, modify the fields you want, and
send the whole object back.

**Required parameters:** `id` (UUID, in path). Body is the same shape as `POST`.

#### `DELETE /alerting/alert-rules/{id}`

Deletes the rule. Returns `204` with no body.

Deleting a rule does not delete the incidents it produced — those remain, and their `resolutionReason`
becomes `rule_deleted` for any that were still active.

**Required parameters:** `id` (UUID, in path)

#### `PATCH /alerting/alert-rules/{id}/enabled`

Enables or disables a rule without rewriting the rest of it. This is the endpoint to use for a simple
on/off toggle — `PUT` would require resending the entire rule.

**Required parameters:** `id` (UUID, in path)

```json
{ "enabled": false }
```

### Alert Incidents

#### `GET /alerting/incidents`

Pages through incidents raised by your alert rules.

**Required parameters:** none

**Optional parameters:** `status`, `metric`, `dimensionKey`, `ruleId`, `startedAfter`, `startedBefore`,
`resolvedAfter`, `resolvedBefore`, `organization`, `page`, `perPage`, `sortField`, `order`

```json
{
  "results": [
    {
      "id": "9c81f0a7-3d6e-4b12-8f55-71ae4c2b9d08",
      "ticketId": "INC0012345",
      "ruleId": "3f2b9c1e-58a4-4d2f-9b71-2c0e5a7d1f34",
      "metric": "client_health_score",
      "dimensionSet": ["network", "band"],
      "dimensionKey": "CorpWiFi|5",
      "startedAt": 1786975920000,
      "resolvedAt": 1786977480000,
      "resolutionReason": "cleared",
      "triggerValue": 61.4,
      "resolveValue": 78.2,
      "snapshot": {
        "thresholdValue": 70.0,
        "thresholdOperator": "<",
        "aggregationFunction": "avg",
        "pendingPeriodSeconds": 600,
        "dimensionFilters": null
      }
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 1,
    "total": 148,
    "pages": 15
  }
}
```

#### `GET /alerting/incidents/summary`

```json
{
  "totalCount": 148,
  "activeCount": 6
}
```

#### `GET /alerting/incidents/by-rule`

Incident counts grouped by the rule that produced them. Answers "which of my rules is noisiest?"

**Optional parameters:** `from`, `to`, `organization`, `page`, `perPage`

There is **no `ruleId` filter on this endpoint** — it always groups across every rule. To look at one
rule's incidents, use `GET /alerting/incidents?ruleId=<id>` instead.

Note this returns a **bare JSON array**, not a `{results, pagination}` envelope.

```json
[
  {
    "ruleId": "3f2b9c1e-58a4-4d2f-9b71-2c0e5a7d1f34",
    "rule": {
      "metric": "client_health_score",
      "dimensionSet": ["network", "band"],
      "thresholdValue": 70.0,
      "thresholdOperator": "<"
    },
    "incidentCount": 42,
    "activeCount": 3
  }
]
```

#### `GET /alerting/incidents/{id}`

Fetches a single incident, including its rule snapshot. Returns `404` if the id is unknown.

**Required parameters:** `id` (UUID, in path)

#### `POST /alerting/incidents/{id}/resolve`

Manually resolves an active incident — for when you've fixed the underlying problem and don't want to
wait for the metric to recover on its own. The resolved incident sets `resolutionReason` to
`cleared_by_user`.

**Required parameters:** `id` (UUID, in path). No request body.

Returns `409` if the incident is already resolved.

## 3. Developer Tips

**Query parameters:**

| Parameter | Type | Applies to | Description |
|-----------|------|------------|-------------|
| `metric` | string | rules, incidents | Filter by metric name |
| `enabled` | boolean | rules | Filter by enabled state |
| `name` | string | rules | Case-insensitive partial match on rule name |
| `status` | string | incidents | `active` or `resolved` |
| `dimensionKey` | string | incidents | Filter by the concrete dimension key |
| `ruleId` | string (UUID) | incidents | Only incidents from this rule. **Not accepted by by-rule** |
| `startedAfter` / `startedBefore` | integer | incidents | Epoch milliseconds, UTC |
| `resolvedAfter` / `resolvedBefore` | integer | incidents | Epoch milliseconds, UTC |
| `from` / `to` | integer | by-rule | Window for the aggregation (epoch ms) |
| `organization` | string | all | Defaults to the organization on your token |
| `page` | integer | all paginated | **First page is 1**, not 0 |
| `perPage` | integer | all paginated | Records per page |
| `sortField` | string | all paginated | Field to sort on |
| `order` | string | all paginated | `asc` or `desc` |

**Enum values are lowercase, and the API is strict about them.** This is the single easiest thing to get
wrong:

| Field | Accepted values |
|-------|-----------------|
| `dimensionSet` items | `device_id`, `bssid`, `network`, `band`, `location_id`, `target` |
| `aggregationFunction` | `avg`, `min`, `max` |
| `thresholdOperator` | `<`, `<=`, `>`, `>=` |
| `missingDataPolicy` | `ignore`, `good`, `bad` |
| `resolutionReason` (read-only) | `cleared`, `cleared_by_user`, `rule_deleted`, `rule_config_changed`, `insufficient_data`, `location_deleted`, `rule_disabled` |

Sending `"AVG"` or `"Avg"` instead of `"avg"` returns a `400`.

**Defaults when you omit optional fields:**

| Field | Default |
|-------|---------|
| `pendingPeriodSeconds` | `300` (minimum `1`) |
| `missingDataPolicy` | `ignore` |
| `enabled` | `true` |

**Missing data policy** controls what happens when a metric reports nothing for an evaluation window:

- `ignore` — hold the current state and wait for the next window with data. The safe default.
- `good` — treat the gap as compliant. No incident is raised.
- `bad` — treat the gap as a breach. Expect more incidents; devices that go offline legitimately will
  trigger alerts.

**Notification deliveries** are a list, and each entry is discriminated by `kind`:

```json
{
  "deliveries": [
    { "kind": "email", "address": "neteng@example.com" },
    { "kind": "webhook", "url": "https://hooks.example.com/7signal", "auth": { "type": "NONE" }, "format": "slack" },
    { "kind": "servicenow", "mdsConfigId": "abc-123", "organizationName": "globalcorp" }
  ]
}
```

- `email` requires `address`.
- `webhook` requires `url` and `auth`. `format` is `generic` (default) or `slack`.
- `servicenow` requires `mdsConfigId` and `organizationName`, and the ServiceNow integration must
  already be configured — see [Integration Configs](12-integration-configs.md).

For an authenticated webhook, credentials are referenced by AWS Secrets Manager ARN rather than sent
inline — `{ "type": "BASIC", "username": "svc", "passwordSecretArn": "arn:aws:secretsmanager:..." }` or
`{ "type": "TOKEN", "tokenSecretArn": "arn:aws:secretsmanager:..." }`. The secret value itself is never
stored on, or returned by, the rule.

**Getting epoch milliseconds in Python:**

```python
import time

# Current time in milliseconds
now_ms = int(time.time() * 1000)

# 24 hours ago
yesterday_ms = now_ms - (24 * 60 * 60 * 1000)
```

**Toggling a rule off is not the same as deleting it.** `PATCH .../enabled` keeps the configuration and
the incident history, and stops evaluation. `DELETE` removes the rule permanently.

## 4. Troubleshooting & FAQs

**Q: I created a rule with a breaching metric, but no incident appeared.**

A: Check `pendingPeriodSeconds`. The condition has to hold continuously for that long before an incident
is raised — with the default of `300`, a metric that dips below threshold for two minutes and recovers
will never raise one. Also confirm the rule is `enabled`.

**Q: My `PUT` wiped settings I didn't touch.**

A: `PUT` fully replaces the rule; it does not merge. Omitted optional fields fall back to their defaults
(`pendingPeriodSeconds` → `300`, `missingDataPolicy` → `ignore`, `enabled` → `true`), which reads as
settings being wiped. `GET` the rule, change the fields you want, and `PUT` the complete object back.
For an enable/disable toggle, use `PATCH .../enabled` instead.

**Q: I get a `400` on create and the message points at `aggregationFunction` or `thresholdOperator`.**

A: These enums are case-sensitive and lowercase — `avg`, not `AVG`. `thresholdOperator` is the literal
symbol (`<`, `<=`, `>`, `>=`), not a word like `lt`.

**Q: `POST /alerting/incidents/{id}/resolve` returns `409`.**

A: The incident is already resolved. Fetch it and check `resolvedAt` and `resolutionReason` — the metric
may have recovered on its own between your list call and the resolve call.

**Q: Why does one rule produce so many incidents?**

A: A rule is evaluated once per combination of the dimensions in `dimensionSet`. A rule keyed on
`device_id` evaluates every device independently, so a site-wide problem raises one incident per affected
device. Key the rule on a coarser dimension — `location_id`, `network`, or `band` — if you want one
incident for the whole group. `GET /alerting/incidents/by-rule` will show you which rules are the
noisiest.

**Q: An incident's `resolutionReason` is `rule_config_changed`. What happened?**

A: The rule was edited while the incident was active. Because the evaluation criteria changed, the old
incident is closed out rather than carried forward against different thresholds. If the new
configuration still breaches, a fresh incident is raised on the next evaluation.

**Q: I deleted a rule. Why are its incidents still listed?**

A: Incidents are retained as historical records and keep the rule snapshot they were raised under, so
they stay meaningful after the rule is gone. Active incidents belonging to a deleted rule are resolved
with `resolutionReason` of `rule_deleted`.

**Q: The `dimensionKey` values look like `CorpWiFi|5`. What's the format?**

A: It's the concrete values of the rule's `dimensionSet`, in order, joined by `|`. For a
`dimensionSet` of `["network", "band"]`, `CorpWiFi|5` means network `CorpWiFi` on the 5 GHz band. Match
it against `dimensionSet` on the same incident to interpret the parts.
