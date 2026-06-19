# Scans

## 1. Overview

The Scans endpoints return raw RF scan data collected by 7SIGNAL agents and sensors as they passively observe the wireless environment. Each scan record contains a timestamp and a list of detected access points with details such as BSSID, SSID, signal strength, channel, and band. Sensor scan records additionally include noise floor readings for each AP.

Scan data is useful for RF environment analysis, rogue AP detection, channel utilization studies, and historical airtime visibility.

## 2. Endpoints

#### `GET /scans/agents`

Returns paginated RF scan records collected by a specific agent. Each record groups the APs detected during a single scan pass, along with the BSSID and SSID the agent was connected to at that moment.

**Required parameters:** `agentId` (UUID), `start` (epoch ms), `end` (epoch ms)

```json
{
  "pagination": {
    "page": 0,
    "pages": 3,
    "total": 48,
    "perPage": 20
  },
  "scans": [
    {
      "timestamp": 1718755200000,
      "agentConnectedBssid": "aa:bb:cc:dd:ee:ff",
      "agentConnectedSsid": "CorpWiFi",
      "data": [
        {
          "bssid": "aa:bb:cc:dd:ee:ff",
          "ssid": "CorpWiFi",
          "signalStrength": -58,
          "channel": 36,
          "channelWidth": 80,
          "band": 5,
          "stationCount": 12
        }
      ]
    }
  ]
}
```

#### `GET /scans/sensors`

Returns paginated RF scan records collected by a specific sensor (eye). Sensor scans cover a broader view of the RF environment and include a `noise` field (dBm) for each detected AP, which agents do not report.

**Required parameters:** `sensorId` (integer), `start` (epoch ms), `end` (epoch ms)

```json
{
  "pagination": {
    "page": 0,
    "pages": 5,
    "total": 96,
    "perPage": 20
  },
  "scans": [
    {
      "timestamp": 1718755200000,
      "data": [
        {
          "bssid": "aa:bb:cc:dd:ee:ff",
          "ssid": "CorpWiFi",
          "signalStrength": -55,
          "noise": -92,
          "channel": 36,
          "channelWidth": 80,
          "band": 5,
          "stationCount": 14
        }
      ]
    }
  ]
}
```

## 3. Developer Tips

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agentId` | string (UUID) | Yes (agents) | The UUID of the agent |
| `sensorId` | integer | Yes (sensors) | The numeric ID of the sensor |
| `start` | integer | Yes | Start of time range (epoch milliseconds, UTC) |
| `end` | integer | Yes | End of time range (epoch milliseconds, UTC) |
| `page` | integer | No | Page number (0-based, default: 0) |
| `size` | integer | No | Records per page (default: 20, max: 1000) |

**Pagination note:** Unlike most other API endpoints in this repo, the Scans endpoints use 0-based page numbering (first page = `0`) and the `size` parameter instead of `perPage`.

**Getting epoch milliseconds in Python:**

```python
import time

# Current time in milliseconds
now_ms = int(time.time() * 1000)

# 1 hour ago
one_hour_ago_ms = now_ms - (60 * 60 * 1000)
```

**Finding your agent ID or sensor ID:**

- Agent IDs (UUID format) are available from the `/eyes/agents` endpoint
- Sensor IDs (integers) are available from the `/eyes/sensors` endpoint

**Signal strength interpretation:**
- `-50 dBm` and above: Excellent
- `-60 to -50 dBm`: Good
- `-70 to -60 dBm`: Fair
- Below `-70 dBm`: Poor

## 4. Troubleshooting & FAQs

**Q: I get an empty `scans` array even though the agent/sensor was active.**

A: Scan data retention depends on your 7SIGNAL subscription tier. Try a shorter, more recent time window. Also confirm the agent or sensor ID is correct by looking it up via `/eyes/agents` or `/eyes/sensors`.

**Q: What is the difference between agent scans and sensor scans?**

A: Agents are end-user devices (laptops, mobile devices) running the 7SIGNAL client. Their scans reflect the RF environment as seen by a client. Sensors are dedicated 7SIGNAL hardware deployed in the environment; they scan more frequently, from a fixed vantage point, and report a noise floor value that agents do not.

**Q: The `agentConnectedBssid` field is null — is that an error?**

A: No. If the agent was not associated to any AP at the time of the scan, both `agentConnectedBssid` and `agentConnectedSsid` will be null. This is normal for disconnection events or brief roaming gaps.
