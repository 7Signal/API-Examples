# Organizations, Groups, Roles

## 1. Overview

The Organizations, Groups, and Roles endpoints provide read-only access to identity and access metadata. These endpoints allow developers to query metadata about organizations, user groups, and roles, and retrieve details using UUID identifiers.

- **Organizations:** represents an entity that owns or manages resources
- **Groups:** provides access to a set of Sensors. Groups are created by 7SIGNAL Support, but an organization administrator can assign a group to their users and API keys.
- **Roles:** represents permissions that define what actions users can perform/access

> **Note:** These are read-only endpoints. Modifications are not supported.

## 2. Endpoints

### Organizations

#### `GET /organizations`

Lists all accessible organizations.

> **Note:** Pagination for this endpoint starts at page 0.

```json
{
  "results": [
    {
      "id": "...",
      "name": "string",
      "connection": { "id": "..." },
      "mobileEyeOrgCode": "string",
      "isSuspended": false
    }
  ]
}
```

#### `GET /organizations/{organizationId}`

Lists details about a specific organization by UUID.

#### `GET /organizations/{organizationId}/features`

Lists all features mapped to the organization by UUID.

### Groups

#### `GET /groups`

Lists all accessible groups.

> **Note:** Pagination for this endpoint starts at page 0.

```json
{
  "results": [
    {
      "organization": { "id": "..." },
      "instance": { "id": "..." },
      "id": "...",
      "key": "string",
      "displayName": "string"
    }
  ]
}
```

#### `GET /groups/{groupId}`

Lists details about a specific group by UUID.

### Roles

#### `GET /roles`

Lists all accessible roles.

```json
{
  "results": [
    {
      "id": "...",
      "key": "customer:configurator",
      "description": "string",
      "auth0Id": "string",
      "isPublic": true
    }
  ]
}
```

#### `GET /roles/{roleId}`

Lists details about a specific role by UUID.

## 3. Troubleshooting & FAQs

**Q: Why do I see a 403 Forbidden error even with the token?**

A: Your token is valid but does not have access rights to the requested organization, group, or role. Check role permissions.

**Q: Can I modify Organizations, Groups, or Roles with these endpoints?**

A: No, these are read-only endpoints.
