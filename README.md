# BulletDrop

Modern file sharing and profile platform with advanced customization, OAuth integration, and beautiful UI effects.

## ✨ Features

### 🔐 Authentication & Security
- **Multi-OAuth Support**: GitHub, Google, Discord integration
- **Secure Sessions**: JWT-based authentication with refresh tokens
- **Rate Limiting**: Advanced rate limiting to prevent brute force attacks
- **IP Blocking**: Automatic blocking of suspicious IPs
- **Admin Panel**: Comprehensive user and content management
- **Password Management**: Secure password handling with bcrypt

### 📁 File Management
- **Smart Upload System**: Drag & drop with progress indicators
- **ShareX Integration**: Custom ShareX configuration for seamless uploads
- **File Organization**: User-specific file management and organization
- **Storage Analytics**: Real-time storage usage tracking

### 🎨 Profile Customization
- **Dynamic Backgrounds**: Custom images, colors, and effects
- **Matrix Rain Effect**: Animated digital rain background (toggleable)
- **Social Links**: GitHub, Discord, Telegram, Instagram integration
- **Custom Domains**: Personal domain support for profiles
- **Responsive Design**: Beautiful on all devices

### 🌟 Premium Features
- **Enhanced Image Effects**: RGB borders and advanced filters
- **Premium Domains**: Access to exclusive domain options
- **Increased Storage**: Higher upload limits
- **Priority Support**: Enhanced user experience

### 🛠 Developer Experience
- **Modern Stack**: React + TypeScript + FastAPI + PostgreSQL
- **Real-time Updates**: Live view tracking and notifications
- **Comprehensive API**: RESTful endpoints for all features
- **Database Migrations**: Alembic-powered schema management

## 🚀 Quick Setup

### Prerequisites

- **Node.js** (18+)
- **Python** (3.9+)
- **PostgreSQL** (12+)
- **Redis** (optional, for caching)

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

## ⚙️ Configuration

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

# OAuth Providers
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret

# OAuth Redirect URIs
GITHUB_REDIRECT_URI=http://localhost:3000/auth/github/callback
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
DISCORD_REDIRECT_URI=http://localhost:3000/auth/discord/callback

# Optional: Redis for caching/sessions
REDIS_URL=redis://localhost:6379

# Rate Limiting (requires Redis)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_PER_MINUTE=5
RATE_LIMIT_AUTH_PER_HOUR=20
RATE_LIMIT_API_PER_MINUTE=60
RATE_LIMIT_API_PER_HOUR=1000
RATE_LIMIT_UPLOAD_PER_MINUTE=10
RATE_LIMIT_UPLOAD_PER_HOUR=100
RATE_LIMIT_BLOCK_DURATION=300

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

Frontend configuration is handled through environment variables. Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_GITHUB_CLIENT_ID=your_github_client_id
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_DISCORD_CLIENT_ID=your_discord_client_id
```

## 📋 Available Scripts

### Root Project
- `npm run dev` - Start both frontend and backend in development mode
- `npm run build` - Build both frontend and backend for production
- `npm run install:all` - Install all dependencies
- `./full-deploy.sh` - Full production deployment script

### Backend (cd backend)
- `python -m uvicorn app.main:app --reload` - Start backend development server
- `alembic upgrade head` - Run database migrations
- `alembic revision --autogenerate -m "description"` - Generate new migration
- `python create_admin.py` - Create admin user
- `pytest` - Run tests

### Frontend (cd frontend)
- `npm run dev` - Start frontend development server (Vite)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - TypeScript type checking

## Features

- **Image Hosting**: Upload and share images with direct links
- **Discord Integration**: OAuth login and profile management
- **Custom Domains**: Support for custom domain routing
- **Screenshot Tools**: ShareX integration and custom tools
- **Rate Limiting**: Comprehensive rate limiting with Redis-based storage
- **Security**: IP blocking, brute force protection, and attack prevention
- **Admin Panel**: User and content management with rate limit monitoring
- **API**: RESTful API for integrations

## 🛡️ Security Features

### Rate Limiting
BulletDrop includes comprehensive rate limiting to protect against various attacks:

- **Authentication Endpoints**: 5 requests/minute, 20 requests/hour
- **API Endpoints**: 60 requests/minute, 1000 requests/hour  
- **Upload Endpoints**: 10 requests/minute, 100 requests/hour
- **Automatic IP Blocking**: IPs exceeding auth limits are blocked for 5 minutes
- **Admin Controls**: View blocked IPs, manually block/unblock addresses
- **Redis-based**: Distributed rate limiting using sliding window algorithm

Rate limiting can be configured via environment variables and disabled if needed.

### Admin Rate Limit Management
- `/admin/rate-limits/blocked-ips` - View currently blocked IP addresses
- `/admin/rate-limits/block-ip` - Manually block an IP address
- `/admin/rate-limits/unblock-ip/{ip}` - Unblock an IP address
- `/admin/rate-limits/stats` - View rate limiting statistics
- `/admin/rate-limits/clear-all` - Clear all rate limiting data (emergency use)

## 🔗 API Endpoints

### Authentication
- `POST /auth/login` - Login with username/password
- `POST /auth/register` - Register new account
- `POST /auth/logout` - Logout current session
- `POST /auth/github` - GitHub OAuth login
- `POST /auth/google` - Google OAuth login
- `POST /auth/discord` - Discord OAuth login
- `GET /auth/me` - Get current authenticated user

### File Management
- `POST /upload` - Upload image/file with progress tracking
- `POST /upload/sharex` - ShareX-compatible upload endpoint
- `GET /uploads/{filename}` - Access uploaded files
- `DELETE /uploads/{filename}` - Delete file (owner only)
- `GET /api/uploads` - List user's uploads with pagination

### User Profiles
- `GET /users/me` - Get current user profile with full details
- `PUT /users/me` - Update profile (bio, social links, preferences)
- `GET /users/{username}` - Get public user profile
- `GET /profile/{username}` - Get profile page data
- `POST /profile/{username}/view` - Track profile view

### Admin Panel (requires admin role)
- `GET /admin/users` - List all users with filters
- `DELETE /admin/users/{user_id}` - Delete user and associated data
- `PUT /admin/users/{user_id}` - Update user permissions
- `GET /admin/uploads` - List all uploads with moderation tools
- `DELETE /admin/uploads/{upload_id}` - Delete any upload
- `GET /admin/stats` - Platform statistics and analytics

### Domain Management
- `GET /domains` - List available domains
- `GET /domains/user/{user_id}` - Get user's domain preferences

## 🗄️ Database Schema

The application uses SQLAlchemy with Alembic for migrations. Key models:

### Core Models
- **User**: User accounts, profiles, OAuth integrations, preferences
  - Authentication (password, OAuth tokens)
  - Profile data (bio, social links, appearance settings)
  - Permissions and premium status
  - Storage usage and limits

- **Upload**: File uploads with comprehensive metadata
  - File information (size, type, dimensions)
  - Upload tracking (date, IP, user agent)
  - Access control and permissions
  - Storage optimization

- **Domain**: Custom domain configurations
  - Domain validation and SSL
  - User associations and preferences
  - Premium domain features

- **ProfileView**: Profile visit tracking
  - View analytics and statistics
  - IP-based tracking with privacy controls
  - Real-time view counters

### Advanced Features
- **OAuth Integration**: Multi-provider authentication
- **File Management**: Advanced upload handling with progress
- **User Preferences**: Customizable UI and behavior settings
- **Admin Tools**: Comprehensive moderation and management

## 🛠️ Troubleshooting

### Common Issues

**Database connection fails:**
- Ensure PostgreSQL is running: `sudo systemctl status postgresql`
- Check DATABASE_URL in .env file
- Verify database and user exist with correct permissions
- Test connection: `psql -h localhost -U bulletdrop -d bulletdrop`

**Frontend can't connect to backend:**
- Check ALLOWED_HOSTS in backend .env (include frontend URL)
- Verify VITE_API_URL in frontend .env
- Ensure backend is running on correct port (8000)
- Check browser console for CORS errors

**OAuth authentication fails:**
- Verify OAuth app credentials in .env
- Check redirect URIs match OAuth app settings
- Ensure OAuth apps are enabled and configured
- Check backend logs for OAuth errors

**File uploads fail:**
- Check UPLOAD_DIR permissions: `chmod 755 uploads/`
- Verify MAX_FILE_SIZE setting
- Ensure sufficient disk space
- Check nginx/proxy upload limits

**Matrix effect not working:**
- Ensure user has matrix_effect_enabled = true in database
- Check browser console for JavaScript errors
- Verify CSS animations are enabled
- Try refreshing the page

**Permission denied errors:**
- Check file/directory permissions: `ls -la`
- Ensure upload directory is writable: `chmod 755 uploads/`
- Verify database user has correct privileges
- Check systemd service permissions for production

### Development Tips

- Use `npm run dev` for hot-reload development
- Check browser console and backend logs for detailed errors
- Database changes require new migrations: `alembic revision --autogenerate -m "description"`
- Reset database: Drop database, recreate, and run `alembic upgrade head`
- Use `./full-deploy.sh` for production deployment testing
- Monitor backend logs: `sudo journalctl -u bulletdrop-backend.service -f`

### Performance Optimization

- Enable Redis for session caching
- Configure nginx for static file serving
- Use database connection pooling
- Implement image optimization and CDN
- Monitor storage usage and cleanup old files

## 🚀 Production Deployment

### Docker Deployment (Recommended)

```bash
# Build and deploy with Docker
docker-compose up -d

# Or use the deployment script
./full-deploy.sh
```

### Manual Deployment

For production deployment:

1. **Security Configuration**
   - Set secure SECRET_KEY (64+ characters)
   - Use production database with SSL
   - Configure proper CORS origins
   - Enable HTTPS with SSL certificates

2. **Web Server Setup**
   ```nginx
   # Example nginx configuration
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:5173;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Environment Setup**
   - Set NODE_ENV=production
   - Configure production database
   - Set up file upload limits
   - Configure Redis for caching

4. **Monitoring & Maintenance**
   - Set up logging and monitoring
   - Configure automated backups
   - Monitor storage usage
   - Set up health checks

### Environment Variables for Production

```env
# Production overrides
NODE_ENV=production
DATABASE_URL=postgresql://user:password@localhost:5432/bulletdrop_prod
SECRET_KEY=your-super-secure-production-key
ALLOWED_HOSTS=https://yourdomain.com,https://www.yourdomain.com
```

## 📊 Features Overview

### User Interface
- 🎨 **Modern Design**: Clean, responsive UI with dark/light themes
- 🌟 **Animations**: Smooth transitions and interactive elements
- 📱 **Mobile First**: Optimized for all device sizes
- ♿ **Accessibility**: WCAG compliant with keyboard navigation

### File Management
- 📎 **Drag & Drop**: Intuitive file upload experience
- 📊 **Progress Tracking**: Real-time upload progress
- 🔄 **ShareX Integration**: Custom configuration for seamless uploads
- 📁 **Organization**: Smart file categorization and search

### Social Features
- 👥 **Profile Pages**: Customizable user profiles with social links
- 👀 **View Tracking**: Real-time profile view analytics
- 🔗 **Social Integration**: GitHub, Discord, Google, Instagram links
- 🌐 **Custom Domains**: Personal domain support for profiles

### Administrative Tools
- 👑 **Admin Dashboard**: Comprehensive user and content management
- 📈 **Analytics**: Platform usage statistics and insights
- 🛡️ **Moderation**: Content moderation and user management tools
- ⚙️ **Configuration**: System-wide settings and preferences

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/bulletdrop.git
cd bulletdrop

# Install dependencies
npm run install:all

# Start development environment
npm run dev
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ using React, TypeScript, and FastAPI
- Icons by [Heroicons](https://heroicons.com/)
- UI components inspired by [Tailwind UI](https://tailwindui.com/)
- Matrix effect inspired by classic cyberpunk aesthetics

---

**BulletDrop** - Share files, express yourself, connect with others. 🚀
