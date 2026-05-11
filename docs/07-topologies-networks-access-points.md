# Topologies, Networks, Access Points

> **Deprecation Notice:** The `/topologies/*` endpoints are deprecated. See [migration/topology-endpoints.md](migration/topology-endpoints.md) for replacement endpoints.

## 1. Overview

These APIs allow users to interact with topological configurations, network infrastructure, and access point management for Agents and Sensors.

These APIs can:

- List locations, networks, and service areas
- Create, update, delete networks and access points
- Get more visibility on how systems are organized and deployed

**Scope:**

- **Topologies:** location and service area data
- **Networks:** grouping of Agents and Sensors
- **Access Points:** connection nodes for Agents and Sensors

## 2. Topologies Endpoints

> **Deprecated** — use the `/locations/*` and `/service-areas/*` endpoints instead. See [migration/topology-endpoints.md](migration/topology-endpoints.md).

### Agent Locations

#### `GET /topologies/agents/locations`

Lists all agent topology locations.

```json
{
  "results": [
    {
      "id": "...",
      "name": "string",
      "address": "string",
      "createdAt": "2025-08-07T17:51:01.969Z",
      "updatedAt": "2025-08-07T17:51:01.969Z"
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 2,
    "total": 45,
    "pages": 5
  }
}
```

#### `GET /topologies/agents/locations/{locationId}`

Fetches a specific agent topology location. Requires `locationId`.

### Sensor Locations

#### `GET /topologies/sensors/locations`

Lists all sensor topology locations.

```json
{
  "results": [
    {
      "id": 0,
      "name": "string",
      "description": "string",
      "parentId": 0
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 2,
    "total": 45,
    "pages": 5
  }
}
```

#### `GET /topologies/sensors/locations/{locationId}`

Fetches a specific sensor topology location. Requires `locationId`.

### Service Areas

> **Note:** Service areas only exist for sensors.

#### `GET /topologies/sensors/serviceAreas`

Lists all sensor service areas.

```json
{
  "results": [
    {
      "id": 0,
      "name": "string",
      "description": "string",
      "parentLocationId": 0,
      "parentLocationName": "string"
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 2,
    "total": 45,
    "pages": 5
  }
}
```

#### `GET /topologies/sensors/serviceAreas/{serviceAreaId}`

Fetches a specific service area. Requires `serviceAreaId`.

## 3. Networks Endpoints

### Agent Networks

#### `GET /networks/agents`

Lists all agent networks.

```json
{
  "results": [
    {
      "id": "...",
      "name": "string",
      "isEnabled": true,
      "createdAt": "2025-08-07T18:06:10.925Z",
      "updatedAt": "2025-08-07T18:06:10.925Z"
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 2,
    "total": 45,
    "pages": 5
  }
}
```

#### `POST /networks/agents`

Creates agent networks.

```json
[
  {
    "name": "string",
    "isEnabled": true
  }
]
```

#### `GET /networks/agents/{networkId}`

Fetches a specific agent network. Requires `networkId`.

#### `PUT /networks/agents/{networkId}`

Replaces an agent network. Requires `networkId`.

#### `DELETE /networks/agents/{networkId}`

Deletes an agent network. Requires `networkId`.

### Sensor Networks

#### `GET /networks/sensors`

Lists all sensor networks.

```json
{
  "results": [
    {
      "id": 0,
      "name": "string",
      "description": "string"
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 2,
    "total": 45,
    "pages": 5
  }
}
```

#### `GET /networks/sensors/{networkId}`

Fetches a specific sensor network. Requires `networkId`.

## 4. Access Points Endpoints

### Agent Access Points

#### `GET /access-points/agents`

Lists all agent access points.

```json
{
  "pagination": {
    "perPage": 167,
    "page": 1,
    "pages": 1,
    "total": 167
  },
  "results": [
    {
      "bssids": [],
      "id": "...",
      "name": "string",
      "controller": "string",
      "overTheAirName": "string",
      "modifiedBy": "string",
      "macAddress": "string",
      "locationId": "..."
    }
  ]
}
```

#### `POST /access-points/agents`

Creates agent access points.

```json
[
  {
    "name": "string",
    "controller": "string",
    "locationId": "...",
    "bssids": [
      {
        "bssid": "string",
        "band": "string"
      }
    ]
  }
]
```

#### `GET /access-points/agents/{accessPointId}`

Fetches a specific access point. Requires `accessPointId`.

#### `PUT /access-points/agents/{accessPointId}`

Replaces an access point. Requires `accessPointId`.

#### `PATCH /access-points/agents/{accessPointId}`

Updates an access point. Requires `accessPointId`.

#### `DELETE /access-points/agents/{accessPointId}`

Deletes an access point. Requires `accessPointId`.

### Sensor Access Points

#### `GET /access-points/sensors`

Lists all sensor access points.

```json
{
  "results": [
    {
      "id": 0,
      "name": "string",
      "bssid": "string",
      "description": "string",
      "serviceAreaId": 0,
      "serviceAreaName": "string",
      "network": "string",
      "band": 5
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 2,
    "total": 45,
    "pages": 0
  }
}
```

#### `GET /access-points/sensors/{accessPointId}`

Fetches a specific sensor access point. Requires `accessPointId`.

#### `PATCH /access-points/sensors/{accessPointId}`

Updates a sensor access point. Requires `accessPointId`.

```json
{
  "accessPointAlias": "string"
}
```

## 5. Developer Tips

- Pagination for Topologies, Networks, and AccessPoints endpoints all start at page 1.

## 6. Troubleshooting & FAQs

**Q: What is the difference between Agents and Sensors?**

A: Agents are entities used to monitor/process specific resources (software clients). 7SIGNAL's hardware sensors are dedicated devices for monitoring WiFi.

**Q: How do I fetch everything related to a location?**

A: First, get the location ID from `/topologies/agents/locations` or `/topologies/sensors/locations` (or their replacements), then use that ID to search networks and access points.
