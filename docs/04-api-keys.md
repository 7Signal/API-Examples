# API Keys

## 1. Overview

This set of endpoints allows users to manage API keys for secure access to protected resources. API keys are used to authorize users that interact with their system.

API keys are unique credentials that are tied to an organization or group, enabling access to features like Mobile Eye and Sapphire resources. They're associated with a single role, an optional set of additional permissions, and are intended to be non-editable after creation.

## 2. Endpoints

### `GET /apikeys`

Returns a list of all accessible API keys. Supports optional query parameters to filter the results: `permissions`, `ids`, `createdBys`, `organizationIds`.

> **Note:** Pagination for this endpoint starts at page 0.

```json
{
  "pagination": {
    "perPage": 20,
    "page": 0,
    "total": 5,
    "pages": 1
  },
  "results": [
    {
      "id": "...",
      "apiKey": "...",
      "createdBy": "random.user@gmail.com",
      "description": "",
      "createdAt": "2025-07-09T18:43:13.156294Z",
      "organization": { "id": "..." },
      "isSystem": false
    }
  ]
}
```

### `POST /apikeys`

Creates a new API key with specific permissions.

> **Note:** Requires `organizationId`, `sapphireGroupId`, `roleId`, and `permissionIds`. Use an empty list if no additional permissions are needed.

**Request:**

```json
{
  "organizationId": "...",
  "sapphireGroupId": "...",
  "roleId": "...",
  "permissionIds": [],
  "description": "string"
}
```

**Response:**

```json
{
  "organization": { "id": "..." },
  "group": { "id": "..." },
  "id": "...",
  "apiKey": "string",
  "createdBy": "string",
  "description": "string",
  "createdAt": "2025-07-22T19:59:36.085Z",
  "isSystem": true,
  "clientSecret": "string",
  "permissions": [
    {
      "id": "...",
      "key": "string",
      "description": "string",
      "isPublic": true
    }
  ]
}
```

> **Important:** Save the `apiKey` and `clientSecret` values immediately — the secret is not retrievable after the creation response is dismissed.

### `GET /apikeys/{apikeyId}`

Returns data and permissions for a specific API key.

```json
{
  "organization": { "id": "..." },
  "group": { "id": "..." },
  "id": "...",
  "apiKey": "string",
  "createdBy": "string",
  "description": "string",
  "createdAt": "2025-07-22T20:39:01.721Z",
  "isSystem": true,
  "clientSecret": "string",
  "permissions": [
    {
      "id": "...",
      "key": "string",
      "description": "string",
      "isPublic": true
    }
  ]
}
```

### `DELETE /apikeys/{apikeyId}`

Permanently deletes the specified API key. Deleted keys cannot be recovered — you must create a new one if a key is lost.

## 3. Developer Tips

- API keys are not modifiable after creation. This is intentional and prevents permission escalation by updating an existing key.
- Save the API key and secret immediately — secret values are not retrievable once the creation response is dismissed.
- API keys must be associated with an organization. This gives the key access to Mobile Eye through that organization.
- API keys may optionally be associated with a single group (not multiple). The group provides access to the Sapphire resources for that group.
- Once deleted, an API key is permanently gone.

## 4. Troubleshooting & FAQs

**Q: I tried to fetch an API key and it returned a 404 error. Why?**

A: A 404 means the API key was either deleted or never existed. Deleted keys cannot be recovered.

**Q: I got a 401 error, what does that mean?**

A: The token was missing or invalid. Make sure your request includes a valid Bearer token in the `Authorization` header.

**Q: Can I update an API key's permissions?**

A: No. API keys are not modifiable. To make changes, delete and recreate the key.
