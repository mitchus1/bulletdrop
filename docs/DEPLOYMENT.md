# 🚀 BulletDrop Deployment Guide

This guide provides comprehensive instructions for deploying BulletDrop on DigitalOcean services using multiple deployment methods.

## 📋 Prerequisites

- DigitalOcean account with billing enabled
- GitHub repository with your BulletDrop code
- Domain name (optional, for custom domains)
- OAuth app credentials (Google, Discord, GitHub)

## 🎯 Deployment Options

### Option 1: DigitalOcean App Platform (Recommended)
### Option 2: DigitalOcean Droplets with Docker
### Option 3: Local Development with DigitalOcean Services

---

## 🚀 Option 1: DigitalOcean App Platform Deployment

### Step 1: Prepare Your Repository

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for DigitalOcean deployment"
   git push origin main
   ```

2. **Update the App Platform configuration:**
   - Edit `.do/app.yaml`
   - Replace `your-username/bulletdrop` with your actual GitHub repository

### Step 2: Create DigitalOcean Resources

#### 2.1 Create a Spaces Bucket

1. Go to DigitalOcean Console → Spaces
2. Create a new Space:
   - **Name:** `bulletdrop-uploads`
   - **Region:** `NYC3` (or your preferred region)
   - **CDN:** Enable for better performance
3. Generate Spaces access keys:
   - Go to API → Spaces Keys
   - Generate new key pair
   - Save the Access Key and Secret Key

#### 2.2 Create Managed Database

1. Go to DigitalOcean Console → Databases
2. Create PostgreSQL database:
   - **Engine:** PostgreSQL 15
   - **Plan:** Basic ($15/month for production, $4/month for dev)
   - **Region:** Same as your app region
   - **Database name:** `bulletdrop`

### Step 3: Set Up OAuth Applications

#### Google OAuth:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `https://your-app-name.ondigitalocean.app/auth/google/callback`

#### Discord OAuth:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application
3. Go to OAuth2 settings
4. Add redirect URI:
   - `https://your-app-name.ondigitalocean.app/auth/discord/callback`

#### GitHub OAuth:
1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create new OAuth App
3. Set authorization callback URL:
   - `https://your-app-name.ondigitalocean.app/auth/github/callback`

### Step 4: Deploy to App Platform

1. **Create App via CLI (doctl):**
   ```bash
   # Install doctl
   snap install doctl

   # Authenticate
   doctl auth init

   # Deploy the app
   doctl apps create --spec .do/app.yaml
   ```

2. **Or via Web Console:**
   - Go to DigitalOcean Console → Apps
   - Click "Create App"
   - Choose "GitHub" as source
   - Select your repository and branch
   - Upload the `.do/app.yaml` spec file

### Step 5: Configure Environment Variables

In the App Platform console, set these environment variables:

**For the API service:**
```env
SECRET_KEY=your_32_character_secret_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
DO_SPACES_KEY=your_spaces_access_key
DO_SPACES_SECRET=your_spaces_secret_key
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
DO_SPACES_BUCKET=bulletdrop-uploads
DO_SPACES_REGION=nyc3
```

### Step 6: Run Database Migrations

1. Access your app's console via DigitalOcean dashboard
2. Run migrations:
   ```bash
   alembic upgrade head
   ```

### Step 7: Configure Domain (Optional)

1. In App Platform console, go to Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Enable automatic HTTPS certificate

---

## 🐳 Option 2: DigitalOcean Droplets with Docker

### Step 1: Create a Droplet

1. **Create Droplet:**
   - Image: Ubuntu 22.04 LTS
   - Size: Basic plan, 2GB RAM minimum
   - Add your SSH key
   - Enable monitoring and backups

2. **Connect to your Droplet:**
   ```bash
   ssh root@your_droplet_ip
   ```

### Step 2: Install Docker and Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git
apt install git -y
```

### Step 3: Deploy Your Application

```bash
# Clone your repository
git clone https://github.com/your-username/bulletdrop.git
cd bulletdrop

# Create environment file
cp .env.example .env
nano .env  # Edit with your values

# Start the application
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

### Step 4: Set Up Nginx Reverse Proxy

```bash
# Install Nginx
apt install nginx -y

# Create Nginx configuration
cat > /etc/nginx/sites-available/bulletdrop << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
ln -s /etc/nginx/sites-available/bulletdrop /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Install SSL certificate
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

---

## 🛠️ Option 3: Local Development with DigitalOcean Services

Perfect for development while using production-grade database and storage.

### Step 1: Set Up DigitalOcean Resources

Follow Steps 2.1 and 2.2 from Option 1 to create:
- DigitalOcean Spaces bucket
- DigitalOcean Managed Database

### Step 2: Configure Local Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your DigitalOcean service credentials
nano .env
```

**Example .env for local development:**
```env
# Local database (or use DigitalOcean database URL)
DATABASE_URL=postgresql://username:password@db-postgresql-nyc3-12345.ondigitalocean.com:25060/bulletdrop?sslmode=require

# DigitalOcean Spaces
DO_SPACES_KEY=your_spaces_key
DO_SPACES_SECRET=your_spaces_secret
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
DO_SPACES_BUCKET=bulletdrop-uploads

# OAuth credentials
GOOGLE_CLIENT_ID=your_google_client_id
# ... other OAuth settings
```

### Step 3: Run Locally

```bash
# Start with Docker Compose
docker-compose up -d

# Or run services individually
cd backend && python -m uvicorn app.main:app --reload
cd frontend && npm run dev
```

---

## 📊 Monitoring and Maintenance

### App Platform Monitoring
- Built-in metrics dashboard
- Log aggregation
- Automatic health checks
- Auto-scaling capabilities

### Custom Monitoring Setup
```bash
# Install monitoring tools on Droplet
docker run -d --name=prometheus \
  -p 9090:9090 \
  prom/prometheus

docker run -d --name=grafana \
  -p 3000:3000 \
  grafana/grafana
```

### Backup Strategies

#### Database Backups
```bash
# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Automated daily backups (add to crontab)
0 2 * * * pg_dump $DATABASE_URL > /backups/bulletdrop_$(date +\%Y\%m\%d).sql
```

#### Spaces Backups
- DigitalOcean Spaces has built-in versioning
- Enable lifecycle policies for cost optimization

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check build logs
doctl apps logs your-app-id --type=build

# Common fixes:
# - Ensure all dependencies are in requirements.txt/package.json
# - Check for syntax errors
# - Verify environment variables
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
psql $DATABASE_URL -c "SELECT version();"

# Check firewall rules
# Ensure trusted sources include your app's IP range
```

#### 3. File Upload Issues
```bash
# Test Spaces connectivity
aws s3 ls s3://your-bucket --endpoint-url=https://nyc3.digitaloceanspaces.com

# Check CORS settings in Spaces console
```

#### 4. OAuth Callback Errors
- Verify redirect URIs match exactly
- Check that OAuth apps are in production mode
- Ensure HTTPS is used for production callbacks

### Performance Optimization

#### Database Performance
```sql
-- Create indexes for common queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_uploads_user_id ON uploads(user_id);
CREATE INDEX idx_uploads_created_at ON uploads(created_at);
```

#### CDN Configuration
- Enable CDN for your Spaces bucket
- Configure appropriate cache headers
- Use WebP format for images when possible

### Security Checklist

- [ ] All environment variables are configured as secrets
- [ ] Database uses SSL connections
- [ ] CORS is properly configured
- [ ] File upload size limits are enforced
- [ ] OAuth applications use HTTPS callbacks
- [ ] Regular security updates are applied

---

## 💰 Cost Estimation

### App Platform (Recommended)
- **Basic App:** $12/month (API + Frontend)
- **Database:** $15/month (Basic PostgreSQL)
- **Spaces:** $5/month (250GB storage + CDN)
- **Total:** ~$32/month

### Droplet Deployment
- **Droplet:** $12/month (2GB RAM)
- **Database:** $15/month (Managed PostgreSQL)
- **Spaces:** $5/month (250GB storage)
- **Load Balancer:** $12/month (optional)
- **Total:** ~$32-44/month

### Development
- **Database:** $4/month (Dev cluster)
- **Spaces:** $5/month
- **Total:** ~$9/month

---

## 🆘 Support Resources

- [DigitalOcean Documentation](https://docs.digitalocean.com/)
- [App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [Spaces Documentation](https://docs.digitalocean.com/products/spaces/)
- [Community Support](https://www.digitalocean.com/community/)

For BulletDrop-specific issues, check the project's GitHub issues or create a new issue with deployment logs.

---

## ✅ Post-Deployment Checklist

- [ ] Application is accessible via HTTPS
- [ ] Database migrations completed successfully
- [ ] File uploads are working to Spaces
- [ ] OAuth login flows are functional
- [ ] Domain is properly configured (if using custom domain)
- [ ] Monitoring and alerting are set up
- [ ] Backup strategy is implemented
- [ ] Security headers are configured
- [ ] Performance baseline is established

🎉 **Congratulations!** Your BulletDrop application is now live on DigitalOcean!