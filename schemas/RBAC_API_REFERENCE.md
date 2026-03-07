# Veeam Backup & Replication v13.0.1 - RBAC API Reference

**All endpoints require Veeam Backup Administrator role**

## Table of Contents
- [Roles Management](#roles-management)
- [Users and Groups Management](#users-and-groups-management)
- [Security Settings](#security-settings)

---

## Roles Management

### 1. Get All Roles
**Endpoint:** `GET /api/v1/security/roles`

**Description:** Retrieves an array of all available roles in Veeam Backup & Replication.

**Query Parameters:**
- `skip` (integer, optional) - Number of roles to skip
- `limit` (integer, optional) - Maximum number of roles to return
- `orderColumn` (object, optional) - Sorts roles by parameter
- `orderAsc` (boolean, optional) - Sort in ascending order
- `nameFilter` (string, optional) - Filter roles by name pattern

**Example:**
```bash
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/roles?limit=50&orderAsc=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

**Responses:**
- `200` - OK
- `401` - Unauthorized
- `403` - Forbidden
- `500` - Internal Server Error

---

### 2. Get Role by ID
**Endpoint:** `GET /api/v1/security/roles/{id}`

**Description:** Gets a specific role by its ID.

**Path Parameters:**
- `id` (string, required) - Role ID

**Example:**
```bash
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/roles/{role-id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

**Responses:**
- `200` - OK
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

### 3. Get Role Permissions
**Endpoint:** `GET /api/v1/security/roles/{id}/permissions`

**Description:** Gets the permissions assigned to a specific role.

**Path Parameters:**
- `id` (string, required) - Role ID

**Example:**
```bash
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/roles/{role-id}/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

**Responses:**
- `200` - OK
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## Users and Groups Management

### 4. Get All Users and Groups
**Endpoint:** `GET /api/v1/security/users`

**Description:** Retrieves an array of users and groups with their assigned roles.

**Query Parameters:**
- `skip` (integer, optional) - Number of users/groups to skip
- `limit` (integer, optional) - Maximum number to return
- `orderColumn` (object, optional) - Sort by parameter
- `orderAsc` (boolean, optional) - Sort in ascending order
- `nameFilter` (string, optional) - Filter by name pattern
- `typeFilter` (array, optional) - Filter by type (User/Group)
- `roleIdFilter` (string, optional) - Filter by role ID
- `roleNameFilter` (string, optional) - Filter by role name
- `isServiceAccountFilter` (boolean, optional) - Filter service accounts only

**Example:**
```bash
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/users?limit=100&orderAsc=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

**Responses:**
- `200` - OK
- `401` - Unauthorized
- `403` - Forbidden
- `500` - Internal Server Error

---

### 5. Add User or Group
**Endpoint:** `POST /api/v1/security/users`

**Description:** Adds a new user or group with an assigned built-in role.

**Request Body:** JSON object with user/group details and role assignment

**Example:**
```bash
curl -X POST "https://lab-v13.sliema.lab:9419/api/v1/security/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1" \
  -H "Content-Type: application/json" \
  -d '{
    "userName": "domain\\username",
    "roleIds": ["role-id-here"]
  }'
```

**Responses:**
- `201` - User or group has been added
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `500` - Internal Server Error

---

### 6. Get User or Group by ID
**Endpoint:** `GET /api/v1/security/users/{id}`

**Description:** Gets a specific user or group by ID.

**Path Parameters:**
- `id` (string, required) - User or group ID

**Example:**
```bash
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/users/{user-id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

**Responses:**
- `200` - OK
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

### 7. Remove User or Group
**Endpoint:** `DELETE /api/v1/security/users/{id}`

**Description:** Removes a user or group from the system.

**Path Parameters:**
- `id` (string, required) - User or group ID

**Example:**
```bash
curl -X DELETE "https://lab-v13.sliema.lab:9419/api/v1/security/users/{user-id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

**Responses:**
- `204` - User or group has been removed
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

### 8. Get Roles Assigned to User or Group
**Endpoint:** `GET /api/v1/security/users/{id}/roles`

**Description:** Gets all roles assigned to a specific user or group.

**Path Parameters:**
- `id` (string, required) - User or group ID

**Example:**
```bash
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/users/{user-id}/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

**Responses:**
- `200` - OK
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

### 9. Edit Roles Assigned to User or Group
**Endpoint:** `PUT /api/v1/security/users/{id}/roles`

**Description:** Updates the roles assigned to a user or group.

**Path Parameters:**
- `id` (string, required) - User or group ID

**Request Body:** JSON array of role IDs

**Example:**
```bash
curl -X PUT "https://lab-v13.sliema.lab:9419/api/v1/security/users/{user-id}/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1" \
  -H "Content-Type: application/json" \
  -d '{
    "roleIds": ["role-id-1", "role-id-2"]
  }'
```

**Responses:**
- `200` - User or group has been updated
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

### 10. Change Service Account Mode
**Endpoint:** `POST /api/v1/security/users/{id}/changeServiceAccountMode`

**Description:** Changes whether a user is configured as a service account.

**Path Parameters:**
- `id` (string, required) - User ID

**Example:**
```bash
curl -X POST "https://lab-v13.sliema.lab:9419/api/v1/security/users/{user-id}/changeServiceAccountMode" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1" \
  -H "Content-Type: application/json" \
  -d '{
    "isServiceAccount": true
  }'
```

**Responses:**
- `200` - User has been updated
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

### 11. Reset MFA for Specific User
**Endpoint:** `POST /api/v1/security/users/{id}/resetMFA`

**Description:** Resets multi-factor authentication for a user. User will be prompted to configure MFA on next login.

**Path Parameters:**
- `id` (string, required) - User ID

**Example:**
```bash
curl -X POST "https://lab-v13.sliema.lab:9419/api/v1/security/users/{user-id}/resetMFA" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

**Responses:**
- `204` - MFA has been reset
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## Security Settings

### 12. Get MFA Settings
**Endpoint:** `GET /api/v1/security/settings`

**Description:** Checks whether multi-factor authentication (MFA) is enabled or disabled for all users.

**Example:**
```bash
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

**Responses:**
- `200` - OK
- `401` - Unauthorized
- `403` - Forbidden
- `500` - Internal Server Error

---

### 13. Edit MFA Settings
**Endpoint:** `PUT /api/v1/security/settings`

**Description:** Enables or disables multi-factor authentication (MFA) for all users.

**Request Body:** JSON object with MFA configuration

**Example:**
```bash
curl -X PUT "https://lab-v13.sliema.lab:9419/api/v1/security/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1" \
  -H "Content-Type: application/json" \
  -d '{
    "isMfaEnabled": true
  }'
```

**Responses:**
- `200` - OK
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `500` - Internal Server Error

---

## Common Workflows

### Workflow 1: List all users and their roles
```bash
# 1. Get all users
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"

# 2. For each user, get their roles
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/users/{user-id}/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

### Workflow 2: Add new user with specific role
```bash
# 1. Get available roles
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"

# 2. Create user with role ID from step 1
curl -X POST "https://lab-v13.sliema.lab:9419/api/v1/security/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1" \
  -H "Content-Type: application/json" \
  -d '{
    "userName": "domain\\newuser",
    "roleIds": ["role-id-from-step-1"]
  }'
```

### Workflow 3: Audit role permissions
```bash
# 1. Get all roles
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"

# 2. For each role, get permissions
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/roles/{role-id}/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1"
```

---

## Notes

1. **Authentication:** All endpoints require Bearer token authentication
2. **API Version:** Use `x-api-version: 1.3-rev1` header
3. **Permissions:** All RBAC endpoints require Veeam Backup Administrator role
4. **SSL:** Ensure your curl commands use `-k` or have proper SSL certificates configured
5. **Response Format:** All responses return JSON format

## Complete Example with Token
```bash
# 1. Get token
TOKEN=$(curl -X POST "https://lab-v13.sliema.lab:9419/api/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=DOMAIN\\username&password=password" \
  -k -s | jq -r '.access_token')

# 2. Use token for RBAC operations
curl -X GET "https://lab-v13.sliema.lab:9419/api/v1/security/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-version: 1.3-rev1" \
  -k
```
