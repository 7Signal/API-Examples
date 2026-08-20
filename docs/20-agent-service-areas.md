# Agent Service Areas

## 1. Overview

Agent Service Areas are named sub-divisions of a location — a floor, a wing, a warehouse aisle — used to
group agent (client device) measurements more finely than location alone. An agent's data rolls up to a
service area, and service areas roll up to a location.

Unlike most resources in this API, the collection endpoint supports **bulk** create, update, and delete.
`POST`, `PUT`, and `DELETE` on `/service-areas/agents` operate on many service areas in one call, which
is what you want when standing up a new site with a dozen floors. The `{serviceAreaId}` endpoints handle
one at a time.

That gives two ways to do the same thing, with different payload shapes:

| Operation | Collection (bulk) | Single |
|-----------|-------------------|--------|
| Create | `POST /service-areas/agents` — `{serviceAreas: [...]}` | *(not available)* |
| Update | `PUT /service-areas/agents` — `{serviceAreas: [{id, ...}]}` | `PUT /service-areas/agents/{serviceAreaId}` — `{name, address}` |
| Delete | `DELETE /service-areas/agents?ids=a&ids=b` | `DELETE /service-areas/agents/{serviceAreaId}` |

> Sensor service areas are a separate resource with a different shape, documented under
> [Topologies, Networks, Access Points](07-topologies-networks-access-points.md). This page covers the
> agent side only.

## 2. Endpoints

#### `GET /service-areas/agents`

Pages through the organization's agent service areas.

**Required parameters:** none

**Optional parameters:** `serviceAreaIds`, `searchValue`, `sort`, `scoreSortStart`, `scoreSortEnd`,
`organization`, `page`, `perPage`

```json
{
  "results": [
    {
      "id": "6e2a9c41-7b35-4d88-a1f0-92c4e7b5d306",
      "name": "Cleveland HQ - Floor 3",
      "address": "1000 Example Ave, Cleveland, OH 44113",
      "locationId": "4d1e8b7c-9a35-4c72-b6f0-2e5a9d3c8f41",
      "createdAt": "2026-03-11T15:04:22Z",
      "updatedAt": "2026-07-28T09:41:07Z"
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 1,
    "total": 34,
    "pages": 4
  }
}
```

#### `POST /service-areas/agents`

Creates one or more service areas. Returns `201`.

**Body:** a `serviceAreas` array, each entry with `name` and `address`.

```json
{
  "serviceAreas": [
    { "name": "Cleveland HQ - Floor 3", "address": "1000 Example Ave, Cleveland, OH 44113" },
    { "name": "Cleveland HQ - Floor 4", "address": "1000 Example Ave, Cleveland, OH 44113" }
  ]
}
```

Note the create entries carry no `id` — the server assigns them.

#### `PUT /service-areas/agents`

Bulk update. Returns `201`.

**Body:** a `serviceAreas` array where **each entry must include its `id`** — that's how the server knows
which record each set of values belongs to.

```json
{
  "serviceAreas": [
    { "id": "6e2a9c41-7b35-4d88-a1f0-92c4e7b5d306", "name": "Cleveland HQ - Floor 3 (East)", "address": "1000 Example Ave, Cleveland, OH 44113" },
    { "id": "b81f3d07-2c69-4a15-8e73-5f0a9c62d418", "name": "Cleveland HQ - Floor 4 (East)", "address": "1000 Example Ave, Cleveland, OH 44113" }
  ]
}
```

#### `DELETE /service-areas/agents`

Bulk delete. Returns `204`.

**Required parameters:** `ids` — one or more service area UUIDs, as a **query parameter**, not a body.

```
DELETE /service-areas/agents?ids=6e2a9c41-7b35-4d88-a1f0-92c4e7b5d306&ids=b81f3d07-2c69-4a15-8e73-5f0a9c62d418
```

#### `GET /service-areas/agents/{serviceAreaId}`

**Required parameters:** `serviceAreaId` (UUID, in path)

Returns a single `AgentServiceArea` object — the same shape as one entry in the list's `results`.

#### `PUT /service-areas/agents/{serviceAreaId}`

Updates one service area. Returns `200`.

**Required parameters:** `serviceAreaId` (UUID, in path)

**Body:** `{name, address}` — **no `id` field.** The id comes from the path here, unlike the bulk `PUT`
where it must be in each array entry.

```json
{
  "name": "Cleveland HQ - Floor 3 (East)",
  "address": "1000 Example Ave, Cleveland, OH 44113"
}
```

#### `DELETE /service-areas/agents/{serviceAreaId}`

Deletes one service area. Returns `204`.

**Required parameters:** `serviceAreaId` (UUID, in path)

## 3. Developer Tips

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `serviceAreaIds` | string | **Comma-separated** list of UUIDs, to return only those service areas |
| `searchValue` | string | Case-insensitive "name contains" filter |
| `sort` | string | `field,direction` — e.g. `name,asc`. **Repeat the parameter** for multi-column sorts |
| `scoreSortStart` | number | Epoch ms — **required when `sort=score`** |
| `scoreSortEnd` | number | Epoch ms — **required when `sort=score`** |
| `ids` | array | Required on the bulk `DELETE` only |
| `organization` | string | Defaults to the organization on your token |
| `page` | integer | **First page is 1**, not 0 |
| `perPage` | integer | Records per page |

**`sort` is not the `sortField`/`order` pair used elsewhere.** This endpoint takes a single combined
`sort` parameter and supports multiple sort keys by repeating it:

```python
# Two-column sort — pass a list of tuples so the param repeats
params = [("sort", "name,asc"), ("sort", "createdAt,desc")]
response = requests.get(url, headers=headers, params=params)
```

**Sorting by score needs a time window.** `sort=score` orders service areas by average experience score,
which is only meaningful over a period — so `scoreSortStart` and `scoreSortEnd` become required:

```python
now_ms = int(time.time() * 1000)
params = {
    "sort": "score",
    "scoreSortStart": now_ms - (24 * 60 * 60 * 1000),
    "scoreSortEnd": now_ms,
}
```

**Note the two id-list formats.** `serviceAreaIds` (filtering on `GET`) is one comma-separated string.
`ids` (bulk `DELETE`) is a repeated array parameter. They are not interchangeable:

```python
# GET filter — single comma-joined string
requests.get(url, headers=headers, params={"serviceAreaIds": ",".join(area_ids)})

# Bulk DELETE — repeated parameter
requests.delete(url, headers=headers, params=[("ids", i) for i in area_ids])
```

**Bulk `PUT` needs ids inside the array; single `PUT` must not have one.** This is the easiest mistake to
make when refactoring between the two. The bulk form identifies records by the `id` in each entry; the
single form identifies it by the path and takes only `name` and `address`.

**Service area ids are UUIDs**, as is `locationId`. That differs from sensor targets and network keys
(see [Sensor Targets & Network Keys](19-sensor-targets-and-network-keys.md)), where ids are integers.

**Confirming destructive calls in a script.** A bulk delete can remove many service areas in one request,
so echo the count and names before sending:

```python
logging.info(f"About to delete {len(area_ids)} service area(s):")
for area in selected_areas:
    logging.info(f"  - {area.get('name')} ({area.get('id')})")

choice = input("Type 'yes' to confirm: ").strip().lower()
if choice != "yes":
    logging.info("Aborted; nothing was deleted.")
    return
```

**Finding a location ID:** `locationId` values come from `/locations/agents` — see
[Topologies, Networks, Access Points](07-topologies-networks-access-points.md).

## 4. Troubleshooting & FAQs

**Q: My bulk `PUT` created duplicates instead of updating.**

A: The `id` was missing from the array entries. Without it the server can't match an entry to an existing
record. Every object in the bulk `PUT`'s `serviceAreas` array needs its `id`.

**Q: My single `PUT` returns `400` and I copied the body from the bulk call.**

A: Drop the `id` from the body. `PUT /service-areas/agents/{serviceAreaId}` takes only `name` and
`address`; the id belongs in the path.

**Q: `DELETE /service-areas/agents` returns `400` even though I sent a JSON body with ids.**

A: The bulk delete reads ids from the `ids` **query parameter**, not from a request body. Use
`?ids=<uuid>&ids=<uuid>`.

**Q: `sort=score` returns a `400`.**

A: Score sorting needs a window. Supply both `scoreSortStart` and `scoreSortEnd` as epoch milliseconds.

**Q: `sortField=name&order=asc` isn't sorting.**

A: Those are the parameter names used by most other endpoints in this API, but not this one. Use
`sort=name,asc` here.

**Q: Only my last `sort` is being applied.**

A: The parameter needs to repeat, and most HTTP client helpers collapse a dict's duplicate keys. In
`requests`, pass a list of tuples rather than a dict so both values survive.

**Q: Filtering with `serviceAreaIds` returns nothing.**

A: Check the format — it's a single comma-separated string of UUIDs, not a repeated parameter. Passing it
the way you'd pass `ids` to the bulk delete produces an unmatched filter.

**Q: Does deleting a service area delete the agents in it, or its measurement history?**

A: No. It removes the grouping. Agents and their measurements remain; they simply stop rolling up to that
service area.
