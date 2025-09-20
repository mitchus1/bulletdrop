# BulletDrop - Discord Profile & Image Hosting Platform

A modern, full-stack web application that provides Discord-style user profiles and comprehensive image hosting capabilities with custom domain support. Users can create personalized profiles, upload files with drag-and-drop functionality, and share content through custom domains.

## ✨ Features

### 🔐 Authentication & User Management
- **Multi-Provider Authentication**: JWT-based auth + OAuth integration (Google, GitHub, Discord)
- **Secure Password Management**: Bcrypt password hashing with token refresh capabilities
- **User Profiles**: Comprehensive profile customization with social media links
- **Admin Panel**: Administrative dashboard for platform management

### 📁 File Upload & Hosting
- **Drag-and-Drop Upload**: Modern file upload interface with progress tracking
- **Multiple File Support**: Batch upload capabilities with validation
- **ShareX Integration**: Compatible endpoint for screenshot tools
- **File Management**: View, rename, delete, and organize uploaded files
- **Storage Tracking**: Real-time storage usage monitoring with quotas

### 🌐 Custom Domain Support
- **Domain Selection**: Choose from predefined hosting domains
- **Custom URLs**: User-friendly file URLs with custom naming
- **View Analytics**: Track file views and engagement metrics

### 🎨 Modern UI/UX
- **Dark/Light Themes**: Toggle between theme modes
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Real-time Updates**: Live progress tracking and notifications
- **Accessibility**: WCAG-compliant interface components

## 🛠️ Technology Stack

### Backend Architecture
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - Powerful ORM with PostgreSQL database
- **Alembic** - Database migration management
- **Pydantic** - Data validation and serialization
- **Passlib + Bcrypt** - Secure password hashing
- **Python-JOSE** - JWT token management
- **HTTPx** - Async HTTP client for OAuth integrations
- **Uvicorn** - Lightning-fast ASGI server

### Frontend Architecture
- **React 18** - Modern component-based UI framework
- **TypeScript** - Type-safe JavaScript development
- **Vite** - Next-generation frontend build tool
- **Tailwind CSS** - Utility-first CSS framework
- **React Router DOM** - Client-side routing
- **React Hook Form** - Performant forms with validation
- **React Dropzone** - File upload with drag-and-drop

### Development & Deployment
- **Concurrently** - Run multiple npm scripts simultaneously
- **ESLint** - Code linting and quality enforcement
- **Autoprefixer** - CSS vendor prefix automation
- **PostCSS** - CSS post-processing

## 📁 Project Structure

```
bulletdrop/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/        # API endpoint definitions
│   │   │       ├── auth.py    # Authentication & OAuth
│   │   │       ├── uploads.py # File upload management
│   │   │       ├── users.py   # User management
│   │   │       ├── domains.py # Domain configuration
│   │   │       └── admin.py   # Admin panel endpoints
│   │   ├── core/              # Core application logic
│   │   │   ├── config.py      # Application settings
│   │   │   ├── database.py    # Database configuration
│   │   │   └── security.py    # Auth & security utilities
│   │   ├── models/            # SQLAlchemy database models
│   │   │   ├── user.py        # User account model
│   │   │   ├── upload.py      # File upload model
│   │   │   └── domain.py      # Domain configuration model
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   │   ├── auth.py        # Authentication schemas
│   │   │   ├── upload.py      # Upload schemas
│   │   │   └── admin.py       # Admin schemas
│   │   ├── services/          # Business logic layer
│   │   │   ├── upload_service.py  # File upload operations
│   │   │   └── oauth.py       # OAuth provider integrations
│   │   └── main.py            # FastAPI application entry point
│   ├── migrations/            # Alembic database migrations
│   ├── uploads/               # File storage directory
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   │   ├── FileUpload.tsx # Drag-and-drop upload component
│   │   │   ├── Layout.tsx     # Main application layout
│   │   │   └── ProtectedRoute.tsx # Authentication guard
│   │   ├── contexts/          # React context providers
│   │   │   ├── AuthContext.tsx    # Authentication state
│   │   │   └── ThemeContext.tsx   # Theme management
│   │   ├── hooks/             # Custom React hooks
│   │   │   └── useAuth.ts     # Authentication hook
│   │   ├── pages/             # Page components
│   │   │   ├── Home.tsx       # Landing page
│   │   │   ├── Login.tsx      # User login
│   │   │   ├── Register.tsx   # User registration
│   │   │   ├── Dashboard.tsx  # User dashboard
│   │   │   ├── Uploads.tsx    # File management
│   │   │   ├── Profile.tsx    # User profiles
│   │   │   └── AdminDashboard.tsx # Admin panel
│   │   ├── services/          # API service layer
│   │   │   ├── api.ts         # Main API service
│   │   │   └── admin.ts       # Admin API methods
│   │   ├── types/             # TypeScript type definitions
│   │   │   ├── auth.ts        # Authentication types
│   │   │   └── upload.ts      # Upload types
│   │   ├── App.tsx            # Main application component
│   │   └── main.tsx           # Application entry point
│   ├── public/                # Static assets
│   ├── package.json           # Frontend dependencies
│   └── vite.config.ts         # Vite configuration
├── docs/                      # Documentation files
├── .github/                   # GitHub workflows and templates
├── package.json               # Root package.json for scripts
├── README.md                  # Project documentation
├── TODO.md                    # Development roadmap
└── NEXT-STEPS.md             # Immediate action items
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

### Quick Start (All Services)

From the root directory:
```bash
npm run install:all
npm run dev
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 Development

### Backend Commands
```bash
cd backend
npm run dev          # Start development server
npm run test         # Run tests
npm run migrate      # Run database migrations
```

### Frontend Commands
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
```

## 📚 Documentation

### API Documentation
- **[API Reference](docs/API.md)** - Complete REST API documentation with examples
- **Interactive API Docs** - Available at `http://localhost:8000/docs` when running
- **ReDoc Documentation** - Available at `http://localhost:8000/redoc`

### Technical Documentation
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and component interactions
- **[Development Guide](NEXT-STEPS.md)** - Step-by-step development instructions
- **[Project Roadmap](TODO.md)** - Feature development timeline and priorities

### Code Documentation
- **Backend**: Comprehensive Python docstrings following Google style
- **Frontend**: JSDoc comments for all TypeScript components and functions
- **Type Safety**: Full TypeScript coverage with strict type checking

## 🧪 Testing

### Backend Testing
```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm test
```

### API Testing
Import the Postman collection from `docs/` or use the interactive Swagger UI at `/docs`.

## 🐳 Docker Support

Docker configuration is in development. Current manual setup provides full development capabilities.

**Planned Docker Features:**
- Multi-stage builds for optimized production images
- Docker Compose for full-stack development
- Health checks and monitoring
- Automated deployment pipelines

## 🔧 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Add comprehensive tests for new functionality
4. Ensure all tests pass and code follows style guidelines
5. Update documentation for API or architecture changes
6. Submit a pull request with detailed description

### Code Style Guidelines
- **Backend**: Follow PEP 8, use Black formatter, type hints required
- **Frontend**: ESLint configuration, Prettier formatting, TypeScript strict mode
- **Documentation**: Keep docstrings and comments up-to-date with code changes

## 🆘 Support & Community

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas
- **Wiki**: Additional documentation and guides (coming soon)
- **Discord**: Development community chat (coming soon)

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- React team for the powerful UI library
- SQLAlchemy for robust ORM capabilities
- Tailwind CSS for beautiful, responsive design
- All open-source contributors who make projects like this possible

---

**Built with ❤️ by the BulletDrop team**# bulletdrop
