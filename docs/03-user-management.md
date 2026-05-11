# User Management

## 1. Overview

This API allows for user management, and their roles, groups, and organizational access within the system.

### Roles

There are 3 main user roles with differing levels of permissions:

| **Role** | **Description** | **Permissions Summary** |
| --- | --- | --- |
| Reporter | Read-only user | Can view data and generate reports only |
| Configurator | Can configure sensors and agents | Can configure the system but cannot manage users |
| Organization Admin | Full admin privileges | Can manage users, configure systems, and assign roles |

## 2. Common Use Cases

Most users will use these endpoints frequently:

- Create users
- Search/list users
- Delete users
- Modify user's access to groups

Though these are the most common, the API supports full CRUD operations for users, groups, organizations, and roles.

## 3. Pagination

Pagination is included in the response payload, specifically for endpoints that return lists of resources (e.g., `GET /users`).

The response includes the following:

| **Field** | **Description** |
| --- | --- |
| `perPage` | Number of records per page (default: 20) |
| `page` | The current page number (starting at 0) |
| `total` | Total number of records available |
| `pages` | Total number of pages |

Example:

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

## 4. Understanding Relationships

This API is designed with interlinked systems. Understanding how these resources relate can help manage users more effectively:

- **Users and Roles:** Each user is assigned one role via `PUT /users/{userId}/role`. When fetching the user (`GET /users/{userId}`), you'll see their `roleId`. You could use this to map back to the role object to see more details.
- **Users and Groups:** Groups are used to define access within an organization. A user can be assigned to multiple groups, and each of these groups must belong to one of the user's organizations.
- **Users and Organizations:** Users can belong to one or more organizations. These are managed by the `/users/{userId}/organizations` endpoints.

Mapping users to their roles, groups, and organizations allows developers to validate if a user has access, determine different group assignments, and troubleshoot permissions more efficiently.

## 5. Endpoints

### a. Users

#### `GET /users`

Returns a list of users that the requester has access to.

> **Note:** Pagination for this endpoint starts at page 0, which is not the default. This will be fixed to be consistent in the next major API version.

```json
{
  "results": [
    {
      "id": "...",
      "firstName": "random",
      "lastName": "user",
      "email": "random.user@example.com",
      "roleId": "...",
      "roleKey": "customer:reporter"
    }
  ]
}
```

#### `POST /users`

Creates a new user.

> **Note:** Leave `permissionIds` and `permissionNames` as empty arrays.

```json
{
  "firstName": "string",
  "lastName": "string",
  "email": "string",
  "roleId": "...",
  "organizationId": "...",
  "permissionIds": [],
  "permissionNames": []
}
```

Returns a detailed response including user details, role, permissions, organizations, and groups.

#### `GET /users/{userId}`

Returns detailed information about the user, including role, organizational, and group information.

#### `DELETE /users/{userId}`

Deletes the specified user. This is an immediate action and cannot be reversed.

### b. Groups

#### `GET /users/{userId}/groups`

Lists all groups assigned to the user.

> **Note:** Pagination for this endpoint starts at page 0.

```json
{
  "results": [
    {
      "id": "...",
      "key": "string",
      "displayName": "string",
      "organization": { "id": "..." },
      "instance": { "id": "..." }
    }
  ]
}
```

#### `PUT /users/{userId}/groups`

Replaces all groups the user is currently assigned to.

> **Note:** Requires `userId` and `groupId`. `PUT` replaces — use `POST` to add.

#### `POST /users/{userId}/groups`

Adds one or more groups to the user's current group memberships.

#### `DELETE /users/{userId}/groups/{groupId}`

Removes a specific group from a user.

### c. Organizations

Groups assigned to a user must belong to one of their organizations.

#### `GET /users/{userId}/organizations`

Lists all organizations the user has access to.

> **Note:** Pagination for this endpoint starts at page 0.

```json
{
  "results": [
    {
      "id": "...",
      "name": "string",
      "connectionId": "string",
      "isPrimary": true,
      "mobileEyeOrgCode": "string"
    }
  ]
}
```

#### `PUT /users/{userId}/organizations`

Replaces the list of organizations the user has access to.

#### `POST /users/{userId}/organizations`

Adds one or more organizations to the user.

#### `DELETE /users/{userId}/organizations/{organizationId}`

Removes the specified organization from the user.

> **Advanced Usage:** The first organization added becomes the primary. If the primary is removed, the next organization becomes the primary.

### d. Roles

#### `PUT /users/{userId}/role`

Assigns or replaces the user's role. Requires `userId` and `roleId`.

#### `DELETE /users/{userId}/role`

Removes the user's role, resulting in no access.

## 6. Developer Tips

- Pagination for list endpoints starts at page 0 (not the default) — this will be fixed in the next major API version.
- To use the Permissions endpoints, you need the Organization Admin role.
- `POST` adds data; `PUT` replaces data.
- Reference `/users`, `/groups`, and `/roles` for valid IDs.
- Groups and organizations must be compatible.
- Any role is sufficient for `GET` endpoints.
- For `POST`, `PUT`, and `DELETE` endpoints, you need admin access.
- `GET /resource` usually returns a paginated or summarized list. `GET /resource/{id}` returns the full object.

## 7. Troubleshooting & FAQs

**Q: What happens if I delete a user?**

A: The user is permanently removed from the system. There is no undo.

**Q: I assigned a role to a user, but the user still can't access anything. What should I do?**

A: Check if:
- The user has at least one organization.
- They have groups assigned that match their organization.

**Q: I used `PUT` and removed group access unintentionally. What should I do?**

A: `PUT` replaces all groups. If you want to add groups, use `POST`.

**Q: Can a user belong to multiple groups and organizations?**

A: Yes, but each group must belong to one of the user's assigned organizations.

**Q: I accidentally assigned the wrong role. How do I fix it?**

A: Use `PUT` again to replace the current role with the correct role.
