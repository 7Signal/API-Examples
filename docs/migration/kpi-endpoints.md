# Migration Notes: KPI Endpoints

Gateway API KPI endpoints have been deprecated and will be removed in a future release. They have been replaced by the [Time Series endpoints](../09-time-series.md).

## Deprecated Endpoints

- `/kpis/agents`
- `/kpis/agents/access-points`
- `/kpis/agents/adapter-drivers`
- `/kpis/agents/locations`
- `/kpis/agents/client-capabilities`
- `/kpis/sensors/organizations`
- `/kpis/sensors/access-points/{accessPointId}`
- `/kpis/sensors/dest-nw-band-loc/{targetId}`
- `/kpis/sensors/locations/{locationId}`
- `/kpis/sensors/eyes/{sensorId}`
- `/kpis/sensors/service-areas/{serviceAreaId}`

## Time Series Endpoint Overview

The Time Series endpoints follow a consistent structure across all Agent and Sensor endpoints.

### Agent Endpoints

| **Endpoint** | **Description** |
| --- | --- |
| `/time-series/agents/discrete/{groupByDimension}` | Discrete data (e.g., `BAND`, `CHANNEL`) |
| `/time-series/agents/numeric/{groupByDimension}` | Numeric data (e.g., `CLIENT_COUNT`, `EXPERIENCE_SCORE`) |
| `/time-series/agents/histogram/{groupByDimension}` | Data bucketed into grade categories |
| `/time-series/agents/numeric-summary` | Numeric summary across the whole organization |
| `/time-series/agents/numeric-summary/{groupByDimension}` | Numeric summary by dimension |
| `/time-series/agents/metric-types` | Available metric types and descriptions |

### Sensor Endpoints

| **Endpoint** | **Description** |
| --- | --- |
| `/time-series/sensors/numeric` | Numeric data across the whole organization |
| `/time-series/sensors/numeric/{groupByDimension}` | Numeric data by dimension |
| `/time-series/sensors/numeric-summary` | Summary across the whole organization |
| `/time-series/sensors/numeric-summary/{groupByDimension}` | Summary by dimension |
| `/time-series/sensors/metric-types` | Available metric types (KPI codes) and descriptions |

## KPI → Time Series Endpoint Mapping

| **Deprecated** | **New** |
| --- | --- |
| `/kpis/agents` | TBD |
| `/kpis/agents/access-points` | TBD |
| `/kpis/agents/adapter-drivers` | TBD |
| `/kpis/agents/locations` | `/time-series/agents/discrete/locationId` or `/time-series/agents/numeric/locationId` |
| `/kpis/agents/client-capabilities` | TBD |
| `/kpis/sensors/organizations` | `/time-series/sensors/numeric` |
| `/kpis/sensors/access-points/{accessPointId}` | `/time-series/sensors/numeric/accessPoint` |
| `/kpis/sensors/dest-nw-band-loc/{targetId}` | No corresponding group-by dimension currently |
| `/kpis/sensors/locations/{locationId}` | `/time-series/sensors/numeric/locationId` |
| `/kpis/sensors/eyes/{sensorId}` | `/time-series/sensors/numeric/sensor` |
| `/kpis/sensors/service-areas/{serviceAreaId}` | `/time-series/sensors/numeric/serviceArea` |

## Parameter Migration Guide

1. **Time range:** `from` and `to` — no change (milliseconds from epoch).
2. **Averaging → timeBucket:** Replace `averaging` with `timeBucket`. Allowed values: `1_MIN`, `10_MIN`, `1_HOUR`, `1_DAY`, `1_MONTH`.
3. **timelimit:** Drop this parameter — it is not used with Time Series endpoints. The limit is enforced at 120 records max; adjust `timeBucket` or shorten the time range if needed.
4. **kpiCodes → metrics:** Same metric/KPI code values. You should send multiple codes per request to reduce total requests.
5. **aggregateFunctions (new, required):** Specify which aggregations to return (`SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `PCTL`, etc.). Check the OpenAPI Spec for supported functions per endpoint.
6. **Filters:** Agent and Sensor Time Series endpoints each have a fixed set of filters (all Agents endpoints share the same filters; same for Sensors). See the [OpenAPI Spec / Swagger UI](https://api-v2.7signal.com/swagger-ui/index.html) for the full list.
7. **Pagination:** Same parameters. Pagination happens at the metric level — if you request 10 metrics with page size 5, you get 2 pages. Time series data per metric is not paginated (max 120 data points).

## Response Format Notes

The Time Series response format is consistent across all endpoints (Agent and Sensor):

1. Top-level object contains `results` and `pagination`.
2. Each entry in `results` contains:
   - The filter dimensions that were applied (omitted if not applied)
   - A `metricAggregates` array, each element containing:
     - `metric` — the metric key
     - `kpiCode` — the KPI code for the metric
     - Aggregate values (`min`, `max`, `avg`, `sum`, `count`) based on selected functions — these are summaries across the entire time series
     - `threshold` — threshold for the metric
     - `timeSeries` — array of data points per `timeBucket`, each with:
       - `ts` — epoch timestamp in UTC
       - The selected aggregate values for that bucket
