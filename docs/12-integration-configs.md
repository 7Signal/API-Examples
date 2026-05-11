# Integration Configs

## 1. Overview

These endpoints allow users to configure integrations between 7SIGNAL and 3rd-party systems. In some cases, this includes the configuration of automated jobs.

### Available Integrations

| **Integration** | **Purpose** | **Features Supported** |
| --- | --- | --- |
| Meraki Cloud API | Sync AccessPoint information from the Meraki Cloud API into the 7SIGNAL platform | AccessPoint Name Synchronization |

## 2. Pagination

Pagination is included in the response payload for endpoints that return lists of resources (e.g., `GET /integrations/meraki/configs`).

| **Field** | **Description** |
| --- | --- |
| `perPage` | Number of records per page (default: 20) |
| `page` | The current page number (starting at 0) |
| `total` | Total number of records available |
| `pages` | Total number of pages |

```json
{
  "pagination": {
    "perPage": 20,
    "page": 0,
    "total": 4,
    "pages": 1
  }
}
```

## 3. Scheduling Overview

When configuring scheduled jobs (such as a Meraki access point synchronization), there are several options for defining when the schedule should run.

### Run Options

| Option | Description |
| --- | --- |
| `ONE_TIME` | Runs the job once, then never again (until the schedule is changed) |
| `SCHEDULED` | Runs on a recurring schedule based on the scheduling options below |

### Scheduled Options

A scheduled job can run `DAILY`, `WEEKLY`, or `MONTHLY`. Use `DISABLED` when the run option is `ONE_TIME`.

| **Run Option** | **Scheduled Option** | **Day of Week** | **Week of Month** | **Result** |
| --- | --- | --- | --- | --- |
| `ONE_TIME` | `DISABLED` | n/a | n/a | Job runs once |
| `SCHEDULED` | `DISABLED` | n/a | n/a | Job never runs |
| `SCHEDULED` | `DAILY` | n/a | n/a | Job runs every day |
| `SCHEDULED` | `WEEKLY` | 3 | n/a | Runs on Tuesday (1 = Sunday) |
| `SCHEDULED` | `MONTHLY` | 3 | 2 | Runs on the second Tuesday of the month |

### Important Notes for Monthly Jobs

- If the selected week number exceeds the number of weeks in the month (e.g., 5th week in February), the job will be skipped.
- If the requested weekday does not exist in the first week (e.g., Monday in a week starting Saturday), the job will be skipped.

For reliable monthly runs, choose `scheduledWeekOfMonth` = 2, 3, or 4 to minimize skipped executions.

## 4. Endpoints

### `GET /integrations/meraki/configs`

Returns a list of Meraki configurations. Returns an empty array if none exist.

Supports optional filtering: `ids`, `createdBys`, `organizationIds`, `sortField`, `order`.

```json
{
  "pagination": {
    "perPage": 20,
    "page": 0,
    "total": 1,
    "pages": 1
  },
  "results": [
    {
      "id": "00000000-0000-0000-0000-000000000001",
      "runOption": "SCHEDULED",
      "scheduledOption": "DAILY",
      "agentsEnabled": true,
      "agentsFullSynchronization": false,
      "sensorsEnabled": false,
      "organization": { "id": "11111111-1111-1111-1111-111111111111" },
      "createdBy": "joe.user@example.com",
      "createdAt": "2025-12-25T01:11:22.000000Z",
      "apiKeyId": { "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" },
      "group": { "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb" }
    }
  ]
}
```

### `POST /integrations/meraki/configs`

Creates a new Meraki configuration. One configuration is sufficient for most organizations.

| **Field** | **Description** |
| --- | --- |
| `apiKey` | Your Meraki API Key *(write-only — never returned after creation)* |
| `runOption` | `ONE_TIME` or `SCHEDULED` |
| `scheduledOption` | `DAILY`, `WEEKLY`, `MONTHLY`, or `DISABLED` |
| `scheduledDayOfWeek` | Day of the week (1 = Monday … 7 = Sunday) |
| `scheduledWeekOfMonth` | Week of the month (1–5) |
| `agentsEnabled` | Whether to sync AP names with the agents part of the platform |
| `agentsFullSynchronization` | If true, removes all APs from 7SIGNAL that are absent from Meraki. **Do NOT enable in mixed environments.** |
| `sensorsEnabled` | Whether to sync AP names with the sensors part of the platform |
| `organizationId` | Required if `sensorsEnabled` is true |
| `sapphireGroupId` | Required if `sensorsEnabled` is true |

```json
{
  "apiKey": "12345678910",
  "runOption": "SCHEDULED",
  "scheduledOption": "WEEKLY",
  "agentsEnabled": true,
  "agentsFullSynchronization": false,
  "sensorsEnabled": true,
  "scheduledDayOfWeek": 3,
  "scheduledWeekOfMonth": 2,
  "organizationId": "11111111-1111-1111-1111-111111111111",
  "sapphireGroupId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
}
```

### `GET /integrations/meraki/configs/{id}`

Returns a specific configuration by `id`. Returns 404 if not found.

### `PUT /integrations/meraki/configs/{id}`

Modifies an existing configuration's schedule or sync flags. Does not require the Meraki API key to be re-submitted.

> **Note:** To change the Meraki API key or organization/group, `DELETE` the existing configuration and `POST` a new one.

```json
{
  "runOption": "SCHEDULED",
  "scheduledOption": "DAILY",
  "agentsEnabled": true,
  "agentsFullSynchronization": true,
  "sensorsEnabled": true,
  "scheduledDayOfWeek": 2,
  "scheduledWeekOfMonth": 0
}
```

### `DELETE /integrations/meraki/configs/{id}`

Removes the configuration with the specified ID. This cannot be undone. Returns `204 No Content` on success.

## 5. Developer Tips

1. Use `PUT` to modify schedules and flags without creating a new configuration. Some changes (API key, org/group) require `DELETE` + `POST`.
2. The Meraki API key is write-only. If you need to update it, perform a `DELETE` and `POST` a new configuration.
3. When you create a Meraki configuration with a sensor group ID, a 7SIGNAL API key is automatically created to manage the Meraki ↔ 7SIGNAL interaction. This key will have the description `Meraki API Key`.
