# BulletDrop API Documentation

Complete API reference for the BulletDrop platform, including authentication, file uploads, user management, and admin operations.

## Table of Contents

- [Authentication](#authentication)
- [Users](#users)
- [File Uploads](#file-uploads)
- [Domains](#domains)
- [Admin](#admin)
- [Error Responses](#error-responses)
- [Rate Limiting](#rate-limiting)

## Base URL

```
http://localhost:8000
```

For production deployments, replace with your actual domain.

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

**Error Codes:**
- `400` - Email already registered or username taken
- `422` - Validation error

### POST /auth/login/json

Authenticate user with JSON credentials.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

**Error Codes:**
- `401` - Incorrect username or password

### POST /auth/login

Authenticate user with form data (OAuth2PasswordRequestForm).

**Form Data:**
- `username`: string
- `password`: string

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### GET /auth/me

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "discord_id": "string",
  "google_id": "string",
  "github_id": "string",
  "avatar_url": "string",
  "bio": "string",
  "github_username": "string",
  "discord_username": "string",
  "telegram_username": "string",
  "instagram_username": "string",
  "background_image": "string",
  "background_color": "#ffffff",
  "favorite_song": "string",
  "custom_domain": "string",
  "storage_used": 1048576,
  "storage_limit": 1073741824,
  "upload_count": 5,
  "is_active": true,
  "is_admin": false,
  "is_verified": true,
  "api_key": "string",
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00",
  "last_login": "2023-01-01T00:00:00"
}
```

### POST /auth/logout

Logout the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### POST /auth/refresh

Refresh the current authentication token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### OAuth Endpoints

#### GET /auth/oauth/{provider}

Initiate OAuth login with supported providers: `google`, `github`, `discord`.

**Response:** Redirects to the OAuth provider's authorization page.

#### POST /auth/oauth/{provider}/callback

Handle OAuth callback and create/login user.

**Request Body:**
```json
{
  "code": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

## File Uploads

### POST /api/uploads/

Upload a file with optional metadata.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: File (required)
- `custom_name`: string (optional)
- `domain_id`: integer (optional)
- `is_public`: boolean (default: true)

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "filename": "abc123.png",
  "original_filename": "screenshot.png",
  "file_size": 1048576,
  "mime_type": "image/png",
  "file_hash": "sha256_hash",
  "upload_url": "https://img.bulletdrop.com/abc123.png",
  "custom_name": "my_screenshot",
  "domain_id": 1,
  "view_count": 0,
  "is_public": true,
  "expires_at": null,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

**Error Codes:**
- `413` - File too large
- `415` - Unsupported file type
- `507` - Storage quota exceeded

### POST /api/uploads/sharex

ShareX-compatible upload endpoint.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: File (required)

**Response:**
```json
{
  "url": "https://img.bulletdrop.com/abc123.png",
  "thumbnail_url": "https://img.bulletdrop.com/abc123.png",
  "deletion_url": "http://localhost:8000/api/uploads/1/delete"
}
```

### GET /api/uploads/

Get paginated list of user uploads.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `page`: integer (default: 1)
- `per_page`: integer (default: 20, max: 100)

**Response:**
```json
{
  "uploads": [
    {
      "id": 1,
      "filename": "abc123.png",
      "original_filename": "screenshot.png",
      "file_size": 1048576,
      "mime_type": "image/png",
      "upload_url": "https://img.bulletdrop.com/abc123.png",
      "view_count": 5,
      "is_public": true,
      "created_at": "2023-01-01T00:00:00"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### GET /api/uploads/{upload_id}

Get specific upload by ID.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "filename": "abc123.png",
  "original_filename": "screenshot.png",
  "file_size": 1048576,
  "mime_type": "image/png",
  "upload_url": "https://img.bulletdrop.com/abc123.png",
  "view_count": 5,
  "is_public": true,
  "created_at": "2023-01-01T00:00:00"
}
```

### PATCH /api/uploads/{upload_id}

Update upload metadata.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "custom_name": "new_name",
  "is_public": false
}
```

**Response:** Updated upload object.

### DELETE /api/uploads/{upload_id}

Delete an upload.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Upload deleted successfully"
}
```

### POST /api/uploads/{upload_id}/view

Track a file view (public endpoint).

**Response:**
```json
{
  "message": "View tracked"
}
```

## Domains

### GET /api/domains/

Get available domains for file hosting.

**Response:**
```json
{
  "domains": [
    {
      "id": 1,
      "domain_name": "img.bulletdrop.com",
      "display_name": "Images",
      "description": "General image hosting",
      "is_available": true,
      "is_premium": false,
      "max_file_size": 10485760
    }
  ]
}
```

### GET /api/domains/my

Get user's claimed domains.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "domains": [
    {
      "id": 1,
      "domain_name": "img.bulletdrop.com",
      "display_name": "Images",
      "claimed_at": "2023-01-01T00:00:00"
    }
  ]
}
```

### POST /api/domains/claim/{domain_id}

Claim a domain for use.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Domain claimed successfully",
  "domain": {
    "id": 1,
    "domain_name": "img.bulletdrop.com",
    "display_name": "Images"
  }
}
```

## Admin Endpoints

All admin endpoints require admin privileges.

### GET /admin/stats

Get platform statistics.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "total_users": 1500,
  "total_uploads": 25000,
  "total_storage_used": 10737418240,
  "active_users_today": 150,
  "uploads_today": 250
}
```

### GET /admin/users

Get paginated list of all users.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `page`: integer (default: 1)
- `per_page`: integer (default: 20)

### POST /admin/users/{user_id}/ban

Ban a user account.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "User banned successfully"
}
```

### POST /admin/users/{user_id}/unban

Unban a user account.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "User unbanned successfully"
}
```

## Error Responses

All API endpoints return consistent error responses:

```json
{
  "detail": "Error description"
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error, missing fields)
- `401` - Unauthorized (invalid or missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `413` - Payload Too Large (file size exceeded)
- `415` - Unsupported Media Type
- `422` - Unprocessable Entity (validation error)
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error
- `507` - Insufficient Storage

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Authentication endpoints**: 5 requests per minute per IP
- **Upload endpoints**: 20 requests per minute per user
- **General endpoints**: 100 requests per minute per user

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1609459200
```

## Examples

### Complete Upload Workflow

1. **Authenticate:**
```bash
curl -X POST "http://localhost:8000/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "password": "secret"}'
```

2. **Upload File:**
```bash
curl -X POST "http://localhost:8000/api/uploads/" \
  -H "Authorization: Bearer <token>" \
  -F "file=@screenshot.png" \
  -F "custom_name=my_screenshot" \
  -F "is_public=true"
```

3. **Get Upload List:**
```bash
curl -X GET "http://localhost:8000/api/uploads/?page=1&per_page=10" \
  -H "Authorization: Bearer <token>"
```

### ShareX Configuration

For ShareX integration, use this configuration:

```json
{
  "Version": "13.4.0",
  "Name": "BulletDrop",
  "DestinationType": "ImageUploader, FileUploader",
  "RequestMethod": "POST",
  "RequestURL": "http://localhost:8000/api/uploads/sharex",
  "Headers": {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
  },
  "Body": "MultipartFormData",
  "FileFormName": "file",
  "URL": "{json:url}",
  "ThumbnailURL": "{json:thumbnail_url}",
  "DeletionURL": "{json:deletion_url}"
}
```

## WebSocket Support

Currently not implemented but planned for real-time notifications and upload progress.

## Versioning

The API is currently at version 1.0. Future versions will be available at `/v2/`, `/v3/`, etc., maintaining backward compatibility.

## Support

For API support and bug reports, please create an issue in the project repository.