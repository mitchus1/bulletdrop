# Admin API Endpoints

This document describes the admin-only API endpoints for managing users, domains, and viewing system statistics.

## Authentication

All admin endpoints require:
1. Valid JWT token in Authorization header
2. User with `is_admin: true` in the database

```
Authorization: Bearer <jwt_token>
```

## User Management

### Get All Users
`GET /admin/users`

Query Parameters:
- `skip` (int): Number of users to skip (default: 0)
- `limit` (int): Maximum number of users to return (default: 100, max: 1000)
- `search` (string): Search by username or email
- `is_active` (bool): Filter by active status
- `is_admin` (bool): Filter by admin status

### Get User by ID
`GET /admin/users/{user_id}`

### Update User
`PATCH /admin/users/{user_id}`

Request Body:
```json
{
  "is_active": true,
  "is_admin": false,
  "is_verified": true,
  "storage_limit": 2147483648
}
```

### Delete User
`DELETE /admin/users/{user_id}`

Note: Cannot delete your own admin account.

## Domain Management

### Get All Domains
`GET /admin/domains`

Returns domains with usage statistics (user_count, upload_count).

### Create Domain
`POST /admin/domains`

Request Body:
```json
{
  "domain_name": "img.example.com",
  "display_name": "Image Hosting",
  "description": "Primary image hosting domain",
  "is_available": true,
  "is_premium": false,
  "max_file_size": 10485760
}
```

### Update Domain
`PATCH /admin/domains/{domain_id}`

Request Body:
```json
{
  "display_name": "Updated Name",
  "description": "Updated description",
  "is_available": false,
  "is_premium": true,
  "max_file_size": 52428800
}
```

### Delete Domain
`DELETE /admin/domains/{domain_id}`

Note: Cannot delete domains with existing uploads.

## Statistics

### Get System Statistics
`GET /admin/stats`

Response:
```json
{
  "total_users": 150,
  "active_users": 142,
  "admin_users": 3,
  "verified_users": 89,
  "total_uploads": 2547,
  "total_storage_used": 5368709120,
  "total_domains": 8,
  "available_domains": 6,
  "premium_domains": 2
}
```

### Get User Activity Statistics
`GET /admin/stats/users?limit=50`

Returns top users by upload count with activity stats.

### Get Domain Statistics
`GET /admin/stats/domains`

Returns domain usage statistics (uploads, users, storage).

### Get Recent Activity
`GET /admin/activity?days=7&limit=100`

Query Parameters:
- `days` (int): Number of days to look back (default: 7, max: 30)
- `limit` (int): Maximum number of activities (default: 100, max: 1000)

Returns recent system activities:
- User registrations
- File uploads
- Domain creations

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Cannot remove admin privileges from yourself"
}
```

## Example Usage

### Create Admin User (CLI)
```bash
cd backend
python create_admin.py
```

### Test Admin Access
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/admin/stats
```

### Get All Users with Search
```bash
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/admin/users?search=john&limit=10"
```

### Update User Status
```bash
curl -X PATCH \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"is_active": false}' \
     http://localhost:8000/admin/users/123
```

### Create New Domain
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "domain_name": "cdn.bulletdrop.com",
       "display_name": "CDN",
       "description": "Content delivery network",
       "is_premium": true,
       "max_file_size": 52428800
     }' \
     http://localhost:8000/admin/domains
```