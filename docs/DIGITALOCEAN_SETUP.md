# ⚙️ DigitalOcean Setup Guide for BulletDrop

This guide walks you through setting up all the necessary DigitalOcean services for BulletDrop deployment.

## 📋 Quick Setup Checklist

- [ ] DigitalOcean account created and verified
- [ ] Payment method added
- [ ] Domain name configured (optional)
- [ ] OAuth applications set up
- [ ] DigitalOcean CLI installed and configured

---

## 🏁 Getting Started

### 1. Create DigitalOcean Account

1. Sign up at [DigitalOcean](https://digitalocean.com)
2. Verify your email address
3. Add a payment method
4. (Optional) Apply a referral code for $200 credit

### 2. Install DigitalOcean CLI (doctl)

**On macOS:**
```bash
brew install doctl
```

**On Ubuntu/Debian:**
```bash
sudo snap install doctl
```

**On Windows:**
Download from [GitHub releases](https://github.com/digitalocean/doctl/releases)

### 3. Authenticate CLI

```bash
# Get your API token from: https://cloud.digitalocean.com/account/api/tokens
doctl auth init

# Verify authentication
doctl account get
```

---

## 🗄️ Database Setup

### Create PostgreSQL Database

**Using Web Console:**
1. Go to [Databases](https://cloud.digitalocean.com/databases)
2. Click "Create Database Cluster"
3. Choose PostgreSQL version 15
4. Select plan:
   - **Development:** Basic plan ($4/month)
   - **Production:** Professional plan ($15/month)
5. Choose region (preferably same as your app)
6. Name: `bulletdrop-db`

**Using CLI:**
```bash
# Development database
doctl databases create bulletdrop-db \
  --engine pg \
  --version 15 \
  --region nyc3 \
  --size db-s-1vcpu-1gb

# Production database
doctl databases create bulletdrop-db \
  --engine pg \
  --version 15 \
  --region nyc3 \
  --size db-s-2vcpu-2gb
```

### Configure Database

```bash
# Get database connection info
doctl databases connection bulletdrop-db

# Create database user (optional)
doctl databases user create bulletdrop-db bulletdrop-user

# Get connection string
doctl databases connection bulletdrop-db --format DSN
```

**Important Security Notes:**
- Database comes with SSL enabled by default
- Only trusted sources can connect
- Add your app's IP ranges to trusted sources

---

## 📁 Spaces (Object Storage) Setup

### Create Spaces Bucket

**Using Web Console:**
1. Go to [Spaces](https://cloud.digitalocean.com/spaces)
2. Click "Create Space"
3. Configuration:
   - **Name:** `bulletdrop-uploads` (must be unique globally)
   - **Region:** NYC3 (or same as your app)
   - **CDN:** Enable for better performance
   - **File Listing:** Disable for security

**Using CLI:**
```bash
doctl spaces bucket create bulletdrop-uploads --region nyc3
```

### Generate Spaces Access Keys

**Using Web Console:**
1. Go to API → [Spaces Keys](https://cloud.digitalocean.com/account/api/spaces)
2. Click "Generate New Key"
3. Name: `bulletdrop-app`
4. Save both Access Key and Secret Key securely
YWKAxOpkuddwGZZ20DpReizGafdguBSULkQbgyszwKY
**Using CLI:**
```bash
# List existing keys
doctl spaces key list

# Note: Cannot create keys via CLI, must use web console
```

### Configure CORS for Spaces

Create a CORS configuration file:

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "POST", "PUT", "DELETE"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

Apply CORS configuration:
```bash
# Using AWS CLI (compatible with Spaces)
aws s3api put-bucket-cors \
  --bucket bulletdrop-uploads \
  --cors-configuration file://cors.json \
  --endpoint-url https://nyc3.digitaloceanspaces.com
```

---

## 🌐 App Platform Setup

### Create App Platform App

**Method 1: Using App Spec File (Recommended)**

1. Ensure your repository has `.do/app.yaml`
2. Update GitHub repository URL in the spec
3. Deploy:

```bash
# Create new app
doctl apps create --spec .do/app.yaml

# Or update existing app
doctl apps update <app-id> --spec .do/app.yaml
```

**Method 2: Using Web Console**

1. Go to [App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Choose GitHub source
4. Select repository and branch
5. Configure build and run commands:

**Backend Service:**
- Build Command: (leave empty)
- Run Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- HTTP Port: 8000

**Frontend Service:**
- Build Command: `npm run build`
- Run Command: `serve -s dist -l $PORT`
- HTTP Port: 8080

### Configure Environment Variables

**Required Environment Variables:**

```bash
# Security
SECRET_KEY=<32-character-secret-key>

# Database (auto-configured if using managed database)
DATABASE_URL=${bulletdrop-db.DATABASE_URL}

# OAuth
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
DISCORD_CLIENT_ID=<your-discord-client-id>
DISCORD_CLIENT_SECRET=<your-discord-client-secret>
GITHUB_CLIENT_ID=<your-github-client-id>
GITHUB_CLIENT_SECRET=<your-github-client-secret>

# DigitalOcean Spaces
DO_SPACES_KEY=<your-spaces-access-key>
DO_SPACES_SECRET=<your-spaces-secret-key>
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
DO_SPACES_BUCKET=bulletdrop-uploads
DO_SPACES_REGION=nyc3

# App Configuration
ENVIRONMENT=production
CORS_ORIGINS=${_self.PROTOCOL}://${_self.PUBLIC_URL}
```

**Using CLI to set environment variables:**
```bash
# Get app ID
doctl apps list

# Set environment variables
doctl apps update <app-id> --spec .do/app.yaml
```

---

## 🔐 OAuth Setup

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API:
   - Go to APIs & Services → Library
   - Search for "Google+ API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → OAuth 2.0 Client ID
   - Application type: Web application
   - Authorized redirect URIs:
     - `https://your-app-name.ondigitalocean.app/auth/google/callback`
     - `http://localhost:8000/auth/google/callback` (for development)

### Discord OAuth Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name your application: "BulletDrop"
4. Go to OAuth2 → General:
   - Copy Client ID and Client Secret
   - Add redirect URI: `https://your-app-name.ondigitalocean.app/auth/discord/callback`

### GitHub OAuth Setup

1. Go to GitHub Settings → Developer settings → [OAuth Apps](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in details:
   - Application name: "BulletDrop"
   - Homepage URL: `https://your-app-name.ondigitalocean.app`
   - Authorization callback URL: `https://your-app-name.ondigitalocean.app/auth/github/callback`

---

## 🌍 Domain Configuration (Optional)

### Add Custom Domain

**Using Web Console:**
1. Go to your App Platform app
2. Settings → Domains
3. Click "Add Domain"
4. Enter your domain name
5. Choose to manage DNS through DigitalOcean or update your current DNS

**DNS Configuration:**
If managing DNS elsewhere, add these records:
```
Type: CNAME
Name: @
Value: your-app-name.ondigitalocean.app

Type: CNAME
Name: www
Value: your-app-name.ondigitalocean.app
```

### SSL Certificate

DigitalOcean App Platform automatically provisions and manages Let's Encrypt SSL certificates for your custom domains.

---

## 📊 Monitoring Setup

### Enable Monitoring

**App Platform Built-in Monitoring:**
- Automatic metrics collection
- Log aggregation
- Health checks
- Auto-scaling based on metrics

**Additional Monitoring:**
```bash
# Create monitoring Droplet (optional)
doctl compute droplet create monitoring \
  --region nyc3 \
  --image ubuntu-22-04-x64 \
  --size s-1vcpu-1gb \
  --ssh-keys <your-ssh-key-id>
```

### Set Up Alerts

1. Go to Monitoring → Alerts
2. Create alerts for:
   - High CPU usage (>80%)
   - High memory usage (>90%)
   - Response time (>2 seconds)
   - Error rate (>5%)

---

## 💰 Cost Optimization

### Development Environment
- **Database:** Basic plan ($4/month)
- **App Platform:** Basic tier ($5-12/month)
- **Spaces:** $5/month (250GB included)
- **Total:** ~$14-21/month

### Production Environment
- **Database:** Professional plan ($15/month)
- **App Platform:** Professional tier ($12-25/month)
- **Spaces:** $5/month + bandwidth
- **CDN:** Included with Spaces
- **Total:** ~$32-45/month

### Cost-Saving Tips

1. **Right-size your resources:** Start small and scale up
2. **Use Spaces lifecycle policies:** Archive old files
3. **Enable CDN:** Reduce bandwidth costs
4. **Monitor usage:** Set up billing alerts
5. **Development/staging environments:** Use smaller instances

---

## 🔒 Security Best Practices

### Database Security
- ✅ SSL/TLS enabled by default
- ✅ Configure trusted sources (restrict access by IP)
- ✅ Use strong passwords
- ✅ Regular automated backups
- ✅ Enable connection pooling

### Spaces Security
- ✅ Use IAM policies for fine-grained access control
- ✅ Enable versioning for important data
- ✅ Configure appropriate CORS settings
- ✅ Use signed URLs for sensitive content
- ✅ Regularly rotate access keys

### App Platform Security
- ✅ Store secrets as encrypted environment variables
- ✅ Use HTTPS for all communication
- ✅ Enable security headers
- ✅ Regular dependency updates
- ✅ Monitor for vulnerabilities

### Network Security
- ✅ Use VPC for network isolation
- ✅ Configure firewalls appropriately
- ✅ Enable DDoS protection
- ✅ Use load balancers for high availability

---

## 🚀 Deployment Automation

### CI/CD Pipeline

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to DigitalOcean App Platform

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Install doctl
      uses: digitalocean/action-doctl@v2
      with:
        token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

    - name: Deploy to App Platform
      run: doctl apps update ${{ secrets.APP_ID }} --spec .do/app.yaml
```

### Infrastructure as Code

Use Terraform for infrastructure management:

```hcl
# main.tf
resource "digitalocean_database_cluster" "bulletdrop_db" {
  name       = "bulletdrop-db"
  engine     = "pg"
  version    = "15"
  size       = "db-s-1vcpu-1gb"
  region     = "nyc3"
  node_count = 1
}

resource "digitalocean_spaces_bucket" "bulletdrop_uploads" {
  name   = "bulletdrop-uploads"
  region = "nyc3"
}
```

---

## 🆘 Troubleshooting

### Common Issues

**1. App Platform Build Failures:**
```bash
# Check build logs
doctl apps logs <app-id> --type=build --follow

# Common solutions:
# - Verify all dependencies are listed
# - Check for syntax errors
# - Ensure environment variables are set
```

**2. Database Connection Issues:**
```bash
# Test database connectivity
doctl databases connection <db-id>

# Check trusted sources
doctl databases firewalls list <db-id>
```

**3. Spaces Access Issues:**
```bash
# Test Spaces connectivity
aws s3 ls s3://bulletdrop-uploads \
  --endpoint-url=https://nyc3.digitaloceanspaces.com
```

### Support Resources

- [DigitalOcean Documentation](https://docs.digitalocean.com/)
- [Community Q&A](https://www.digitalocean.com/community/questions)
- [Support Tickets](https://cloud.digitalocean.com/support/tickets) (for paid accounts)
- [Status Page](https://status.digitalocean.com/)

---

## ✅ Final Checklist

Before going live:

- [ ] All services are created and configured
- [ ] Environment variables are set correctly
- [ ] OAuth applications are configured with correct callback URLs
- [ ] Custom domain is configured (if applicable)
- [ ] SSL certificates are active
- [ ] Database migrations have been run
- [ ] File uploads are working correctly
- [ ] Monitoring and alerts are configured
- [ ] Backup strategy is implemented
- [ ] Security best practices are followed

🎉 **You're ready to deploy BulletDrop on DigitalOcean!**

Use the automated deployment script:
```bash
./scripts/deploy.sh app-platform
```

Or follow the detailed deployment guide in `docs/DEPLOYMENT.md`.