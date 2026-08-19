# Agent Incidents

## 1. Overview

Agent Incidents are periods where a measurable share of the agent population at a location, network, and
band fell below the platform's service thresholds at the same time. They are detected by the platform
rather than configured by you — there is no rule to create. An incident represents "a group of devices
here had a bad time, together, for long enough to matter."

Each incident carries the count of impacted agents, the size of the population it was measured against,
and the thresholds that were in force when it was determined to be an incident. That last part matters:
it lets you see *why* something qualified without having to reconstruct the configuration afterwards.

> **Not to be confused with** the incidents under `/alerting/incidents`, which are raised by alert rules
> that you define yourself. See [Alerting](16-alerting.md). These endpoints live under `/incidents/`
> and are platform-detected.

## 2. Endpoints

#### `GET /incidents/agents`

Returns the agent incidents that overlap a time window.

**Required parameters:** none — `from` and `to` both default (see Developer Tips)

**Optional parameters:** `from`, `to`, `location_id`, `organization`, `order`

```json
{
  "range": {
    "from": 1786957200000,
    "fromAsDateString": "2026-08-17T09:00:00.000Z[UTC]",
    "to": 1787043600000,
    "toAsDateString": "2026-08-18T09:00:00.000Z[UTC]",
    "total": 3,
    "duration": 86400000,
    "durationAsString": "24 hours"
  },
  "results": [
    {
      "id": "b7c19d3a-4e82-4f16-9d05-3a8c2f7b1e64",
      "startTimestamp": "2026-08-17T14:12:00.000Z",
      "asOfTimestamp": "2026-08-17T14:45:00.000Z",
      "endTimestamp": "2026-08-17T14:38:00.000Z",
      "timestampDeterminedToBeIncident": "2026-08-17T14:22:00.000Z",
      "organizationName": "globalcorp",
      "type": "CONNECTION",
      "location": "4d1e8b7c-9a35-4c72-b6f0-2e5a9d3c8f41",
      "locationName": "Cleveland HQ - Floor 3",
      "network": "CorpWiFi",
      "band": 5.00,
      "countImpacted": 12,
      "populationCount": 84,
      "thresholds": {
        "warningThreshold": 80,
        "criticalThreshold": 60,
        "successRateThreshold": 90,
        "minPopulationCount": 10,
        "minCountImpacted": 5,
        "minPercentImpacted": 10,
        "minIncidentDurationMinutes": 10
      }
    }
  ]
}
```

Note the envelope is `{range, results}` — there is no `pagination` object, and no `page`/`perPage`
parameters. The time window is what bounds the result set.

#### `GET /incidents/agents/{incidentId}`

Fetches a single incident.

**Required parameters:** `incidentId` (UUID, in path)

**Optional parameters:** `organization`

```json
{
  "id": "b7c19d3a-4e82-4f16-9d05-3a8c2f7b1e64",
  "startTimestamp": "2026-08-17T14:12:00.000Z",
  "asOfTimestamp": "2026-08-17T14:45:00.000Z",
  "endTimestamp": "2026-08-17T14:38:00.000Z",
  "timestampDeterminedToBeIncident": "2026-08-17T14:22:00.000Z",
  "organizationName": "globalcorp",
  "type": "CONNECTION",
  "location": "4d1e8b7c-9a35-4c72-b6f0-2e5a9d3c8f41",
  "locationName": "Cleveland HQ - Floor 3",
  "network": "CorpWiFi",
  "band": 5.00,
  "countImpacted": 12,
  "populationCount": 84,
  "warningThreshold": 80,
  "criticalThreshold": 60,
  "successRateThreshold": 90,
  "minPopulationCount": 10,
  "minCountImpacted": 5,
  "minPercentImpacted": 10,
  "minIncidentDurationMinutes": 10
}
```

**The two endpoints shape thresholds differently.** In the list response the threshold fields are nested
under a `thresholds` object; in the single-incident response the same fields sit flat at the top level,
and there is no `thresholds` key at all. Code that reads `incident["thresholds"]["criticalThreshold"]`
against a list result will raise a `KeyError` if you point it at a single-fetch result. See Developer
Tips for a helper that handles both.

## 3. Developer Tips

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from` | integer | No | Lower bound, epoch milliseconds UTC. **Defaults to 24 hours ago** |
| `to` | integer | No | Upper bound, epoch milliseconds UTC. **Defaults to now** |
| `location_id` | string (UUID) | No | Restrict to one location. Note the underscore — not `locationId` |
| `organization` | string | No | Defaults to the organization on your token |
| `order` | string | No | `asc` or `desc` |

**The window cannot exceed 30 days.** `to - from` greater than 30 days is rejected. For a longer
retrospective, page through it in chunks of 30 days or fewer.

**`location_id` is snake_case**, unlike almost every other parameter in this API (`sensorId`,
`accessPointId`, `serviceAreaId`). Passing `locationId` here is silently ignored rather than rejected,
so you'll get unfiltered results and no error to tell you why.

**Reading thresholds from either response shape:**

```python
def get_threshold(incident, name):
    # The list endpoint nests thresholds; the single-incident endpoint flattens them.
    thresholds = incident.get("thresholds")
    if thresholds is not None:
        return thresholds.get(name)
    return incident.get(name)
```

**Interpreting the timestamps** — there are four, and they mean different things:

| Field | Meaning |
|-------|---------|
| `startTimestamp` | When the degradation actually began |
| `timestampDeterminedToBeIncident` | When it had persisted long enough to qualify as an incident |
| `endTimestamp` | When it recovered |
| `asOfTimestamp` | When the record was last evaluated |

`timestampDeterminedToBeIncident` is always later than `startTimestamp` — the gap is roughly
`minIncidentDurationMinutes`. An incident still in progress has no meaningful `endTimestamp`.

**Judging severity** uses two numbers together: `countImpacted` against `populationCount`. Twelve
impacted devices out of 84 is a different problem from twelve out of thirteen. The
`minCountImpacted` / `minPercentImpacted` / `minPopulationCount` thresholds are the floors that had to be
crossed for the incident to be recorded at all.

**Getting epoch milliseconds in Python:**

```python
import time

now_ms = int(time.time() * 1000)
seven_days_ago_ms = now_ms - (7 * 24 * 60 * 60 * 1000)
```

**Finding a location ID:** location UUIDs come from `/locations/agents` — see
[Topologies, Networks, Access Points](07-topologies-networks-access-points.md).

## 4. Troubleshooting & FAQs

**Q: I passed no parameters and got a small result set. Is that everything?**

A: No — you got the last 24 hours, which is the default window. Pass `from` explicitly to look further
back, in windows of 30 days or less.

**Q: My `location_id` filter isn't filtering.**

A: Check the spelling. This endpoint uses `location_id` with an underscore, not `locationId`. An
unrecognised parameter is ignored rather than rejected, so the request succeeds and quietly returns
unfiltered results.

**Q: `incident["thresholds"]` raises a `KeyError`.**

A: You're reading a single-incident response, where the threshold fields are flat at the top level
instead of nested. Only the list response has a `thresholds` object. Use the `get_threshold()` helper
above to handle both shapes.

**Q: Where are `page` and `perPage`?**

A: This resource isn't paginated. The response is bounded by the time window and returns a `range`
object instead of a `pagination` object. Narrow `from`/`to` or `location_id` to reduce the result size.

**Q: `endTimestamp` looks wrong — it's earlier than `asOfTimestamp`.**

A: That's normal. `endTimestamp` is when the degradation recovered; `asOfTimestamp` is when the record
was last evaluated, which continues past recovery. They're measuring different things.

**Q: How do these relate to the alert incidents under `/alerting/incidents`?**

A: They're independent. Agent incidents are detected by the platform against its own service thresholds
and cannot be configured. Alert incidents come from rules you create yourself — see
[Alerting](16-alerting.md). A single real-world problem may well show up in both.

**Q: What values can `type` take?**

A: The field is an open string rather than a fixed enum in the specification, so treat it as a label to
display and group by rather than something to branch on exhaustively. Don't assume the set you observe
today is complete.
