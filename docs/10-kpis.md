# KPIs

> **Deprecation Notice:** The `/kpis/*` endpoints are deprecated and will be removed in a future release. They have been replaced by the [Time Series](09-time-series.md) endpoints. See [migration/kpi-endpoints.md](migration/kpi-endpoints.md) for the migration guide.

## 1. Overview

The KPI (Key Performance Indicator) endpoints retrieve performance data for both sensors and agents. This allows for analysis at different levels of granularity including organizations, locations, access points, etc.

The API is divided into two categories:

- **Sensors:** Endpoints to retrieve KPI data related to network sensors.
- **Agents:** Endpoints to retrieve KPI data related to client agents.

## 2. Endpoints

### Sensors

These endpoints require `kpiCodes` (e.g., `HC001`, `HC002`, `HC003`, etc.).

#### `GET /kpis/sensors/organizations`

Retrieves KPI data for sensors by organization.

```json
{
  "results": [
    {
      "kpiCode": "string",
      "name": "string",
      "description": "string",
      "measurements24GHz": [
        {
          "kpiValue": 0,
          "status": "string",
          "created_at": "string"
        }
      ],
      "measurements5GHz": [
        {
          "kpiValue": 0,
          "status": "string",
          "created_at": "string"
        }
      ]
    }
  ]
}
```

#### `GET /kpis/sensors/locations/{locationId}`

Retrieves KPI data for sensors by location. Requires `locationId`.

#### `GET /kpis/sensors/service-areas/{serviceAreaId}`

Retrieves KPI data for sensors by service area. Requires `serviceAreaId`.

#### `GET /kpis/sensors/eyes/{sensorId}`

Retrieves KPI data for a specific sensor. Requires `sensorId`.

#### `GET /kpis/sensors/access-points/{accessPointId}`

Retrieves KPI data for sensors by access point. Requires `accessPointId`.

#### `GET /kpis/sensors/dest-nw-band-loc/{targetId}`

Retrieves KPI data for sensors by destination, network, band, and location. Requires `targetId`.

### Agents

These endpoints require the `type` parameter.

**Available types:** `DOWNLOAD_MOS_SCORE`, `DOWNLOAD_THROUGHPUT`, `GATEWAY_PING_RTT`, `GATEWAY_PING_SUCCESS_RATE`, `PING_RTT`, `PING_SUCCESS_RATE`, `ROAMING`, `SIGNAL_STRENGTH`, `UPLOAD_MOS_SCORE`, `UPLOAD_THROUGHPUT`, `WEB_DOWNLOAD_DURATION`, `WEB_DOWNLOAD_SUCCESS_RATE`, `ADJACENT_CHANNEL_INTERFERENCE`, `CO_CHANNEL_INTERFERENCE`, `RF_PROBLEM`, `CONGESTION`, `COVERAGE`, `SEVEN_MCS`

#### `GET /kpis/agents`

Retrieves KPI data for agents.

```json
{
  "results": [
    {
      "clientCount": 0,
      "types": [
        {
          "id": "Unknown Type: type",
          "criticalSum": 0,
          "warningSum": 0,
          "goodSum": 0
        }
      ]
    }
  ],
  "range": {
    "to": 1674055815825,
    "toAsDateString": "string",
    "from": 1674055815825,
    "fromAsDateString": "string",
    "total": 5,
    "duration": 60000,
    "durationAsString": "60 seconds"
  }
}
```

#### `GET /kpis/agents/access-points`

Retrieves KPI data for agents by access point.

#### `GET /kpis/agents/adapter-drivers`

Retrieves KPI data for agents by adapter and driver.

#### `GET /kpis/agents/locations`

Retrieves KPI data for agents by location.

#### `GET /kpis/agents/client-capabilities`

Retrieves KPI data for agents by client capabilities.

> **Note:** Available `type` options for this endpoint: `connection`, `band`.

## 3. Developer Tips

Use query parameters to refine results:

- **Agents:** epoch time (in milliseconds), `ssid`, `band`, `location`
- **Sensors:** epoch time (in milliseconds), `networkId`, `band`, `averaging`, `timelimit`, `clientMac`

**Defaults:**

- `to`/`from` defaults to the last 24 hours
- `band` defaults to all bands
- `networkId` defaults to the first available
- `averaging` defaults to 1 hour
- Agents: `type`, `ssid`, `band`, `location` default to all (they narrow results when provided)

## 4. Troubleshooting & FAQs

**Q: What does the 404 Not Found error mean when calling the APIs?**

A: The specified ID (e.g., `locationId`, `sensorId`) may be invalid or does not exist.

**Q: Why are results empty for some endpoints?**

A: There may be no KPI data available for the selected parameters.

**Q: How can I optimize calls if I need to access multiple KPIs?**

A: Use the organization or location endpoints first to gather higher-level insight before narrowing down to service areas, access points, etc.
