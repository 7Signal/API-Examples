# Sensor Clients & Change Events

## 1. Overview

Two read-only endpoints that answer "what was here?" and "what changed?" for sensor-side monitoring:

- **Clients** (`/clients/sensors`) — the client devices sensors observed on the wireless network over a
  time window, with MAC address and vendor. Useful for inventory, rogue-device spotting, and mapping a
  MAC you found elsewhere back to a vendor.
- **Change events** (`/change-events/sensors`) — an audit trail of configuration and state changes on
  sensor-side elements: sensors (Eyes), access points, networks, and service areas. Useful when a metric
  shifted and you want to know whether something was reconfigured at that moment.

Both are windowed by `from`/`to` in epoch milliseconds, but they default differently and they return
different envelopes — see Developer Tips.

## 2. Endpoints

#### `GET /clients/sensors`

Returns the client devices observed within the time window.

**Required parameters:** none

**Optional parameters:** `from`, `to`, `mac`, `vendor`

```json
{
  "range": {
    "from": 1784451600000,
    "fromAsDateString": "2026-07-19T09:00:00.000Z[UTC]",
    "to": 1787043600000,
    "toAsDateString": "2026-08-18T09:00:00.000Z[UTC]",
    "total": 2,
    "duration": 2592000000,
    "durationAsString": "30 days"
  },
  "results": [
    {
      "id": 90714,
      "name": "ENG-LAPTOP-114",
      "macAddress": "a4:83:e7:1b:5c:90",
      "description": "Engineering loaner laptop",
      "user": "jdoe",
      "vendor": "Apple, Inc."
    },
    {
      "id": 90715,
      "name": "WH-SCANNER-07",
      "macAddress": "00:1b:63:84:45:e6",
      "description": null,
      "user": null,
      "vendor": "Zebra Technologies"
    }
  ]
}
```

The envelope is `{range, results}` — there is **no `pagination` object** and no `page`/`perPage`
parameters, despite the endpoint being described as pageable. Narrow the window or the `mac`/`vendor`
filters to reduce the result size.

#### `GET /change-events/sensors`

Returns change events for a specified sensor or network element.

**Required parameters:** none, but see the valid-combination rule below

**Optional parameters:** `sensorId`, `accessPointId`, `networkId`, `serviceAreaId`, `from`, `to`

```json
{
  "results": [
    {
      "timestamp": 1750821376000,
      "name": "TEST_PROFILE_CHANGED",
      "element": "Eye-Cleveland-03",
      "parentElement": "Cleveland HQ - Floor 3",
      "description": "Test profile changed from 'Standard Branch' to 'High Frequency'"
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 1,
    "total": 18,
    "pages": 2
  }
}
```

**The element filters are not freely combinable.** Only these combinations are valid:

| Combination | Parameters |
|-------------|------------|
| Access Point only | `accessPointId` |
| Eye only | `sensorId` |
| Access Point with Eye | `accessPointId` + `sensorId` |
| Network only | `networkId` |
| Network with Service Area | `networkId` + `serviceAreaId` |

`serviceAreaId` is only meaningful alongside `networkId` — it narrows within a network rather than
standing on its own.

## 3. Developer Tips

**Query parameters:**

| Parameter | Endpoint | Type | Description |
|-----------|----------|------|-------------|
| `from` | both | number | Epoch ms, UTC. **Clients: defaults to 30 days ago. Change events: defaults to 24 hours ago** |
| `to` | both | number | Epoch ms, UTC. Defaults to now on both |
| `mac` | clients | string | Partial MAC address, case-insensitive |
| `vendor` | clients | string | Partial vendor/OUI name, case-insensitive |
| `sensorId` | change events | — | Filter to one Eye |
| `accessPointId` | change events | — | Filter to one access point |
| `networkId` | change events | — | Filter to one network |
| `serviceAreaId` | change events | — | Only valid together with `networkId` |

**The two endpoints default to different windows and cap differently.** This catches people out when
querying both for the same investigation:

| | `from` default | Maximum window |
|---|---|---|
| `/clients/sensors` | 30 days ago | 90 days |
| `/change-events/sensors` | 24 hours ago | not capped in the specification |

Always pass `from` and `to` explicitly when correlating the two, rather than relying on defaults.

**Getting epoch milliseconds in Python:**

```python
import time

now_ms = int(time.time() * 1000)
seven_days_ago_ms = now_ms - (7 * 24 * 60 * 60 * 1000)
```

**Partial matching on `mac` and `vendor`** means you can search by OUI prefix without knowing the full
address:

```python
# Every Apple device seen, by vendor name
params = {"vendor": "apple"}

# Every device whose MAC starts with a known OUI
params = {"mac": "a4:83:e7"}
```

Both are case-insensitive, so `"APPLE"`, `"Apple"`, and `"apple"` behave identically.

**Nullable fields on clients.** `name`, `description`, and `user` are only populated where someone has
labelled the device in the platform. Unmanaged and transient devices commonly have all three as `null`
while still carrying a usable `macAddress` and `vendor`. Guard your display code:

```python
name = client.get("name") or client.get("macAddress") or "(unknown)"
vendor = client.get("vendor") or "(unknown vendor)"
```

**Change event `element` and `parentElement` are names, not ids.** They're intended for display —
`element` is the thing that changed, `parentElement` is its container (an Eye's service area, an access
point's network). To act on the element programmatically, look it up by name through its own endpoint.

**Correlating a metric change with a configuration change** is the main reason to reach for change
events. Fetch the time series around the anomaly, then query change events for the same window and
element:

```python
# Did anything change on this Eye while the metric dipped?
params = {"sensorId": sensor_id, "from": dip_start_ms, "to": dip_end_ms}
```

**Finding the ids:** sensor ids come from `/eyes/sensors`, access point ids from
`/access-points/sensors`, and network ids from `/networks/sensors` — see
[Eyes (Sensors)](06-eyes-sensors.md) and
[Topologies, Networks, Access Points](07-topologies-networks-access-points.md).

## 4. Troubleshooting & FAQs

**Q: Where are `page` and `perPage` on `/clients/sensors`?**

A: That endpoint isn't paginated — it returns a `range` object rather than a `pagination` object, and the
time window bounds the results. `/change-events/sensors` differs: it *does* return a `pagination` object,
but the specification doesn't declare `page` or `perPage` among its accepted parameters. Until that's
confirmed against your own deployment, narrow the window or the element filter to control the result
size rather than relying on paging.

**Q: I asked for 6 months of clients and got a `400`.**

A: The window on `/clients/sensors` cannot exceed 90 days. Split a longer retrospective into 90-day
chunks.

**Q: I passed no parameters to each endpoint and got wildly different time spans.**

A: The defaults differ — clients defaults to the last 30 days, change events to the last 24 hours. Pass
`from` and `to` explicitly whenever the window matters.

**Q: My `serviceAreaId` filter on change events returns nothing.**

A: `serviceAreaId` is only valid in combination with `networkId`. On its own it isn't one of the supported
filter combinations. Add the `networkId` it belongs to.

**Q: Can I filter change events by both a network and an access point?**

A: No. The supported combinations are Access Point, Eye, Access Point + Eye, Network, or Network + Service
Area. Network + Access Point isn't among them — make two calls if you need both views.

**Q: A client I know was connected isn't in the results.**

A: Check the window first, since the default only reaches back 30 days. Beyond that, this endpoint reports
clients as observed by *sensors*; a device that only ever associated where no sensor could see it won't
appear. Data retention also varies by subscription tier.

**Q: Two entries have the same `macAddress` but different `id`s.**

A: `id` identifies the client record in the platform, not the radio. A device re-enrolled, or recorded
under a different name or organization, can produce more than one record for the same hardware address.
Group by `macAddress` when you want one row per physical device.

**Q: What values can a change event `name` take?**

A: It's an open string in the specification rather than a fixed enum, so treat it as a label to display
and group by. Don't assume the set you observe today is complete.
