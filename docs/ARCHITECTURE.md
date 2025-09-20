# BulletDrop Architecture Documentation

This document provides a comprehensive overview of the BulletDrop platform architecture, including system design, component interactions, data flow, and deployment considerations.

## Table of Contents

- [System Overview](#system-overview)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Database Design](#database-design)
- [Authentication & Security](#authentication--security)
- [File Storage & Management](#file-storage--management)
- [API Design](#api-design)
- [Deployment Architecture](#deployment-architecture)
- [Scalability Considerations](#scalability-considerations)

## System Overview

BulletDrop is a modern, full-stack web application built with a microservices-oriented architecture that separates concerns between a FastAPI backend and React frontend.

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (React SPA)   │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│                 │    │                 │    │                 │
│ • React 18      │    │ • Python 3.8+  │    │ • User Data     │
│ • TypeScript    │    │ • FastAPI       │    │ • Upload Meta   │
│ • Tailwind CSS │    │ • SQLAlchemy    │    │ • Domain Config │
│ • Vite         │    │ • Pydantic      │    │ • Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN/Static    │    │  File Storage   │    │   OAuth Providers│
│   Files         │    │   (Local/S3)    │    │                 │
│                 │    │                 │    │ • Google        │
│ • Uploaded      │    │ • Images        │    │ • GitHub        │
│   Files         │    │ • Documents     │    │ • Discord       │
│ • Custom URLs   │    │ • Videos        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **Frontend Application** - React-based single-page application
2. **Backend API** - FastAPI-based REST API server
3. **Database Layer** - PostgreSQL with SQLAlchemy ORM
4. **File Storage** - Local filesystem or cloud storage (S3-compatible)
5. **Authentication System** - JWT + OAuth integration
6. **Admin Panel** - Administrative interface for platform management

## Backend Architecture

The backend follows a layered architecture pattern with clear separation of concerns:

### Layer Structure

```
┌─────────────────────────────────────────────────────────┐
│                   API Layer                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │    Auth     │ │   Uploads   │ │   Admin     │ ...  │
│  │   Routes    │ │   Routes    │ │   Routes    │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                 Service Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │   Upload    │ │    OAuth    │ │   Storage   │ ...  │
│  │  Service    │ │  Service    │ │  Service    │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                 Data Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │    User     │ │   Upload    │ │   Domain    │ ...  │
│  │   Model     │ │   Model     │ │   Model     │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                Database Layer                           │
│              PostgreSQL + SQLAlchemy                   │
└─────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. API Routes (`app/api/routes/`)

- **Authentication Routes** (`auth.py`) - User registration, login, OAuth
- **Upload Routes** (`uploads.py`) - File upload and management
- **User Routes** (`users.py`) - User profile management
- **Domain Routes** (`domains.py`) - Domain configuration
- **Admin Routes** (`admin.py`) - Administrative operations

#### 2. Core Services (`app/core/`)

- **Configuration** (`config.py`) - Application settings management
- **Database** (`database.py`) - Database connection and session management
- **Security** (`security.py`) - Authentication and authorization utilities

#### 3. Business Logic (`app/services/`)

- **Upload Service** (`upload_service.py`) - File processing and storage
- **OAuth Service** (`oauth.py`) - Third-party authentication integration

#### 4. Data Models (`app/models/`)

- **User Model** (`user.py`) - User account representation
- **Upload Model** (`upload.py`) - File upload metadata
- **Domain Model** (`domain.py`) - Available hosting domains

#### 5. Data Schemas (`app/schemas/`)

- **Pydantic Models** - Request/response validation and serialization

## Frontend Architecture

The frontend is built as a modern React SPA with TypeScript and follows component-based architecture:

### Component Hierarchy

```
App.tsx
├── AuthProvider
│   ├── ThemeProvider
│   │   ├── Router
│   │   │   ├── Layout
│   │   │   │   ├── Navigation
│   │   │   │   ├── Sidebar
│   │   │   │   └── Content
│   │   │   │       ├── Home
│   │   │   │       ├── Login/Register
│   │   │   │       ├── Dashboard
│   │   │   │       │   ├── FileUpload
│   │   │   │       │   ├── UploadsList
│   │   │   │       │   └── UserStats
│   │   │   │       ├── Profile
│   │   │   │       └── AdminDashboard
│   │   │   └── ProtectedRoute
```

### State Management

#### Context Providers

1. **AuthContext** - Manages user authentication state
   - Current user information
   - JWT token management
   - Login/logout functions
   - Auto-refresh functionality

2. **ThemeContext** - Manages application theming
   - Dark/light mode toggle
   - Theme persistence in localStorage
   - CSS class management

#### Local State

- Component-specific state using React hooks
- Form state management with React Hook Form
- Upload progress tracking

### Service Layer

#### API Service (`services/api.ts`)

Centralized HTTP client with:
- Automatic JWT token handling
- Request/response interceptors
- Error handling and retry logic
- TypeScript interfaces for all endpoints

#### Admin Service (`services/admin.ts`)

Specialized service for admin operations with enhanced security checks.

## Database Design

### Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Users       │     │    Uploads      │     │    Domains      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │────►│ id (PK)         │  ┌──│ id (PK)         │
│ username        │     │ user_id (FK)    │  │  │ domain_name     │
│ email           │     │ filename        │  │  │ display_name    │
│ hashed_password │     │ original_name   │  │  │ description     │
│ oauth_ids       │     │ file_size       │  │  │ is_available    │
│ profile_data    │     │ mime_type       │  │  │ is_premium      │
│ storage_info    │     │ upload_url      │  │  │ max_file_size   │
│ account_status  │     │ custom_name     │  │  │ created_at      │
│ timestamps      │     │ domain_id (FK)  │──┘  └─────────────────┘
└─────────────────┘     │ view_count      │
                        │ is_public       │
                        │ expires_at      │
                        │ timestamps      │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ UserDomains     │
                        ├─────────────────┤
                        │ id (PK)         │
                        │ user_id (FK)    │
                        │ domain_id (FK)  │
                        │ claimed_at      │
                        └─────────────────┘
```

### Database Schema Details

#### Users Table

- **Primary Key**: Auto-incrementing integer ID
- **Unique Constraints**: username, email, OAuth provider IDs
- **Indexes**: username, email for fast lookups
- **Storage Tracking**: Real-time storage usage and limits

#### Uploads Table

- **Primary Key**: Auto-incrementing integer ID
- **Foreign Keys**: user_id (Users), domain_id (Domains)
- **Indexes**: user_id, created_at for efficient queries
- **File Integrity**: SHA-256 hashes for deduplication

#### Domains Table

- **Configuration-driven**: Available hosting domains
- **Permissions**: Premium domains for certain user tiers
- **Constraints**: File size limits per domain

### Migration Strategy

- **Alembic** for version-controlled database migrations
- **Backward compatibility** for schema changes
- **Data migration scripts** for complex transformations

## Authentication & Security

### Multi-Layer Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Security Layers                       │
├─────────────────────────────────────────────────────────┤
│ 1. Transport Layer (HTTPS/TLS)                         │
├─────────────────────────────────────────────────────────┤
│ 2. CORS & Request Validation                           │
├─────────────────────────────────────────────────────────┤
│ 3. Rate Limiting & DDoS Protection                     │
├─────────────────────────────────────────────────────────┤
│ 4. JWT Token Authentication                            │
├─────────────────────────────────────────────────────────┤
│ 5. Role-Based Access Control (RBAC)                    │
├─────────────────────────────────────────────────────────┤
│ 6. Input Validation & Sanitization                     │
├─────────────────────────────────────────────────────────┤
│ 7. File Type & Size Validation                         │
├─────────────────────────────────────────────────────────┤
│ 8. Database Query Protection (SQLAlchemy ORM)          │
└─────────────────────────────────────────────────────────┘
```

### Authentication Flow

#### JWT Authentication

1. **User Login** → Credentials validation → JWT token generation
2. **Token Storage** → Secure storage in browser (localStorage/httpOnly cookies)
3. **Request Authentication** → Bearer token in Authorization header
4. **Token Validation** → Signature verification + expiration check
5. **User Context** → Database lookup for current user state

#### OAuth Integration

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │ BulletDrop  │    │   OAuth     │
│             │    │   Server    │    │  Provider   │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │
      │ 1. OAuth Request │                  │
      ├─────────────────►│                  │
      │                  │ 2. Redirect      │
      │                  ├─────────────────►│
      │                  │                  │
      │ 3. User Auth     │                  │
      │◄─────────────────┴─────────────────►│
      │                  │                  │
      │ 4. Auth Code     │                  │
      ├─────────────────►│                  │
      │                  │ 5. Token Exchange│
      │                  ├─────────────────►│
      │                  │ 6. Access Token  │
      │                  │◄─────────────────┤
      │                  │ 7. User Info     │
      │                  ├─────────────────►│
      │                  │ 8. User Data     │
      │                  │◄─────────────────┤
      │ 9. JWT Token     │                  │
      │◄─────────────────┤                  │
```

### Security Features

1. **Password Security**
   - Bcrypt hashing with salt rounds
   - Minimum password complexity requirements
   - Password breach detection (planned)

2. **Session Management**
   - JWT tokens with configurable expiration
   - Refresh token mechanism
   - Token blacklisting capability

3. **File Security**
   - MIME type validation
   - File size limits
   - Malware scanning (planned)
   - Content moderation (planned)

4. **API Security**
   - Rate limiting per user/IP
   - CORS configuration
   - Request size limits
   - SQL injection prevention via ORM

## File Storage & Management

### Storage Architecture

```
┌─────────────────────────────────────────────────────────┐
│                File Upload Flow                         │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │   Server    │    │   Storage   │
│             │    │             │    │             │
│ File Select ├───►│ Validation  ├───►│ File Save   │
│             │    │             │    │             │
│ Progress    │◄───┤ Processing  │◄───┤ URL Gen     │
│             │    │             │    │             │
│ URL Receive │◄───┤ Response    │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

### File Processing Pipeline

1. **Upload Validation**
   - File type checking (MIME validation)
   - File size limits (per user tier)
   - Storage quota verification
   - Filename sanitization

2. **File Processing**
   - Unique filename generation (UUID-based)
   - SHA-256 hash calculation for deduplication
   - Metadata extraction (size, type, dimensions)
   - Thumbnail generation (for images)

3. **Storage Operations**
   - Local filesystem storage (development)
   - Cloud storage integration (S3-compatible)
   - CDN distribution (planned)
   - Backup and redundancy (planned)

4. **URL Generation**
   - Custom domain mapping
   - SEO-friendly URLs
   - Access control enforcement
   - Analytics tracking

### Storage Providers

#### Local Storage (Development)
```python
uploads/
├── 2023/
│   ├── 01/
│   │   ├── 15/
│   │   │   ├── uuid_filename.ext
│   │   │   └── uuid_filename.ext
```

#### Cloud Storage (Production)
- S3-compatible storage providers
- CloudFront/CloudFlare CDN integration
- Geographic distribution
- Automated backups

## API Design

### RESTful Design Principles

The API follows REST conventions with clear resource-based URLs:

- **Resources**: `/api/uploads/`, `/api/domains/`, `/users/`
- **HTTP Methods**: GET (read), POST (create), PATCH (update), DELETE (remove)
- **Status Codes**: Consistent HTTP status code usage
- **Response Format**: JSON with consistent error structure

### Versioning Strategy

- **URL Versioning**: `/api/v1/`, `/api/v2/` (planned)
- **Backward Compatibility**: Maintain older versions during transition
- **Deprecation Policy**: 6-month notice for version deprecation

### Documentation

- **OpenAPI/Swagger**: Auto-generated from FastAPI
- **Interactive Docs**: `/docs` and `/redoc` endpoints
- **Postman Collection**: Exported API collection for testing

## Deployment Architecture

### Development Environment

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│  localhost:5173 │    │ localhost:8000  │
│                 │    │                 │
│ • Vite Dev      │    │ • Uvicorn       │
│ • Hot Reload    │    │ • Auto Reload   │
│ • Source Maps   │    │ • Debug Mode    │
└─────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │ localhost:5432  │
                    │                 │
                    │ • Dev Database  │
                    │ • Test Data     │
                    └─────────────────┘
```

### Production Environment (Recommended)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Web Servers   │    │   Database      │
│   (nginx)       │    │   (Gunicorn +   │    │   (PostgreSQL)  │
│                 │    │    Uvicorn)     │    │                 │
│ • SSL Term      │    │ • Multiple      │    │ • Primary/      │
│ • Rate Limiting │    │   Workers       │    │   Replica       │
│ • Static Files  │    │ • Health Checks │    │ • Backups       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      CDN        │    │  File Storage   │    │   Monitoring    │
│  (CloudFlare)   │    │     (S3)        │    │  (Prometheus)   │
│                 │    │                 │    │                 │
│ • Global Cache  │    │ • File Hosting  │    │ • Metrics       │
│ • DDoS Protect  │    │ • Backups       │    │ • Alerts        │
│ • Compression   │    │ • CDN Sync      │    │ • Logging       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Container Deployment (Docker)

```yaml
# docker-compose.yml structure
services:
  frontend:
    build: ./frontend
    ports: ["80:80"]
    depends_on: [backend]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [database, redis]
    environment:
      - DATABASE_URL
      - SECRET_KEY

  database:
    image: postgres:14
    volumes: ["postgres_data:/var/lib/postgresql/data"]
    environment:
      - POSTGRES_DB
      - POSTGRES_USER
      - POSTGRES_PASSWORD

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

## Scalability Considerations

### Horizontal Scaling

1. **Stateless Backend**
   - JWT tokens eliminate server-side sessions
   - Database connection pooling
   - Shared file storage

2. **Load Balancing**
   - Multiple backend instances
   - Round-robin/least-connections algorithms
   - Health check endpoints

3. **Database Scaling**
   - Read replicas for query performance
   - Connection pooling (PgBouncer)
   - Query optimization and indexing

### Performance Optimizations

1. **Caching Strategy**
   - Redis for session data
   - CDN for static assets
   - Database query caching

2. **File Storage**
   - CDN distribution
   - Progressive image loading
   - Compression and optimization

3. **API Optimization**
   - Pagination for large datasets
   - Field selection (sparse fieldsets)
   - ETags for conditional requests

### Monitoring & Observability

1. **Application Metrics**
   - Request/response times
   - Error rates and patterns
   - User activity tracking

2. **Infrastructure Metrics**
   - Server resource usage
   - Database performance
   - Storage utilization

3. **Alerting**
   - Uptime monitoring
   - Error threshold alerts
   - Performance degradation detection

## Security Architecture

### Defense in Depth

Multiple security layers protect the application:

1. **Network Security** - Firewall rules, VPN access
2. **Application Security** - Input validation, output encoding
3. **Data Security** - Encryption at rest and in transit
4. **Access Control** - Authentication and authorization
5. **Monitoring** - Security event logging and alerting

### Compliance Considerations

- **GDPR** - User data privacy and right to deletion
- **CCPA** - California consumer privacy rights
- **SOC 2** - Security and availability controls (planned)

This architecture provides a solid foundation for a scalable, secure, and maintainable image hosting platform while maintaining flexibility for future enhancements and integrations.