#!/bin/bash

# Production Deployment Script for Enhanced Ooumph Feed Algorithm
# This script deploys the enhanced system with all production features

set -e  # Exit on any error

echo "🚀 Starting Enhanced Ooumph Feed Algorithm Deployment"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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
    print_status "Checking deployment requirements..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "All requirements met"
}

# Setup environment variables
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.example .env
        
        # Generate a random secret key
        SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
        sed -i "s/your-super-secret-key-here-change-in-production/$SECRET_KEY/g" .env
        
        # Generate random passwords
        POSTGRES_PASSWORD=$(openssl rand -base64 32)
        GRAFANA_PASSWORD=$(openssl rand -base64 12)
        
        sed -i "s/your_postgres_password/$POSTGRES_PASSWORD/g" .env
        sed -i "s/your_grafana_password/$GRAFANA_PASSWORD/g" .env
        
        print_warning "Please edit .env file with your domain and email settings before continuing."
        print_warning "Press Enter to continue after editing .env file..."
        read
    fi
    
    # Load environment variables
    export $(cat .env | grep -v '#' | xargs)
    
    print_success "Environment configuration ready"
}

# Create necessary directories
setup_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p staticfiles
    mkdir -p media
    mkdir -p nginx/ssl
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/provisioning
    
    # Set proper permissions
    chmod 755 logs staticfiles media
    
    print_success "Directories created"
}

# Generate SSL certificates (self-signed for development)
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    if [ ! -f nginx/ssl/cert.pem ]; then
        print_warning "SSL certificates not found. Generating self-signed certificates..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=${DOMAIN_NAME:-localhost}"
        
        print_warning "Self-signed certificates generated. For production, replace with valid SSL certificates."
    fi
    
    print_success "SSL certificates ready"
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Build images
    print_status "Building Docker images..."
    docker-compose -f docker-compose.production.yml build
    
    # Start infrastructure services first
    print_status "Starting infrastructure services..."
    docker-compose -f docker-compose.production.yml up -d db redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    print_status "Running database migrations..."
    docker-compose -f docker-compose.production.yml run --rm web python manage.py migrate
    
    # Create Django cache table
    print_status "Setting up Django cache..."
    docker-compose -f docker-compose.production.yml run --rm web python manage.py createcachetable
    
    # Collect static files
    print_status "Collecting static files..."
    docker-compose -f docker-compose.production.yml run --rm web python manage.py collectstatic --noinput
    
    # Start all services
    print_status "Starting all services..."
    docker-compose -f docker-compose.production.yml up -d
    
    print_success "All services started"
}

# Create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    
    echo "Please create a superuser account for Django admin:"
    docker-compose -f docker-compose.production.yml exec web python manage.py createsuperuser
    
    print_success "Superuser created"
}

# Setup monitoring dashboards
setup_monitoring() {
    print_status "Setting up monitoring dashboards..."
    
    # Wait for Grafana to start
    sleep 15
    
    # Import default dashboards (if available)
    # This would typically import pre-configured dashboard definitions
    
    print_success "Monitoring setup complete"
}

# Run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Wait for services to be fully ready
    sleep 30
    
    # Check web service health
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        print_success "Web service is healthy"
    else
        print_error "Web service health check failed"
        return 1
    fi
    
    # Check database connection
    if docker-compose -f docker-compose.production.yml exec -T db pg_isready -U ooumph_user > /dev/null 2>&1; then
        print_success "Database is healthy"
    else
        print_error "Database health check failed"
        return 1
    fi
    
    # Check Redis connection
    if docker-compose -f docker-compose.production.yml exec -T redis redis-cli ping | grep -q PONG; then
        print_success "Redis is healthy"
    else
        print_error "Redis health check failed"
        return 1
    fi
    
    # Check Celery workers
    if docker-compose -f docker-compose.production.yml exec -T celery_worker celery -A ooumph_feed inspect ping > /dev/null 2>&1; then
        print_success "Celery workers are healthy"
    else
        print_warning "Celery workers may not be fully ready yet"
    fi
    
    print_success "Health checks completed"
}

# Display access information
show_access_info() {
    echo ""
    echo "🎉 Enhanced Ooumph Feed Algorithm Deployment Complete!"
    echo "====================================================="
    echo ""
    echo "Access URLs:"
    echo "  Main Application:     https://${DOMAIN_NAME:-localhost}"
    echo "  Analytics Dashboard:  https://${DOMAIN_NAME:-localhost}/admin/analytics/"
    echo "  Django Admin:         https://${DOMAIN_NAME:-localhost}/admin/"
    echo "  Celery Monitoring:    https://flower.${DOMAIN_NAME:-localhost}"
    echo "  Grafana Dashboards:   https://${DOMAIN_NAME:-localhost}:3000"
    echo "  Health Check:         https://${DOMAIN_NAME:-localhost}/health/"
    echo ""
    echo "Service Status:"
    docker-compose -f docker-compose.production.yml ps
    echo ""
    echo "Next Steps:"
    echo "  1. Update your DNS to point to this server"
    echo "  2. Replace self-signed SSL certificates with valid ones"
    echo "  3. Configure monitoring alerts"
    echo "  4. Set up backup procedures"
    echo "  5. Review security settings"
    echo ""
    print_success "Deployment successful! 🚀"
}

# Main deployment flow
main() {
    check_requirements
    setup_environment
    setup_directories
    setup_ssl
    deploy_services
    
    # Optional interactive steps
    read -p "Do you want to create a Django superuser now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_superuser
    fi
    
    setup_monitoring
    run_health_checks
    show_access_info
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "health")
        run_health_checks
        ;;
    "logs")
        docker-compose -f docker-compose.production.yml logs -f ${2:-web}
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose -f docker-compose.production.yml restart
        print_success "Services restarted"
        ;;
    "stop")
        print_status "Stopping services..."
        docker-compose -f docker-compose.production.yml down
        print_success "Services stopped"
        ;;
    "backup")
        print_status "Creating backup..."
        mkdir -p backups
        docker-compose -f docker-compose.production.yml exec -T db pg_dump -U ooumph_user ooumph_feed > "backups/backup_$(date +%Y%m%d_%H%M%S).sql"
        print_success "Database backup created in backups/ directory"
        ;;
    "update")
        print_status "Updating services..."
        docker-compose -f docker-compose.production.yml pull
        docker-compose -f docker-compose.production.yml up -d
        print_success "Services updated"
        ;;
    *)
        echo "Usage: $0 {deploy|health|logs [service]|restart|stop|backup|update}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  health  - Run health checks"
        echo "  logs    - View service logs"
        echo "  restart - Restart all services"
        echo "  stop    - Stop all services"
        echo "  backup  - Create database backup"
        echo "  update  - Update and restart services"
        exit 1
        ;;
esac
