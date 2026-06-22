# Impact

## 1. Overview

The Impact endpoints return metrics that quantify how many minutes agents were experiencing degraded Wi-Fi performance within a time range. Impact is broken down by root cause category — coverage, congestion, interference, connectivity, roaming, and overall experience score — giving you a clear picture of where users are being affected and why.

The API covers four views of the same underlying data: an aggregate summary, per-agent details, a status-bucket breakdown, a time series, and a per-location rollup.

## 2. Endpoints

#### `GET /impact/agents/summary`

Returns a single aggregate summary of impact metrics across all agents in the organization.

```json
{
  "results": [
    {
      "deviceCount": 142,
      "minutesMonitored": 204480,
      "minutesImpactedExperienceScore": 8320,
      "minutesImpactedConnectivity": 1440,
      "minutesImpactedCoverage": 2880,
      "minutesImpactedCongestion": 960,
      "minutesImpactedInterference": 720,
      "minutesImpactedRoaming": 480
    }
  ],
  "pagination": { "page": 1, "pages": 1, "total": 1, "perPage": 20 }
}
```

#### `GET /impact/agents`

Returns per-agent impact metrics. Each result row identifies a device and its breakdown of impacted minutes.

```json
{
  "results": [
    {
      "deviceId": "abc123",
      "deviceName": "MacBook-Joe",
      "minutesMonitored": 1440,
      "minutesImpactedExperienceScore": 60,
      "minutesImpactedConnectivity": 10,
      "minutesImpactedCoverage": 20,
      "minutesImpactedCongestion": 5,
      "minutesImpactedInterference": 3,
      "minutesImpactedRoaming": 2
    }
  ],
  "pagination": { "page": 1, "pages": 5, "total": 142, "perPage": 20 }
}
```

#### `GET /impact/agents/by-status`

Returns impact metrics grouped into status buckets based on impacted-minutes thresholds. Useful for understanding the distribution of impact severity across your fleet.

Optional filters: `minImpactedMinutes`, `maxImpactedMinutes`

#### `GET /impact/agents/time-series`

Returns agent impact metrics bucketed by time with configurable granularity. Use this endpoint to identify trends — for example, whether congestion spikes during business hours.

Additional parameters:
- `granularity` — `HOUR`, `DAY`, or `MONTH` (default: `HOUR`)
- `timezone` — IANA timezone string (e.g., `America/New_York`)

```json
{
  "results": [
    {
      "timestamp": 1718755200000,
      "deviceCount": 130,
      "minutesMonitored": 7800,
      "minutesImpactedExperienceScore": 312,
      "minutesImpactedCoverage": 120,
      "minutesImpactedCongestion": 60
    }
  ],
  "pagination": { "page": 1, "pages": 24, "total": 24, "perPage": 1 }
}
```

#### `GET /impact/locations`

Returns impact metrics rolled up per physical location. Helps identify which sites have the most affected users.

```json
{
  "results": [
    {
      "locationId": "loc-001",
      "locationName": "Headquarters - Floor 3",
      "deviceCount": 38,
      "minutesMonitored": 54720,
      "minutesImpactedExperienceScore": 2180,
      "minutesImpactedConnectivity": 420,
      "minutesImpactedCoverage": 780
    }
  ],
  "pagination": { "page": 1, "pages": 3, "total": 12, "perPage": 5 }
}
```

## 3. Developer Tips

**Common query parameters (all endpoints):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from` | integer | Yes | Start of time range (epoch milliseconds) |
| `to` | integer | Yes | End of time range (epoch milliseconds) |
| `organization` | string | No | Filter by organization (defaults to your JWT org) |
| `page` | integer | No | Page number, starting at 1 |
| `perPage` | integer | No | Records per page |

**Getting epoch milliseconds in Python:**

```python
import time

# Current time in milliseconds
now_ms = int(time.time() * 1000)

# 24 hours ago
yesterday_ms = now_ms - (24 * 60 * 60 * 1000)
```

**Choosing the right endpoint:**
- Use `/summary` when you need a quick org-wide health check
- Use `/agents` when you need to identify specific affected devices
- Use `/time-series` with `DAY` granularity for weekly trend charts
- Use `/locations` when you want to prioritize site-level remediation

## 4. Troubleshooting & FAQs

**Q: My results are empty even though I know agents were online during the time range.**

A: Impact data is only generated for agents that experienced measurable degradation. Agents with healthy Wi-Fi throughout the window will not appear in `/agents` results, though they do contribute to `minutesMonitored` in the `/summary` response.

**Q: What is `minutesImpactedExperienceScore` vs. the individual category fields?**

A: `minutesImpactedExperienceScore` reflects minutes where the overall experience score dropped below threshold — it can overlap with category-specific fields since poor coverage or congestion also degrades the experience score. The category fields (coverage, congestion, etc.) are independent counts of minutes where that specific root cause was detected.

**Q: How far back can I query?**

A: The available history depends on your 7SIGNAL subscription. If the time range returns no data, try narrowing it to the past 7 days and expand outward.
