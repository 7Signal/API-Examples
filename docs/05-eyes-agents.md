# Eyes (Agents)

## 1. Overview

The Eyes API provides endpoints for retrieving, modifying, and deleting Agents. These Agents are entities used to monitor/process specific resources. The endpoints support listing all agents, fetching specific information, patching agents, searching, and deleting.

## 2. Endpoints

### `GET /eyes`

Returns a summary of all Eyes (Agents + Sensors) by aggregating data from two different backend systems.

Optional filter parameters: `organizationId`, `organization`, `eyesType`.

- `organization`: the Agent organization code (e.g., `globalcorp`)
- `organizationId`: the UUID of the organization (retrieve from `GET /organizations`)

```json
{
  "agents": {
    "organizationName": "string",
    "deviceCount": 0,
    "licenseSummary": {
      "packageName": "string",
      "totalLicenses": 1000,
      "usedLicenses": 750,
      "freeLicenses": 250
    },
    "platformSummary": {
      "android": 100,
      "linux": 25,
      "mac": 75,
      "windows": 50
    }
  },
  "sensors": {
    "deviceCount": 300,
    "deviceStatusSummary": {
      "active": 150,
      "passive": 75,
      "unconfigured": 50,
      "maintenance": 25
    },
    "modelSummary": {
      "250": 2,
      "2200": 5,
      "6300": 10
    }
  }
}
```

### `GET /eyes/agents`

Lists all available Agents. Supports pagination and limited strict filtering (e.g., filtering for `mac` only returns values that contain `mac` exactly).

```json
{
  "results": [
    {
      "id": "...",
      "name": "desktop-1234.company.example.com",
      "manufacturer": "samsung",
      "model": "SM-G930V",
      "platform": "android",
      "version": "7.0",
      "mac": "48:49:11:46:53:30",
      "lastSeen": 1672456149773,
      "lastSsid": "foo-ssid.5G",
      "lastTestSeen": 1672456149773,
      "lastAgentVersion": "4.7.2+6217",
      "remoteIpAddress": "198.51.100.25",
      "numberOfTxSpatialStreams": 2,
      "numberOfRxSpatialStreams": 2,
      "lastDefinedLocationId": "...",
      "locationPermissionStatus": "GRANTED",
      "readAccountPermissionStatus": "GRANTED",
      "backgroundLocationPermissionStatus": "GRANTED",
      "writeExternalStoragePermissionStatus": "GRANTED",
      "lastBssid": "88:74:4E:61:8D:2D",
      "localIpAddress": "198.168.0.25",
      "isLicensed": false,
      "lastDefinedLocation": "Corporate Office",
      "marketModel": "Samsung Galaxy S7 (SM-G930V)"
    }
  ]
}
```

### `PATCH /eyes/agents`

Patch (update) one or more Agents. Can license/unlicense multiple agents, update nicknames, and mark agents for deletion.

> **Note:** Deleting through `PATCH` may seem odd, but RESTful `DELETE` doesn't allow request bodies, which makes bulk deletes difficult.

```json
[
  {
    "agentId": "...",
    "isLicensed": true
  }
]
```

### `GET /eyes/agents/search`

Search for specific Agents using filters/attributes. This is an advanced fuzzy search that does not support pagination. You can specify a total number of results (capped). It executes a fuzzy search on partial or full agent names, nicknames, MAC addresses, IDs, local IPs, and/or external IPs.

For example, searching "mac pro" might return agents named "Macbook Pro" and "macbook-pro".

```json
{
  "count": 1,
  "results": [
    {
      "agent": {
        "name": "desktop-1234.company.example.com",
        "nickname": "desktop-1234",
        "ssid": "foo-ssid.5G",
        "bssid": "88:74:4E:61:8D:2D",
        "ip": "198.51.100.25",
        "mac": "48:49:11:46:53:30",
        "platform": "android",
        "type": "bssid",
        "uniqueId": "..."
      }
    }
  ]
}
```

### `GET /eyes/agents/{agentId}`

Fetches details for a specific Agent. Requires `agentId`.

### `PATCH /eyes/agents/{agentId}`

Updates a single Agent. Supports nickname changes, licensing updates, and miscellaneous data updates.

```json
{
  "isLicensed": true
}
```

### `DELETE /eyes/agents/{agentId}`

Flags the agent for deletion. Does not remove it immediately — once processed, the Agent is not recoverable.

Use `PATCH /eyes/agents` for bulk deletion.

## 3. Developer Tips

- Pagination for the Eyes endpoints starts at page 1.
- Use `/search` when you don't know the exact string to filter on.
- Use `/agents` when you want strict filtering and pagination.
- Use `/organizations` to look up `organizationId` values.

## 4. Troubleshooting & FAQs

**Q: What format is expected for PATCH?**

A: For `/eyes/agents`, send a JSON array. Each object can have an updatable field (`isLicensed`, `nickname`, delete flag, etc.).

**Q: I got a 404 error. What does it mean?**

A: Check if the agent exists before calling by ID.

**Q: Why are there both `organization` and `organizationId` fields?**

A: The API merges data from two systems. `organization` is the short name (e.g., `globalcorp`), and `organizationId` is the UUID retrievable from `/organizations`.

**Q: How does `/agents/search` differ from `/agents`?**

A: `/agents/search` is fuzzy, non-paginated, and supports multiple match fields. `/agents` is paginated with strict filtering.
