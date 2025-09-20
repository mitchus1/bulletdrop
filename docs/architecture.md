# BulletDrop System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   File Storage  │
                    │   (Static/CDN)  │
                    │   Multi-domain  │
                    └─────────────────┘
```

## 📁 Directory Structure

```
bulletdrop/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── api/            # API route handlers
│   │   │   └── routes/
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── uploads.py
│   │   │       └── domains.py
│   │   ├── core/           # Core application logic
│   │   │   ├── config.py   # Configuration settings
│   │   │   ├── database.py # Database connection
│   │   │   ├── security.py # Authentication/JWT
│   │   │   └── storage.py  # File storage logic
│   │   ├── models/         # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── upload.py
│   │   │   └── domain.py
│   │   ├── schemas/        # Pydantic schemas
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   └── upload.py
│   │   ├── services/       # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── upload_service.py
│   │   │   └── domain_service.py
│   │   └── utils/          # Utility functions
│   │       ├── file_utils.py
│   │       └── validation.py
│   ├── migrations/         # Alembic migrations
│   ├── tests/             # Backend tests
│   ├── uploads/           # Local file storage
│   ├── requirements.txt
│   └── .env
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   │   ├── auth/
│   │   │   ├── upload/
│   │   │   ├── profile/
│   │   │   └── common/
│   │   ├── pages/          # Page components
│   │   │   ├── Home.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── Profile.tsx
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API service functions
│   │   ├── store/          # State management
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utility functions
│   ├── public/
│   └── package.json
├── shared/                 # Shared types and utilities
│   ├── types/
│   └── constants/
├── docs/                   # Documentation
│   ├── api-endpoints.md
│   ├── architecture.md
│   └── deployment.md
├── docker/                 # Docker configuration
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── scripts/               # Utility scripts
│   ├── setup.sh
│   ├── backup.sh
│   └── deploy.sh
├── .github/
│   ├── workflows/         # CI/CD workflows
│   └── copilot-instructions.md
├── README.md
├── TODO.md
└── package.json           # Root package.json
```

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    discord_id VARCHAR(50) UNIQUE,
    avatar_url TEXT,
    bio TEXT,
    custom_domain VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    storage_limit BIGINT DEFAULT 1073741824, -- 1GB in bytes
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Uploads Table
```sql
CREATE TABLE uploads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_hash VARCHAR(64) UNIQUE, -- SHA-256 for deduplication
    upload_url TEXT NOT NULL,
    custom_name VARCHAR(100),
    domain_id INTEGER REFERENCES domains(id),
    view_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Domains Table
```sql
CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    domain_name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,
    max_file_size BIGINT DEFAULT 10485760, -- 10MB
    created_at TIMESTAMP DEFAULT NOW()
);
```

### User_Domains Table (Many-to-Many)
```sql
CREATE TABLE user_domains (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT FALSE,
    claimed_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, domain_id)
);
```

### Upload_Analytics Table
```sql
CREATE TABLE upload_analytics (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    ip_address INET,
    user_agent TEXT,
    referer TEXT,
    country VARCHAR(2),
    accessed_at TIMESTAMP DEFAULT NOW()
);
```

## 🔧 Technology Stack Details

### Backend (FastAPI)
- **Framework**: FastAPI 0.104+
- **Database ORM**: SQLAlchemy 2.0+
- **Authentication**: JWT tokens with python-jose
- **Password Hashing**: bcrypt via passlib
- **File Upload**: python-multipart
- **Image Processing**: Pillow (PIL)
- **Validation**: Pydantic v2
- **Database Migrations**: Alembic
- **Testing**: pytest + httpx
- **Background Tasks**: FastAPI BackgroundTasks

### Frontend (React)
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **State Management**: React Context + useReducer
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form
- **File Upload**: React Dropzone
- **Notifications**: React Hot Toast
- **Testing**: Jest + React Testing Library

### Database (PostgreSQL)
- **Version**: PostgreSQL 14+
- **Connection Pooling**: SQLAlchemy connection pool
- **Indexing Strategy**:
  - Users: username, email
  - Uploads: user_id, filename, created_at
  - Domains: domain_name
- **Full-text Search**: PostgreSQL built-in search

### File Storage
- **Development**: Local filesystem
- **Production Options**:
  - AWS S3 + CloudFront
  - Cloudflare R2 + CDN
  - DigitalOcean Spaces
- **File Organization**:
  ```
  uploads/
  ├── 2025/09/19/        # Date-based folders
  │   ├── abc123.png
  │   └── def456.jpg
  └── thumbnails/        # Generated thumbnails
      ├── 2025/09/19/
      └── ...
  ```

## 🌐 Domain & CDN Architecture

### Domain Routing
```
┌─────────────────┐
│  Main Domain    │
│  bulletdrop.com │
└─────────────────┘
         │
    ┌────┴────┐
    │ Subdomain │
    │ Routing   │
    └────┬────┘
         │
    ┌────▼────────────────────┐
    │                         │
┌───▼────┐  ┌─────▼─────┐  ┌──▼────┐
│img.    │  │shots.     │  │cdn.   │
│bullet  │  │bullet     │  │bullet │
│drop.com│  │drop.com   │  │drop.com│
└────────┘  └───────────┘  └───────┘
```

### File URL Structure
- **Standard**: `https://img.bulletdrop.com/{hash}.{ext}`
- **Custom**: `https://img.bulletdrop.com/{custom_name}.{ext}`
- **User**: `https://shots.bulletdrop.com/u/{username}/{filename}`

## 🔄 Data Flow

### Upload Process
1. **Client**: Select file → Validate → Start upload
2. **Frontend**: Create FormData → POST to `/api/uploads`
3. **Backend**: 
   - Validate file (size, type, malware)
   - Generate unique filename
   - Save to storage
   - Create database record
   - Return upload URL
4. **Frontend**: Update UI with success/error

### Authentication Flow
1. **Login**: Email/password → JWT token
2. **Storage**: Token in httpOnly cookie + localStorage
3. **Requests**: Token in Authorization header
4. **Refresh**: Auto-refresh before expiry
5. **Logout**: Clear token + blacklist

### File Serving Flow
1. **Request**: GET `https://img.bulletdrop.com/abc123.png`
2. **CDN**: Check cache → Serve if cached
3. **Origin**: If not cached → Fetch from storage
4. **Analytics**: Log access (async)
5. **Response**: File with appropriate headers

## 🛡️ Security Architecture

### Authentication & Authorization
- **JWT Tokens**: Short-lived (15 min) with refresh
- **Password Policy**: Min 8 chars, complexity requirements
- **Rate Limiting**: Login attempts, upload frequency
- **Session Management**: Token blacklisting on logout

### File Security
- **Upload Validation**:
  - File type whitelist
  - Size limits per user tier
  - Malware scanning (ClamAV)
  - Image EXIF stripping
- **Access Control**:
  - Public/private file settings
  - Owner-only file management
  - Admin override capabilities

### Infrastructure Security
- **HTTPS Only**: All traffic encrypted
- **CORS**: Restricted origins
- **Headers**: Security headers (HSTS, CSP, etc.)
- **Input Validation**: All endpoints validated
- **SQL Injection**: Parameterized queries only

## 📊 Monitoring & Analytics

### Application Metrics
- **Upload Statistics**: Files per day, total storage
- **User Metrics**: Active users, retention rates
- **Performance**: Response times, error rates
- **Resource Usage**: CPU, memory, storage

### File Analytics
- **View Tracking**: IP, user agent, referer
- **Geographic Data**: Country-level analytics
- **Popular Content**: Most viewed files
- **Bandwidth Usage**: Per user and global

### Error Tracking
- **Application Errors**: Exception tracking
- **API Errors**: 4xx/5xx response monitoring
- **User Experience**: Failed uploads, timeouts
- **Security Events**: Failed logins, suspicious activity