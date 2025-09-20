#!/bin/bash

# BulletDrop Deployment Script
# This script automates the deployment process for BulletDrop on DigitalOcean

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."

    # Check if doctl is installed
    if ! command -v doctl &> /dev/null; then
        print_error "doctl is not installed. Please install it first:"
        echo "  snap install doctl"
        echo "  brew install doctl"
        exit 1
    fi

    # Check if git is available
    if ! command -v git &> /dev/null; then
        print_error "git is not installed"
        exit 1
    fi

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi

    print_success "All requirements satisfied"
}

# Function to generate secure secret key
generate_secret_key() {
    if command -v openssl &> /dev/null; then
        openssl rand -hex 32
    else
        # Fallback for systems without openssl
        cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1
    fi
}

# Interactive setup for environment variables
setup_environment() {
    print_status "Setting up environment variables..."

    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Created .env file from template"
    fi

    # Generate secret key if not set
    if ! grep -q "SECRET_KEY=" .env || grep -q "SECRET_KEY=your_super_secret_key" .env; then
        SECRET_KEY=$(generate_secret_key)
        sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        print_success "Generated new SECRET_KEY"
    fi

    print_warning "Please ensure the following environment variables are properly set in .env:"
    echo "  - Database credentials"
    echo "  - OAuth client IDs and secrets"
    echo "  - DigitalOcean Spaces configuration"
    echo ""
    read -p "Press Enter to continue when .env is configured..."
}

# Deploy using App Platform
deploy_app_platform() {
    print_status "Deploying to DigitalOcean App Platform..."

    # Check if app.yaml exists
    if [ ! -f ".do/app.yaml" ]; then
        print_error "App Platform spec file (.do/app.yaml) not found"
        exit 1
    fi

    # Check if user is authenticated with doctl
    if ! doctl account get &> /dev/null; then
        print_warning "Not authenticated with doctl"
        echo "Please run: doctl auth init"
        exit 1
    fi

    # Commit and push any pending changes
    if [ -n "$(git status --porcelain)" ]; then
        print_status "Committing and pushing changes..."
        git add .
        git commit -m "Deploy to DigitalOcean App Platform $(date)"
        git push origin main
    fi

    # Create or update the app
    if doctl apps list | grep -q "bulletdrop"; then
        print_status "Updating existing app..."
        APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | grep bulletdrop | awk '{print $1}')
        doctl apps update $APP_ID --spec .do/app.yaml
    else
        print_status "Creating new app..."
        doctl apps create --spec .do/app.yaml --wait
    fi

    print_success "App Platform deployment initiated"
}

# Deploy using Docker Compose (for Droplet deployment)
deploy_docker() {
    print_status "Preparing Docker deployment..."

    # Build images
    print_status "Building Docker images..."
    docker-compose build

    # Start services
    print_status "Starting services..."
    docker-compose up -d

    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10

    # Run database migrations
    print_status "Running database migrations..."
    docker-compose exec -T backend alembic upgrade head

    print_success "Docker deployment completed"
}

# Create DigitalOcean resources
create_do_resources() {
    print_status "Creating DigitalOcean resources..."

    # Create Spaces bucket (if it doesn't exist)
    BUCKET_NAME=${DO_SPACES_BUCKET:-bulletdrop-uploads}
    if ! doctl spaces bucket ls | grep -q "$BUCKET_NAME"; then
        print_status "Creating Spaces bucket: $BUCKET_NAME"
        doctl spaces bucket create "$BUCKET_NAME" --region nyc3
        print_success "Spaces bucket created"
    else
        print_warning "Spaces bucket $BUCKET_NAME already exists"
    fi

    # Create database cluster
    DB_NAME=${DATABASE_NAME:-bulletdrop-db}
    if ! doctl databases list | grep -q "$DB_NAME"; then
        print_status "Creating database cluster: $DB_NAME"
        doctl databases create "$DB_NAME" --engine pg --version 15 --region nyc3 --size db-s-1vcpu-1gb
        print_success "Database cluster creation initiated (this may take several minutes)"
    else
        print_warning "Database cluster $DB_NAME already exists"
    fi
}

# Validate deployment
validate_deployment() {
    print_status "Validating deployment..."

    if [ "$DEPLOYMENT_TYPE" = "app-platform" ]; then
        # Get app URL
        APP_URL=$(doctl apps list --format Spec.Name,DefaultIngress --no-header | grep bulletdrop | awk '{print $2}')
        if [ -n "$APP_URL" ]; then
            print_status "Testing app at: https://$APP_URL"
            if curl -s -f "https://$APP_URL/health" > /dev/null; then
                print_success "App is responding correctly"
            else
                print_warning "App may not be fully ready yet"
            fi
        fi
    elif [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        # Test local deployment
        if curl -s -f "http://localhost:8000/health" > /dev/null; then
            print_success "Backend is responding correctly"
        else
            print_warning "Backend may not be ready yet"
        fi

        if curl -s -f "http://localhost:8080/health" > /dev/null; then
            print_success "Frontend is responding correctly"
        else
            print_warning "Frontend may not be ready yet"
        fi
    fi
}

# Show deployment information
show_deployment_info() {
    print_success "Deployment completed!"
    echo ""
    echo "📊 Deployment Information:"
    echo "=========================="

    if [ "$DEPLOYMENT_TYPE" = "app-platform" ]; then
        APP_URL=$(doctl apps list --format Spec.Name,DefaultIngress --no-header | grep bulletdrop | awk '{print $2}')
        echo "🌐 App URL: https://$APP_URL"
        echo "📱 App Platform Console: https://cloud.digitalocean.com/apps"
        echo ""
        echo "Next steps:"
        echo "1. Configure your OAuth applications with the callback URL: https://$APP_URL/auth/{provider}/callback"
        echo "2. Set up your custom domain (optional)"
        echo "3. Configure monitoring and alerts"
    elif [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        echo "🌐 Frontend: http://localhost:8080"
        echo "🔧 Backend API: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/docs"
        echo ""
        echo "Next steps:"
        echo "1. Set up reverse proxy with Nginx"
        echo "2. Configure SSL certificate"
        echo "3. Set up monitoring"
    fi

    echo ""
    echo "📖 For detailed information, see docs/DEPLOYMENT.md"
}

# Main script
main() {
    echo "🚀 BulletDrop Deployment Script"
    echo "================================"
    echo ""

    # Parse command line arguments
    DEPLOYMENT_TYPE=${1:-app-platform}

    case $DEPLOYMENT_TYPE in
        app-platform|app)
            print_status "Deploying to DigitalOcean App Platform"
            check_requirements
            setup_environment
            create_do_resources
            deploy_app_platform
            validate_deployment
            show_deployment_info
            ;;
        docker|droplet)
            print_status "Deploying with Docker"
            setup_environment
            deploy_docker
            validate_deployment
            show_deployment_info
            ;;
        resources)
            print_status "Creating DigitalOcean resources only"
            check_requirements
            create_do_resources
            print_success "Resources created"
            ;;
        *)
            print_error "Invalid deployment type: $DEPLOYMENT_TYPE"
            echo "Usage: $0 [app-platform|docker|resources]"
            echo ""
            echo "Options:"
            echo "  app-platform  Deploy to DigitalOcean App Platform (default)"
            echo "  docker        Deploy using Docker Compose"
            echo "  resources     Create DigitalOcean resources only"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"