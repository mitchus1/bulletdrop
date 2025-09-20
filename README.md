# BulletDrop

Discord profile and image hosting platform with custom domains and screenshot tools.

## Quick Setup

### Prerequisites

- Node.js (18+)
- Python (3.9+)
- PostgreSQL
- Redis (optional)

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone <your-repo-url>
   cd bulletdrop
   npm run install:all
   ```

2. **Database setup:**
   ```bash
   # Create PostgreSQL database
   createdb bulletdrop

   # Create database user
   psql -c "CREATE USER bulletdrop WITH PASSWORD 'bulletdrop123';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE bulletdrop TO bulletdrop;"
   ```

3. **Backend configuration:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your settings (see configuration section below)

   # Setup Python environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Run database migrations
   alembic upgrade head

   # Create admin user
   python create_admin.py
   ```

4. **Start development servers:**
   ```bash
   # From project root
   npm run dev
   ```

   This starts both frontend (http://localhost:5173) and backend (http://localhost:8000).

## Configuration

### Backend Environment (.env)

```env
# Database
DATABASE_URL=postgresql://bulletdrop:bulletdrop123@localhost/bulletdrop

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production-make-it-long-and-random

# Upload Configuration
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# CORS - Frontend URLs
ALLOWED_HOSTS=http://localhost:3000,http://localhost:5173

# Optional: Redis for caching/sessions
REDIS_URL=redis://localhost:6379

# Optional: Discord OAuth
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_REDIRECT_URI=http://localhost:3000/auth/discord/callback

# Optional: Custom domain support
DOMAIN_VALIDATION_ENABLED=false
CUSTOM_DOMAIN_SUPPORT=false

# Optional: Email configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourdomain.com
```

### Frontend Configuration

Frontend configuration is handled through environment variables or build-time constants. Create `frontend/.env` if needed:

```env
VITE_API_URL=http://localhost:8000
VITE_DISCORD_CLIENT_ID=your_discord_client_id
```

## Available Scripts

### Root Project
- `npm run dev` - Start both frontend and backend in development mode
- `npm run build` - Build both frontend and backend for production
- `npm run install:all` - Install all dependencies

### Backend (cd backend)
- `python -m uvicorn app.main:app --reload` - Start backend development server
- `alembic upgrade head` - Run database migrations
- `python create_admin.py` - Create admin user
- `pytest` - Run tests

### Frontend (cd frontend)
- `npm run dev` - Start frontend development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint

## Features

- **Image Hosting**: Upload and share images with direct links
- **Discord Integration**: OAuth login and profile management
- **Custom Domains**: Support for custom domain routing
- **Screenshot Tools**: ShareX integration and custom tools
- **Admin Panel**: User and content management
- **API**: RESTful API for integrations

## API Endpoints

### Authentication
- `POST /auth/login` - Login with username/password
- `POST /auth/discord` - Discord OAuth login
- `POST /auth/logout` - Logout

### File Upload
- `POST /upload` - Upload image/file
- `GET /files/{filename}` - Access uploaded files
- `DELETE /files/{filename}` - Delete file (owner only)

### User Management
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update profile
- `GET /users/{username}` - Get user profile

### Admin (requires admin role)
- `GET /admin/users` - List all users
- `DELETE /admin/users/{user_id}` - Delete user
- `GET /admin/files` - List all files

## Database Schema

The application uses SQLAlchemy with Alembic for migrations. Key models:

- **User**: User accounts and profiles
- **File**: Uploaded files and metadata
- **Domain**: Custom domain configurations
- **Session**: User sessions

## Troubleshooting

### Common Issues

**Database connection fails:**
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database and user exist

**Frontend can't connect to backend:**
- Check ALLOWED_HOSTS in backend .env
- Verify VITE_API_URL in frontend
- Ensure backend is running on correct port

**File uploads fail:**
- Check UPLOAD_DIR permissions
- Verify MAX_FILE_SIZE setting
- Ensure sufficient disk space

**Permission denied errors:**
- Check file/directory permissions
- Ensure upload directory is writable
- Verify database user has correct privileges

### Development Tips

- Use `npm run dev` for hot-reload development
- Check browser console and backend logs for errors
- Database changes require new migrations: `alembic revision --autogenerate -m "description"`
- Reset database: Drop database, recreate, and run `alembic upgrade head`

## Production Deployment

For production deployment:

1. Set secure SECRET_KEY
2. Use production database
3. Configure proper CORS origins
4. Set up reverse proxy (nginx)
5. Use HTTPS
6. Configure file upload limits
7. Set up monitoring and backups

## License

MIT
