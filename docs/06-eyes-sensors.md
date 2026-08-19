# Eyes (Sensors)

## 1. Overview

The Eyes Sensors endpoints provide access to manage Eye Sensors, which are 7SIGNAL's hardware sensors for monitoring WiFi. These endpoints support retrieving, modifying, and registering Eye Sensors.

> **Note:** There is no way to delete sensors via an endpoint. Contact support to remove sensors.

## 2. Endpoints

### `GET /eyes/sensors`

Returns a list of all registered Eyes Sensors.

```json
{
  "results": [
    {
      "commonId": 1001,
      "commonName": "Golden Eye",
      "description": "string",
      "parentLocationId": 0,
      "parentLocationName": "Default",
      "parentServiceAreaId": "string",
      "parentServiceAreaName": "Office",
      "eyeStatus": "ACTIVE",
      "ledStatus": "NORMAL_MODE",
      "eyeSoftware": "string",
      "hardwareVersion": "string",
      "ipV4Address": "10.10.10.10",
      "lastTestResultStoredTimestamp": "2025-08-01T18:53:32.887Z",
      "topologyType": "EYE",
      "antennaArray": true,
      "timeZone": "America/New_York",
      "vht160Support": true,
      "ethernetMACAddress": "string",
      "wlan24MACAddress": "string",
      "wlan5MACAddress": "string"
    }
  ]
}
```

### `GET /eyes/sensors/{sensorId}`

Gets details of a specific Eyes Sensor. Requires `sensorId`.

```json
{
  "commonId": 1001,
  "commonName": "Golden Eye",
  "description": "string",
  "parentLocationId": 0,
  "parentLocationName": "Default",
  "parentServiceAreaId": "string",
  "parentServiceAreaName": "Office",
  "eyeStatus": "ACTIVE",
  "ledStatus": "NORMAL_MODE",
  "eyeSoftware": "string",
  "hardwareVersion": "string",
  "ipV4Address": "10.10.10.10",
  "lastTestResultStoredTimestamp": "2025-08-01T19:02:34.464Z",
  "topologyType": "EYE",
  "antennaArray": true,
  "timeZone": "America/New_York",
  "vht160Support": true,
  "ethernetMACAddress": "string",
  "wlan24MACAddress": "string",
  "wlan5MACAddress": "string"
}
```

### `PATCH /eyes/sensors/{sensorId}`

Updates one or more Eyes Sensors. Requires `sensorId`. The optional parameter is `ledStatus`.

**Request:**

```json
{
  "ledStatus": "NORMAL_MODE"
}
```

**Response:**

```json
{
  "commonId": 1001,
  "commonName": "Golden Eye",
  "description": "string",
  "parentLocationId": 0,
  "parentLocationName": "Default",
  "parentServiceAreaId": "string",
  "parentServiceAreaName": "Office",
  "eyeStatus": "ACTIVE",
  "ledStatus": "NORMAL_MODE",
  "eyeSoftware": "string",
  "hardwareVersion": "string",
  "ipV4Address": "10.10.10.10",
  "lastTestResultStoredTimestamp": "2025-08-01T19:04:13.352Z",
  "topologyType": "EYE",
  "antennaArray": true,
  "timeZone": "America/New_York",
  "vht160Support": true,
  "ethernetMACAddress": "string",
  "wlan24MACAddress": "string",
  "wlan5MACAddress": "string"
}
```

### `POST /eyes/sensors/registration`

Registers a sensor and enables it to start monitoring. There won't be a sensor in `GET /eyes/sensors` until the hardware fetches the configuration, restarts, and begins operation.

> **Note:** This is equivalent to going through the registration process via the Mobile App, Website, or 7SIGNAL Support.

**Request:**

```json
{
  "macAddress": "string",
  "serialNumber": "string",
  "groupId": "..."
}
```

**Response:**

```json
{
  "macAddress": "string",
  "serialNumber": "string",
  "createdAt": "2025-08-01T19:05:38.296Z",
  "updatedAt": "2025-08-01T19:05:38.296Z"
}
```

### `GET /eyes/sensors/{sensorId}/automated-testing`

Returns the current automated-testing state of a sensor — what it is running, against which access point,
and where it is in its test profile.

This is the endpoint to check when an on-demand test appears stuck: on-demand tests do not start while
automated testing is actively running on the sensor.

**Required parameters:** `sensorId` (integer, in path)

**Response:**

```json
{
  "eyeName": "Eye-Cleveland-03",
  "testProfileName": "Standard Branch",
  "testStatus": "RUNNING",
  "currentTestStatus": "Test started",
  "currentAccessPoint": "AP-CLE-3-North",
  "currentTestRunning": "SPEEDTEST"
}
```

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| `eyeName` | string | Name of the sensor |
| `testProfileName` | string | Test profile currently applied |
| `testStatus` | string | `STOPPED`, `PAUSED`, `RUNNING`, `STOPPING`, or `UNKNOWN` |
| `currentTestStatus` | string | Free-text progress message, e.g. `"Test started"` |
| `currentAccessPoint` | string | Access point being tested against right now |
| `currentTestRunning` | string | The test type currently executing |

Note `STOPPING` is a transient state — a stop has been requested but the sensor has not finished winding
down. Poll until it reaches `STOPPED` rather than assuming the stop took effect immediately.

### `POST /eyes/sensors/{sensorId}/automated-testing`

Starts or stops automated testing on a sensor.

**Required parameters:** `sensorId` (integer, in path)

**Request:**

```json
{
  "action": "START_AUTOMATED_TESTING"
}
```

`action` must be exactly `START_AUTOMATED_TESTING` or `STOP_AUTOMATED_TESTING`.

**Response:**

```json
{
  "action": "START_AUTOMATED_TESTING",
  "result": "SUCCESS"
}
```

> **This changes live monitoring behaviour.** Stopping automated testing halts the scheduled measurements
> that KPIs, SLAs, and alerting are calculated from — gaps will appear in the data for as long as it stays
> stopped. Prompt for confirmation before sending this from a script, and remember to start it again.

The `result` field reports whether the request was accepted, not whether the sensor has finished
transitioning. Follow up with `GET .../automated-testing` and check `testStatus` to confirm the sensor
actually reached `RUNNING` or `STOPPED`.

## 3. Developer Tips

- There is no way to delete sensors via an endpoint. Use the Configurator app to remove sensors.
- Pagination for the Eyes endpoints starts at page 1.
- Automated testing and on-demand tests are mutually exclusive on a sensor. If an on-demand test is not
  starting, check `GET /eyes/sensors/{sensorId}/automated-testing` — a `testStatus` of `RUNNING` is the
  usual reason.
- `POST .../automated-testing` returns as soon as the action is accepted. Poll the `GET` to confirm the
  sensor reached the state you asked for; `STOPPING` means it is still winding down.
