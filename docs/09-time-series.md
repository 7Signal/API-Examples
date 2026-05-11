# Time Series

## 1. Overview

The Time Series API allows the retrieval of time series data for performance, connectivity, and usage metrics. Four aggregation methods are supported:

- **Numeric** — continuous values over time, like "Signal Strength" or "Throughput"
- **Discrete** — categorical/event-based values over time, like "Network" or "Connection Type"
- **Numeric Summary** — statistical summaries per time bucket. An "overall" result for the whole period with no time-based breakdown.
- **Histogram** — frequency distribution of values
- **Metric Types** — a list of possible metrics (KPIs)

Each function, except for "histogram", supports specific aggregate functions and metrics.

> **Migration note:** The `/kpis/*` endpoints are deprecated. See [migration/kpi-endpoints.md](migration/kpi-endpoints.md) for the mapping to Time Series endpoints.

## 2. Common Parameters

| **Parameter** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| `groupByDimension` | string | Yes | `band`, `bssid`, `deviceId`, `driverProvider`, `driverVersion`, `locationId`, `make`, `model`, `network`, `platform`, `target`, `serviceArea`, `accessPoint`, `sensor` |
| `from` | integer | Yes | Time in milliseconds from epoch (lower bound) |
| `to` | integer | Yes | Time in milliseconds from epoch (upper bound) |
| `timeBucket` | string | Yes | `1_MIN`, `10_MIN`, `15_MIN`, `1_HOUR`, `2_HOUR`, `1_DAY`, `1_WEEK`, `1_MONTH` (use summary endpoints to group everything into one bucket) |
| `filters` | — | No | `deviceIds`, `bssids`, `locations`, `networks`, `bands`, `targets`, `platforms`, `makes`, `models`, `driverProviders`, `driverVersion`, `serviceAreas`, `accessPoints`, `sensorIds` |

## 3. Endpoints (Agents)

### `GET /time-series/agents/metric-types`

Returns all possible metrics that can be charted, with descriptions and other useful information.

The "keys" in the resulting object (e.g., `CHANNEL_UTILIZATION`) are the metric types used in the agents time-series endpoints.

```json
{
  "CHANNEL_UTILIZATION": {
    "name": "Channel Utilization",
    "description": "Percentage of channel busy time",
    "unit": "%"
  },
  "EXPERIENCE_SCORE": {
    "name": "Experience Score",
    "description": "User experience quality score",
    "unit": ""
  }
}
```

### `GET /time-series/agents/numeric/{groupByDimension}`

Retrieves time series data with numeric aggregation for agents.

**Aggregate functions:** `SUM`, `AVG`, `GRADE`, `MIN`, `MAX`, `COUNT`

**Metrics:** See `/time-series/agents/metric-types`

**Example request parameters:**
- `groupByDimension`: `make`
- `from`: `1755129600000`
- `to`: `1755201896000`
- `timeBucket`: `2_HOUR`
- `aggregateFunctions`: `AVG`
- `metrics`: `EXPERIENCE_SCORE`

```json
{
  "results": [
    {
      "make": "Apple",
      "metricAggregates": [
        {
          "metric": "EXPERIENCE_SCORE",
          "avg": 0.8871398620543564,
          "threshold": 90,
          "timeSeries": [
            { "ts": 1755129600000, "avg": 0.8612683891271695 },
            { "ts": 1755136800000, "avg": 0.880920680494529 },
            { "ts": 1755144000000, "avg": 0.855512750455373 }
          ]
        }
      ]
    }
  ]
}
```

### `GET /time-series/agents/discrete/{groupByDimension}`

Retrieves time series data with discrete aggregation for agents.

**Aggregate functions:** `MODE`, `COUNT`

**Metrics:** See `/time-series/agents/metric-types`

**Example request parameters:**
- `groupByDimension`: `model`
- `from`: `1755129600000`
- `to`: `1755201896000`
- `timeBucket`: `2_HOUR`
- `aggregateFunctions`: `MODE`
- `metrics`: `NETWORK`

```json
{
  "results": [
    {
      "model": "21A7002MUS",
      "metricAggregates": [
        {
          "metric": "NETWORK",
          "timeSeries": [
            { "ts": 1755129600000, "value": "string" },
            { "ts": 1755136800000, "value": "string" }
          ]
        }
      ]
    }
  ]
}
```

### `GET /time-series/agents/numeric-summary/{groupByDimension}`

Returns a single set of aggregated results for the entire period (no time breakdown).

**Aggregate functions:** `SUM`, `AVG`, `GRADE`, `MIN`, `MAX`, `COUNT`

**Example response:**

```json
{
  "pagination": {
    "perPage": 20,
    "page": 0,
    "total": 4,
    "pages": 1
  },
  "results": [
    {
      "make": "Apple",
      "metric": "THROUGHPUT_DOWNLOAD",
      "unit": "Mbps",
      "avg": 171.28350698602793,
      "threshold": 3,
      "score": 0.9940119760479041,
      "grade": "A"
    },
    {
      "make": "Dell Inc.",
      "metric": "THROUGHPUT_DOWNLOAD",
      "unit": "Mbps",
      "avg": 116.73108579088472,
      "threshold": 3,
      "score": 0.9195710455764075,
      "grade": "A"
    }
  ]
}
```

### `GET /time-series/agents/histogram/{groupByDimension}`

Returns a count of items for each aggregation period arranged by "grade". Only one metric can be specified.

**Example request parameters:**
- `groupByDimension`: `make`
- `from`: `176352840000`
- `to`: `1763614799000`
- `timeBucket`: `2_HOUR`
- `metrics`: `ROAMING`

```json
{
  "results": [
    {
      "timestamp": 1763532000000,
      "bins": { "a": 4, "b": 0, "c": 0, "d": 0, "f": 0 }
    },
    {
      "timestamp": 1763539200000,
      "bins": { "a": 4, "b": 0, "c": 0, "d": 0, "f": 0 }
    }
  ]
}
```

## 4. Endpoints (Sensors)

### `GET /time-series/sensors/metric-types`

Returns all possible metrics (KPIs) that can be charted for sensors.

> **Note:** For sensor endpoints, use the `kpiCode` value, not the metric name.

```json
{
  "RADIO_ATTACH_SUCCESS_RATE": {
    "kpiCode": "AC001",
    "name": "Radio attach success rate",
    "description": "The radio attach is a combination of authentication and association...",
    "unit": "%",
    "aggregation": "NO"
  },
  "DHCP_SUCCESS_RATE": {
    "kpiCode": "AC002",
    "name": "DHCP success rate",
    "description": "The KPI is calculated as the amount of successful IP address retrievals divided by all the requests by Eye...",
    "unit": "%",
    "aggregation": "NO"
  }
}
```

### `GET /time-series/sensors/numeric/{groupByDimension}`

Returns time series data with numeric aggregation for sensors.

**Variation:** `GET /time-series/sensors/numeric` (no `groupByDimension`) returns values for the entire organization.

**Aggregate functions:** `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `PCTL`

> **Note:** Some metrics / KPI codes don't support all aggregate functions.

**Example request parameters:**
- `groupByDimension`: `serviceArea`
- `from`: `1763566588000`
- `to`: `1763652988000`
- `timeBucket`: `1_HOUR`
- `aggregateFunctions`: `AVG, COUNT`
- `metrics`: `HC005` (WIFI_CONNECTIVITY), `AC001` (RADIO_ATTACH_SUCCESS_RATE)

```json
{
  "pagination": {
    "perPage": 3,
    "page": 1,
    "pages": 1,
    "total": 3
  },
  "results": [
    {
      "serviceAreaId": 255,
      "metricAggregates": [
        {
          "metric": "WIFI_CONNECTIVITY",
          "avg": 0.992,
          "count": 1595,
          "threshold": 100,
          "timeSeries": [
            { "ts": 1763564400000, "avg": 1, "count": 28 },
            { "ts": 1763568000000, "avg": 0.9852941176470589, "count": 66 }
          ]
        }
      ]
    }
  ]
}
```

### `GET /time-series/sensors/numeric-summary/{groupByDimension}`

Returns a single aggregated result for the entire period (no time breakdown).

**Variation:** `GET /time-series/sensors/numeric-summary` (no `groupByDimension`) returns values for the entire organization.

```json
{
  "pagination": {
    "perPage": 1,
    "page": 1,
    "pages": 1,
    "total": 1
  },
  "results": [
    {
      "metric": "RADIO_ATTACH_SUCCESS_RATE",
      "unit": "%",
      "avg": 98.3811,
      "count": 803,
      "threshold": 100,
      "sensorId": "21479"
    }
  ]
}
```

## 5. Developer Tips

- Some metrics may not support all aggregate functions. Expect that unsupported functions will be omitted from results.
- Use shorter `timeBucket` values for granular data and larger buckets for summaries.
- Apply filters to limit scope and improve performance.
- Time Series endpoints cap at 120 data points per metric. If you exceed this, adjust `timeBucket` or shorten the time range.

## 6. Troubleshooting & FAQs

**Q: Why am I getting no results?**

A: Check the `from` and `to` timestamps — make sure they are in milliseconds.

**Q: How do I calculate averages and totals in the same call?**

A: Select multiple values in the `aggregateFunctions` parameter.
