# Agent Audit & User Summaries

## 1. Overview

Two small read-only endpoints covering account-level questions rather than network measurements:

- **Agent audit** (`/audit/agents`) — a searchable record of who did what to agents and when. Each entry
  names the actor, the action, where in the system it originated, and how it was initiated, plus a
  free-form `details` object carrying whatever is specific to that action.
- **User summaries** (`/summaries/users`) — headline counts of users in an organization and how many have
  logged in recently. A licence-and-adoption snapshot rather than a per-user list.

Both are read-only. Neither is expensive to call.

## 2. Endpoints

#### `GET /audit/agents`

Pages through agent audit records.

**Required parameters:** none

**Optional parameters:** `startTimeRange`, `endTimeRange`, `actor`, `action`, `source`, `initiated`,
`organization`, `page`, `perPage`, `sortField`, `order`

```json
{
  "results": [
    {
      "id": "d51c7a90-4f36-4b28-91e5-6c0a3f8b2d47",
      "timestamp": "2026-08-17T14:22:41Z",
      "organizationName": "globalcorp",
      "actor": "jdoe@example.com",
      "action": "PATCH_EYES_AGENT",
      "source": "GATEWAY",
      "initiated": "API",
      "details": {
        "agentId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "changedFields": ["nickname"]
      }
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 1,
    "total": 264,
    "pages": 27
  }
}
```

**The time range parameters take ISO-8601 date-time strings, not epoch milliseconds.** This is the only
place in the endpoints documented in this repository where that's true — see Developer Tips.

#### `GET /summaries/users`

Returns user counts for an organization.

**Required parameters:** none

**Optional parameters:** `organizationId` — note this is `organizationId`, **not** the `organization`
parameter used by nearly every other endpoint. Omit it to get the summary for your primary organization.

```json
{
  "total": 148,
  "loginLast30Days": 92,
  "loginLast90Days": 121
}
```

The counts are cumulative rather than exclusive: a user who logged in last week is counted in both
`loginLast30Days` and `loginLast90Days`.

## 3. Developer Tips

**Query parameters:**

| Parameter | Endpoint | Type | Description |
|-----------|----------|------|-------------|
| `startTimeRange` | audit | string | **ISO-8601 date-time**, e.g. `2026-08-01T00:00:00Z` |
| `endTimeRange` | audit | string | **ISO-8601 date-time** |
| `actor` | audit | string | User or system component responsible |
| `action` | audit | string | The action taken |
| `source` | audit | string | Area of the system the event came from |
| `initiated` | audit | string | How the event was initiated |
| `organization` | audit | string | Defaults to the organization on your token |
| `page` | audit | integer | **First page is 1**, not 0 |
| `perPage` | audit | integer | Records per page |
| `sortField` | audit | string | Field to sort on |
| `order` | audit | string | `asc` or `desc` |
| `organizationId` | summaries | string | **Not** `organization` — different parameter name |

**Time format on `/audit/agents` differs from the rest of the API.** Most endpoints here take epoch
milliseconds; this one takes ISO-8601 strings, and `timestamp` on each record comes back as an ISO-8601
string too:

```python
import time

# Most endpoints in this API — epoch milliseconds
now_ms = int(time.time() * 1000)

# /audit/agents — ISO-8601, UTC
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
params = {
    "startTimeRange": (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "endTimeRange": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
}
```

Passing an epoch-millisecond integer here returns a `400`.

**The parameter is `organizationId` on `/summaries/users`.** Elsewhere it's `organization`. An
unrecognised parameter is ignored rather than rejected, so passing `organization` here quietly returns the
summary for your primary organization instead of the one you asked for — a wrong answer with no error.
Worth an explicit check in any script that reports per-organization figures.

**`details` is free-form and varies by action.** Its shape depends on `action` and `source`, so treat it
defensively rather than assuming a schema:

```python
details = record.get("details") or {}
agent_id = details.get("agentId", "(not recorded)")
```

Don't build code that requires a particular key to be present across all records.

**`actor`, `action`, `source`, and `initiated` are open strings, not enums.** They're filterable and
useful for grouping, but the specification doesn't fix their value sets — don't write exhaustive
`if/elif` chains over them, and don't assume the values you see today are all of them.

**Filters are exact-match**, unlike the partial matching on
[Sensor Clients](21-sensor-clients-and-change-events.md)'s `mac` and `vendor`. To discover the values in
play, fetch a page unfiltered and collect the distinct ones:

```python
actions = sorted({r.get("action") for r in records if r.get("action")})
```

**Interpreting login counts.** `total` counts users in the organization; the two login figures count how
many of them signed in within the trailing window. `total - loginLast90Days` is a reasonable proxy for
dormant accounts worth reviewing.

## 4. Troubleshooting & FAQs

**Q: `startTimeRange` returns a `400` and I passed a timestamp.**

A: You almost certainly passed epoch milliseconds. This endpoint wants ISO-8601 date-time strings, e.g.
`2026-08-01T00:00:00Z`. The epoch-millisecond convention used elsewhere in this API doesn't apply here.

**Q: `/summaries/users` ignores my organization and returns the wrong numbers.**

A: The parameter is `organizationId` on this endpoint, not `organization`. Unrecognised parameters are
ignored rather than rejected, so the request succeeds and falls back to your primary organization.

**Q: `record["details"]["agentId"]` raises a `KeyError` on some records.**

A: `details` is a free-form object whose contents depend on the action and source. Some actions record no
`agentId` at all. Use `.get()` with a default throughout.

**Q: My `action` filter returns nothing even though I can see that action in the results.**

A: Filtering is exact-match and case-sensitive. Copy the value verbatim from a record rather than typing
it from memory — `PATCH_EYES_AGENT` won't match `patch_eyes_agent`.

**Q: `loginLast30Days` plus `loginLast90Days` is more than `total`. Is that a bug?**

A: No. The windows overlap — anyone who logged in during the last 30 days is also counted in the last 90.
Don't add them together. For an estimate of dormant accounts, use `total - loginLast90Days`.

**Q: Is there an audit trail for sensors, or for things other than agents?**

A: This endpoint covers agents. Sensor-side configuration changes are available through
`GET /change-events/sensors` — see
[Sensor Clients & Change Events](21-sensor-clients-and-change-events.md). The two have different shapes
and different filters.

**Q: Can I get a per-user list rather than counts?**

A: Not from this endpoint — it returns aggregates only. Use `/users` for the per-user list, described in
[User Management](03-user-management.md).
