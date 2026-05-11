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

## 3. Developer Tips

- There is no way to delete sensors via an endpoint. Contact 7SIGNAL support to remove sensors.
- Pagination for the Eyes endpoints starts at page 1.
