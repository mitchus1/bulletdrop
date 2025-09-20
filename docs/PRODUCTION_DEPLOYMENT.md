# 🚀 BulletDrop Production Deployment Guide

Complete guide for deploying BulletDrop to production using DigitalOcean servers and real domains.

## 📋 Table of Contents

1. [Infrastructure Overview](#infrastructure-overview)
2. [Domain Setup](#domain-setup)
3. [DigitalOcean Server Setup](#digitalocean-server-setup)
4. [Database Configuration](#database-configuration)
5. [Application Deployment](#application-deployment)
6. [SSL Certificates](#ssl-certificates)
7. [CDN & File Storage](#cdn--file-storage)
8. [Monitoring & Backups](#monitoring--backups)
9. [Security Hardening](#security-hardening)
10. [CI/CD Pipeline](#cicd-pipeline)

---

## 🏗️ Infrastructure Overview

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Setup                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [CloudFlare CDN] ──→ [Load Balancer] ──→ [App Servers]    │
│                              │                              │
│                              ├──→ [Database Cluster]        │
│                              └──→ [File Storage]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Cost Estimation (Monthly)

| Component | DigitalOcean Droplet | Monthly Cost |
|-----------|---------------------|--------------|
| **App Server** | 4GB RAM, 2 vCPUs, 80GB SSD | $24/month |
| **Database** | Managed PostgreSQL 1GB | $15/month |
| **Load Balancer** | DigitalOcean LB | $12/month |
| **Spaces (Storage)** | 250GB + CDN | $5/month |
| **Domain** | .com domain | $12/year |
| **Backups** | Automated backups | $5/month |
| **Total** | | **~$61/month** |

---

## 🌐 Domain Setup

### 1. Purchase Domains

**Main Domain:**
- `bulletdrop.com` (or your preferred domain)
- Purchase from Namecheap, Google Domains, or directly through DigitalOcean

**Subdomain Strategy:**
```
bulletdrop.com          → Main website/app
api.bulletdrop.com      → Backend API
img.bulletdrop.com      → Image uploads
shots.bulletdrop.com    → Screenshots
cdn.bulletdrop.com      → CDN/assets
media.bulletdrop.com    → Large media files
```

### 2. DNS Configuration

**Set up these DNS records:**

```bash
# A Records (point to your server IP)
@                    A      YOUR_SERVER_IP
www                  A      YOUR_SERVER_IP
api                  A      YOUR_SERVER_IP
img                  A      YOUR_SERVER_IP
shots                A      YOUR_SERVER_IP
cdn                  A      YOUR_SERVER_IP
media                A      YOUR_SERVER_IP

# CNAME for www (alternative to A record)
www                  CNAME  bulletdrop.com

# MX Records (if you want email)
@                    MX     mail.bulletdrop.com
```

### 3. CloudFlare Setup (Recommended)

**Benefits:**
- Free SSL certificates
- DDoS protection
- Global CDN
- Analytics
- Page rules for optimization

**Steps:**
1. Sign up for CloudFlare (free plan sufficient)
2. Add your domain
3. Update nameservers at your domain registrar
4. Enable "Full (strict)" SSL mode
5. Set up page rules for static files

---

## 🖥️ DigitalOcean Server Setup

### 1. Create Droplets

**Application Server:**
```bash
# Create main app server
doctl compute droplet create bulletdrop-app-01 \
    --region nyc3 \
    --image ubuntu-22-04-x64 \
    --size s-2vcpu-4gb \
    --ssh-keys YOUR_SSH_KEY_ID \
    --enable-monitoring \
    --enable-backups \
    --tag-names production,app-server
```

**Database (Alternative to Managed):**
```bash
# Create database server (if not using managed DB)
doctl compute droplet create bulletdrop-db-01 \
    --region nyc3 \
    --image ubuntu-22-04-x64 \
    --size s-2vcpu-2gb \
    --ssh-keys YOUR_SSH_KEY_ID \
    --enable-monitoring \
    --enable-backups \
    --tag-names production,database
```

### 2. Initial Server Configuration

**Connect and Update:**
```bash
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y nginx postgresql-client python3.11 python3.11-venv \
    python3-pip nodejs npm certbot python3-certbot-nginx \
    htop curl wget git ufw fail2ban

# Create application user
useradd -m -s /bin/bash bulletdrop
usermod -aG sudo bulletdrop
```

### 3. Firewall Configuration

```bash
# Configure UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw enable

# Check status
ufw status
```

---

## 🗄️ Database Configuration

### Option 1: Managed PostgreSQL (Recommended)

**Create Database Cluster:**
```bash
# Using doctl
doctl databases create bulletdrop-db \
    --engine postgres \
    --region nyc3 \
    --size db-s-1vcpu-1gb \
    --num-nodes 1

# Get connection details
doctl databases connection bulletdrop-db
```

**Benefits:**
- Automated backups
- High availability
- Security patches
- Monitoring included

### Option 2: Self-Managed PostgreSQL

**Install and Configure:**
```bash
# Install PostgreSQL
apt install -y postgresql postgresql-contrib

# Switch to postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE bulletdrop;
CREATE USER bulletdrop WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE bulletdrop TO bulletdrop;
\q

# Configure PostgreSQL
echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/14/main/pg_hba.conf
echo "listen_addresses = '*'" >> /etc/postgresql/14/main/postgresql.conf

# Restart PostgreSQL
systemctl restart postgresql
systemctl enable postgresql
```

### 3. Database Security

```bash
# Backup configuration
pg_dump bulletdrop > /backup/bulletdrop_$(date +%Y%m%d).sql

# Set up automated backups
echo "0 2 * * * postgres pg_dump bulletdrop > /backup/bulletdrop_\$(date +\%Y\%m\%d).sql" | crontab -
```

---

## 📦 Application Deployment

### 1. Deploy Backend

**Application Setup:**
```bash
# Switch to app user
sudo -u bulletdrop -i

# Clone repository
cd /home/bulletdrop
git clone https://github.com/yourusername/bulletdrop.git
cd bulletdrop

# Set up Python environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Install additional production packages
pip install gunicorn psycopg2-binary
```

**Environment Configuration:**
```bash
# Create production environment file
cat > /home/bulletdrop/bulletdrop/backend/.env << EOF
# Database
DATABASE_URL=postgresql://bulletdrop:your_password@localhost/bulletdrop

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_HOSTS=https://bulletdrop.com,https://www.bulletdrop.com,https://api.bulletdrop.com

# File Upload
UPLOAD_DIR=/var/www/bulletdrop/uploads
MAX_FILE_SIZE=52428800  # 50MB
ALLOWED_EXTENSIONS=.jpg,.jpeg,.png,.gif,.webp,.pdf,.txt,.md,.mp4,.webm

# Production settings
ENVIRONMENT=production
DEBUG=False
EOF
```

**Create Upload Directory:**
```bash
# Create upload directories
sudo mkdir -p /var/www/bulletdrop/uploads/{images,documents,other}
sudo chown -R bulletdrop:bulletdrop /var/www/bulletdrop
sudo chmod -R 755 /var/www/bulletdrop
```

**Run Database Migrations:**
```bash
cd /home/bulletdrop/bulletdrop/backend
source ../venv/bin/activate
alembic upgrade head

# Seed initial domains
python -c "
import requests
response = requests.post('http://localhost:8000/api/domains/seed')
print(response.json())
"
```

### 2. Deploy Frontend

**Build Frontend:**
```bash
cd /home/bulletdrop/bulletdrop/frontend

# Install dependencies
npm install

# Update API endpoint for production
sed -i 's/http:\/\/localhost:8000/https:\/\/api.bulletdrop.com/g' src/services/api.ts

# Build for production
npm run build

# Copy to web directory
sudo mkdir -p /var/www/bulletdrop/frontend
sudo cp -r dist/* /var/www/bulletdrop/frontend/
sudo chown -R www-data:www-data /var/www/bulletdrop/frontend
```

### 3. Systemd Services

**Backend Service:**
```bash
# Create systemd service for backend
sudo cat > /etc/systemd/system/bulletdrop-api.service << EOF
[Unit]
Description=BulletDrop API
After=network.target

[Service]
Type=exec
User=bulletdrop
Group=bulletdrop
WorkingDirectory=/home/bulletdrop/bulletdrop/backend
Environment=PATH=/home/bulletdrop/bulletdrop/venv/bin
ExecStart=/home/bulletdrop/bulletdrop/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable bulletdrop-api
sudo systemctl start bulletdrop-api
sudo systemctl status bulletdrop-api
```

**Monitor Logs:**
```bash
# View service logs
sudo journalctl -u bulletdrop-api -f
```

---

## 🔐 SSL Certificates

### Option 1: Let's Encrypt (Free)

**Install Certbot:**
```bash
# Install certbot for nginx
sudo apt install certbot python3-certbot-nginx

# Obtain certificates for all domains
sudo certbot --nginx -d bulletdrop.com -d www.bulletdrop.com \
    -d api.bulletdrop.com -d img.bulletdrop.com \
    -d shots.bulletdrop.com -d cdn.bulletdrop.com \
    -d media.bulletdrop.com

# Set up auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Option 2: CloudFlare SSL (Easier)

**Benefits:**
- Automatic SSL for all subdomains
- No server configuration needed
- Global CDN included

**Setup:**
1. Enable "Full (strict)" SSL in CloudFlare
2. Create Origin Certificate in CloudFlare
3. Install origin certificate on server

---

## 🌐 Nginx Configuration

### Main Configuration

```bash
# Create main nginx config
sudo cat > /etc/nginx/sites-available/bulletdrop << 'EOF'
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

# Main website
server {
    listen 80;
    listen [::]:80;
    server_name bulletdrop.com www.bulletdrop.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name bulletdrop.com www.bulletdrop.com;

    # SSL configuration (if using Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/bulletdrop.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bulletdrop.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        root /var/www/bulletdrop/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}

# API server
server {
    listen 80;
    listen [::]:80;
    server_name api.bulletdrop.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.bulletdrop.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/bulletdrop.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bulletdrop.com/privkey.pem;

    # API endpoints
    location / {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for uploads
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Upload endpoints with stricter rate limiting
    location /api/uploads/ {
        limit_req zone=upload burst=5 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Large file upload settings
        client_max_body_size 100M;
        proxy_read_timeout 600;
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
    }
}

# File serving subdomains
server {
    listen 80;
    listen [::]:80;
    server_name img.bulletdrop.com shots.bulletdrop.com cdn.bulletdrop.com media.bulletdrop.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name img.bulletdrop.com shots.bulletdrop.com cdn.bulletdrop.com media.bulletdrop.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/bulletdrop.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bulletdrop.com/privkey.pem;

    # Serve uploaded files
    location /static/ {
        alias /var/www/bulletdrop/uploads/;

        # Cache uploaded files
        expires 1y;
        add_header Cache-Control "public, immutable";

        # Security headers for images
        add_header X-Content-Type-Options "nosniff";
        add_header X-Frame-Options "SAMEORIGIN";

        # Enable CORS for images
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS";
    }

    # Redirect root to main site
    location = / {
        return 301 https://bulletdrop.com;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/bulletdrop /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
```

---

## 💾 CDN & File Storage

### Option 1: DigitalOcean Spaces

**Create Spaces:**
```bash
# Create space for file storage
doctl compute cdn create bulletdrop-cdn --origin bulletdrop-files.nyc3.digitaloceanspaces.com
```

**Configure Backend for Spaces:**
```python
# Add to requirements.txt
boto3==1.26.137

# Update backend config for cloud storage
SPACES_KEY=your_spaces_key
SPACES_SECRET=your_spaces_secret
SPACES_BUCKET=bulletdrop-files
SPACES_REGION=nyc3
SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
CDN_ENDPOINT=https://bulletdrop-cdn.nyc3.cdn.digitaloceanspaces.com
```

### Option 2: Local Storage with CloudFlare CDN

**Advantages:**
- Lower cost for small to medium usage
- Simpler setup
- Full control over files

**CloudFlare Configuration:**
1. Enable CloudFlare for your domain
2. Set up Page Rules for static files:
   - `img.bulletdrop.com/static/*` → Cache Everything, Edge TTL 1 month
3. Enable "Automatic Image Optimization"

---

## 📊 Monitoring & Backups

### 1. System Monitoring

**Install Monitoring Tools:**
```bash
# Install monitoring stack
sudo apt install prometheus node-exporter grafana

# Configure prometheus
sudo cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'bulletdrop-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
EOF

# Start services
sudo systemctl enable prometheus grafana-server node-exporter
sudo systemctl start prometheus grafana-server node-exporter
```

### 2. Log Management

**Configure Log Rotation:**
```bash
# Create logrotate config
sudo cat > /etc/logrotate.d/bulletdrop << EOF
/var/log/bulletdrop/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 bulletdrop bulletdrop
    postrotate
        systemctl reload bulletdrop-api
    endscript
}
EOF
```

### 3. Automated Backups

**Database Backups:**
```bash
# Create backup script
sudo cat > /usr/local/bin/backup-bulletdrop.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/bulletdrop"
S3_BUCKET="bulletdrop-backups"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U bulletdrop bulletdrop > $BACKUP_DIR/db_$DATE.sql

# Upload directory backup
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /var/www/bulletdrop/uploads/

# Upload to DigitalOcean Spaces
s3cmd put $BACKUP_DIR/db_$DATE.sql s3://$S3_BUCKET/database/
s3cmd put $BACKUP_DIR/uploads_$DATE.tar.gz s3://$S3_BUCKET/uploads/

# Clean local backups older than 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/backup-bulletdrop.sh

# Schedule daily backups
echo "0 2 * * * /usr/local/bin/backup-bulletdrop.sh" | sudo crontab -
```

---

## 🔒 Security Hardening

### 1. Server Security

**SSH Hardening:**
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Recommended settings:
# Port 2222                    # Change default port
# PermitRootLogin no          # Disable root login
# PasswordAuthentication no   # Use key-based auth only
# AllowUsers bulletdrop       # Restrict users

sudo systemctl restart ssh
```

**Fail2Ban Configuration:**
```bash
# Configure fail2ban for nginx
sudo cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true

[nginx-noproxy]
enabled = true
EOF

sudo systemctl restart fail2ban
```

### 2. Application Security

**Environment Variables Security:**
```bash
# Set restrictive permissions on .env file
chmod 600 /home/bulletdrop/bulletdrop/backend/.env
chown bulletdrop:bulletdrop /home/bulletdrop/bulletdrop/backend/.env
```

**Rate Limiting:**
- Configured in Nginx (see above)
- API-level rate limiting in FastAPI
- Upload limits per user

### 3. Database Security

**PostgreSQL Hardening:**
```bash
# Restrict network access
echo "host all all 127.0.0.1/32 md5" > /etc/postgresql/14/main/pg_hba.conf
echo "local all all md5" >> /etc/postgresql/14/main/pg_hba.conf

# Disable external connections
echo "listen_addresses = 'localhost'" >> /etc/postgresql/14/main/postgresql.conf

sudo systemctl restart postgresql
```

---

## 🔄 CI/CD Pipeline

### 1. GitHub Actions Setup

**Create `.github/workflows/deploy.yml`:**
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Build Frontend
      run: |
        cd frontend
        npm install
        npm run build

    - name: Deploy to Server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.PRIVATE_KEY }}
        script: |
          cd /home/bulletdrop/bulletdrop
          git pull origin main

          # Update backend
          source venv/bin/activate
          cd backend
          pip install -r requirements.txt
          alembic upgrade head

          # Update frontend
          cd ../frontend
          npm install
          npm run build
          sudo cp -r dist/* /var/www/bulletdrop/frontend/

          # Restart services
          sudo systemctl restart bulletdrop-api
          sudo systemctl reload nginx
```

### 2. Deployment Script

**Create Local Deployment Script:**
```bash
#!/bin/bash
# deploy.sh

set -e

SERVER="bulletdrop@your-server-ip"
APP_DIR="/home/bulletdrop/bulletdrop"

echo "🚀 Deploying BulletDrop to production..."

# Build frontend locally
echo "📦 Building frontend..."
cd frontend
npm install
npm run build

# Upload to server
echo "📤 Uploading files..."
rsync -avz --delete dist/ $SERVER:/var/www/bulletdrop/frontend/

# Update backend
echo "🔧 Updating backend..."
ssh $SERVER << 'EOF'
cd /home/bulletdrop/bulletdrop
git pull origin main

source venv/bin/activate
cd backend
pip install -r requirements.txt
alembic upgrade head

sudo systemctl restart bulletdrop-api
sudo systemctl reload nginx
EOF

echo "✅ Deployment complete!"
```

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Domain purchased and DNS configured
- [ ] DigitalOcean account set up
- [ ] SSH keys added to DigitalOcean
- [ ] CloudFlare account configured (optional)

### Server Setup

- [ ] Droplet created and configured
- [ ] Firewall rules configured
- [ ] SSL certificates installed
- [ ] Database set up and secured
- [ ] Nginx configured and tested

### Application Deployment

- [ ] Backend deployed and running
- [ ] Frontend built and served
- [ ] Database migrations run
- [ ] Environment variables configured
- [ ] File upload directories created

### Security & Monitoring

- [ ] SSH hardened
- [ ] Fail2Ban configured
- [ ] Backups scheduled
- [ ] Monitoring tools installed
- [ ] Log rotation configured

### Testing

- [ ] Website loads correctly
- [ ] API endpoints respond
- [ ] File uploads work
- [ ] ShareX/Flameshot integration tested
- [ ] SSL certificates valid
- [ ] Performance acceptable

### Go Live

- [ ] DNS propagated
- [ ] All domains working
- [ ] CDN configured
- [ ] Monitoring alerts set up
- [ ] Team notified

---

## 🎯 Production URLs

After deployment, your BulletDrop instance will be available at:

- **Main Site**: https://bulletdrop.com
- **API**: https://api.bulletdrop.com
- **File Uploads**: https://img.bulletdrop.com/static/...
- **Screenshots**: https://shots.bulletdrop.com/static/...
- **API Docs**: https://api.bulletdrop.com/docs

### ShareX Configuration Update

Update ShareX config for production:
```json
{
  "RequestURL": "https://api.bulletdrop.com/api/uploads/sharex",
  "URL": "$json:url$"
}
```

---

## 🔧 Maintenance

### Regular Tasks

**Weekly:**
- Check server resource usage
- Review logs for errors
- Test backup restoration
- Update system packages

**Monthly:**
- Rotate SSL certificates (automatic with Let's Encrypt)
- Review user analytics
- Clean up old uploaded files (if needed)
- Performance optimization

**Quarterly:**
- Security audit
- Dependency updates
- Disaster recovery testing
- Cost optimization review

---

## 💰 Cost Optimization

### Scaling Strategy

**Start Small:**
- 1 app server ($24/month)
- Managed database ($15/month)
- Load balancer when needed

**Scale Up:**
- Add more app servers behind load balancer
- Upgrade database as needed
- Implement caching (Redis)
- Consider separate file storage servers

### Monitoring Costs

**DigitalOcean Monitoring:**
- Set up billing alerts
- Monitor bandwidth usage
- Optimize image storage
- Use CloudFlare for CDN to reduce bandwidth costs

---

This production deployment plan will give you a robust, scalable, and secure BulletDrop installation ready for real-world usage! 🚀