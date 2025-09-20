# BulletDrop API Endpoints Documentation

## Overview
This document outlines all the API endpoints for the BulletDrop Discord profile and image hosting platform.

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://api.bulletdrop.com`

## Authentication
All protected endpoints require JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

---

## 🔐 Authentication Endpoints

### POST /api/auth/register
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
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string"
  }
}
```

### POST /api/auth/login
Login with username/email and password.

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
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string"
  }
}
```

### POST /api/auth/refresh
Refresh JWT token.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### POST /api/auth/logout
Logout user (invalidate token).

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

---

## 👤 User Management Endpoints

### GET /api/users/me
Get current user profile.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "discord_id": "string",
  "avatar_url": "string",
  "bio": "string",
  "custom_domain": "string",
  "upload_count": 0,
  "total_size": 0,
  "created_at": "2025-09-19T00:00:00Z"
}
```

### PUT /api/users/me
Update current user profile.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "bio": "string",
  "avatar_url": "string",
  "discord_id": "string"
}
```

### GET /api/users/{username}
Get public user profile.

**Response:**
```json
{
  "username": "string",
  "avatar_url": "string",
  "bio": "string",
  "custom_domain": "string",
  "upload_count": 0,
  "created_at": "2025-09-19T00:00:00Z"
}
```

### DELETE /api/users/me
Delete current user account.

**Headers:** `Authorization: Bearer <token>`

---

## 📁 File Upload Endpoints

### POST /api/uploads
Upload a new file.

**Headers:** `Authorization: Bearer <token>`

**Request Body:** `multipart/form-data`
```
file: File
custom_name?: string
```

**Response:**
```json
{
  "id": 1,
  "filename": "abc123.png",
  "original_filename": "screenshot.png",
  "upload_url": "https://img.bulletdrop.com/abc123.png",
  "custom_url": "https://img.bulletdrop.com/custom_name.png",
  "file_size": 1024000,
  "mime_type": "image/png",
  "created_at": "2025-09-19T00:00:00Z"
}
```

### GET /api/uploads
Get user's uploaded files.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page`: number (default: 1)
- `limit`: number (default: 20, max: 100)
- `sort`: string (date_desc, date_asc, size_desc, size_asc)

**Response:**
```json
{
  "uploads": [
    {
      "id": 1,
      "filename": "abc123.png",
      "original_filename": "screenshot.png",
      "upload_url": "string",
      "custom_url": "string",
      "file_size": 1024000,
      "mime_type": "image/png",
      "created_at": "2025-09-19T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20,
  "total_pages": 5
}
```

### GET /api/uploads/{upload_id}
Get specific upload details.

**Headers:** `Authorization: Bearer <token>`

### PUT /api/uploads/{upload_id}
Update upload (custom name, etc.).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "custom_name": "string"
}
```

### DELETE /api/uploads/{upload_id}
Delete an uploaded file.

**Headers:** `Authorization: Bearer <token>`

---

## 🌐 Domain Management Endpoints

### GET /api/domains
Get available domains.

**Response:**
```json
{
  "available_domains": [
    {
      "domain": "img.bulletdrop.com",
      "description": "Main image hosting domain",
      "is_premium": false
    },
    {
      "domain": "shots.bulletdrop.com",
      "description": "Screenshot hosting",
      "is_premium": false
    }
  ]
}
```

### POST /api/domains/claim
Claim a domain for user.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "domain": "img.bulletdrop.com"
}
```

### GET /api/domains/user
Get user's claimed domain.

**Headers:** `Authorization: Bearer <token>`

### POST /api/domains/custom
Request custom domain.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "domain": "mydomain.com",
  "verification_method": "dns"
}
```

---

## 📊 Statistics Endpoints

### GET /api/stats/user
Get user statistics.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "total_uploads": 50,
  "total_size": 1024000000,
  "uploads_this_month": 10,
  "most_used_domain": "img.bulletdrop.com",
  "storage_used_percentage": 25.5
}
```

### GET /api/stats/global
Get global platform statistics.

**Response:**
```json
{
  "total_users": 1000,
  "total_uploads": 50000,
  "total_size": "10GB",
  "uploads_today": 100
}
```

---

## 🔧 Admin Endpoints

### GET /api/admin/users
List all users (admin only).

### DELETE /api/admin/users/{user_id}
Delete user (admin only).

### GET /api/admin/uploads
List all uploads (admin only).

### DELETE /api/admin/uploads/{upload_id}
Delete any upload (admin only).

---

## 🚀 File Serving Endpoints

These are served directly from the CDN/static file server:

### GET /{domain}/{filename}
Serve uploaded file.

**Examples:**
- `https://img.bulletdrop.com/abc123.png`
- `https://shots.bulletdrop.com/screenshot.jpg`

### GET /{domain}/{custom_name}
Serve file by custom name.

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message",
  "error_code": "VALIDATION_ERROR",
  "status_code": 400
}
```

### Common Error Codes
- `VALIDATION_ERROR` (400)
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `NOT_FOUND` (404)
- `FILE_TOO_LARGE` (413)
- `UNSUPPORTED_FILE_TYPE` (415)
- `RATE_LIMITED` (429)
- `INTERNAL_ERROR` (500)