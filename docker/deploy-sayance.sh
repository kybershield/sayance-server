#!/bin/bash

# Sayance Full Stack Deployment Script
# This script deploys Sayance with Element Call integration

set -e

echo "🚀 Deploying Sayance with Element Call Integration"
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

# Check if docker and docker-compose are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "All dependencies are available."
}

# Setup SSL certificates
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    cd element-call-backend
    
    if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
        print_status "Generating SSL certificates..."
        chmod +x setup-tls.sh
        ./setup-tls.sh
        print_success "SSL certificates generated."
    else
        print_warning "SSL certificates already exist. Skipping generation."
    fi
    
    cd ..
}

# Build Sayance Web
build_sayance_web() {
    print_status "Building Sayance Web application..."
    
    cd ../../sayance-web
    
    # Install dependencies
    print_status "Installing dependencies..."
    if command -v yarn &> /dev/null; then
        yarn install
    elif command -v npm &> /dev/null; then
        npm install
    else
        print_error "Neither yarn nor npm is installed."
        exit 1
    fi
    
    print_success "Sayance Web dependencies installed."
    
    cd ../sayance-server/docker
}

# Update hosts file for local development
update_hosts() {
    print_status "Checking local hosts configuration..."
    
    HOSTS_ENTRIES=(
        "127.0.0.1 sayance.localhost"
        "127.0.0.1 app.sayance.localhost"
        "127.0.0.1 rtc.sayance.localhost"
        "127.0.0.1 call.sayance.localhost"
    )
    
    HOSTS_FILE="/etc/hosts"
    NEEDS_UPDATE=false
    
    for entry in "${HOSTS_ENTRIES[@]}"; do
        if ! grep -q "$entry" "$HOSTS_FILE"; then
            NEEDS_UPDATE=true
            break
        fi
    done
    
    if [ "$NEEDS_UPDATE" = true ]; then
        print_warning "Local hosts file needs to be updated for Sayance domains."
        print_status "Adding entries to $HOSTS_FILE (requires sudo)..."
        
        for entry in "${HOSTS_ENTRIES[@]}"; do
            if ! grep -q "$entry" "$HOSTS_FILE"; then
                echo "$entry" | sudo tee -a "$HOSTS_FILE" > /dev/null
                print_status "Added: $entry"
            fi
        done
        
        print_success "Hosts file updated."
    else
        print_success "Hosts file is already configured."
    fi
}

# Start services
start_services() {
    print_status "Starting Sayance services..."
    
    # Stop any existing services
    print_status "Stopping existing services..."
    docker-compose -f docker-compose.sayance-full.yml down || true
    
    # Build and start services
    print_status "Building and starting services..."
    docker-compose -f docker-compose.sayance-full.yml up --build -d
    
    print_success "Services started successfully."
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for Postgres
    print_status "Waiting for PostgreSQL..."
    until docker-compose -f docker-compose.sayance-full.yml exec postgres pg_isready -U sayance_user -d sayance; do
        sleep 2
    done
    print_success "PostgreSQL is ready."
    
    # Wait for Synapse
    print_status "Waiting for Synapse..."
    until curl -s http://localhost:8008/_matrix/client/versions > /dev/null; do
        sleep 5
    done
    print_success "Synapse is ready."
    
    # Wait for nginx
    print_status "Waiting for nginx..."
    until curl -k -s https://sayance.localhost > /dev/null; do
        sleep 3
    done
    print_success "Nginx is ready."
}

# Show deployment information
show_deployment_info() {
    print_success "🎉 Sayance deployment completed successfully!"
    echo ""
    echo "📋 Service URLs:"
    echo "   🏠 Sayance Web:       https://app.sayance.localhost"
    echo "   🔐 Matrix Homeserver: https://sayance.localhost"
    echo "   📞 RTC Backend:       https://rtc.sayance.localhost"
    echo "   📹 Sayance Call:      https://call.sayance.localhost"
    echo ""
    echo "🔧 Management Commands:"
    echo "   📊 View logs:         docker-compose -f docker-compose.sayance-full.yml logs -f"
    echo "   🔄 Restart services:  docker-compose -f docker-compose.sayance-full.yml restart"
    echo "   🛑 Stop services:     docker-compose -f docker-compose.sayance-full.yml down"
    echo ""
    echo "🔐 SSL Certificate Info:"
    echo "   📄 CA Certificate:    $(pwd)/element-call-backend/ssl/sayance-ca.crt"
    echo "   ⚠️  Add the CA certificate to your browser's trusted certificates"
    echo ""
    echo "🚀 Getting Started:"
    echo "   1. Add the CA certificate to your browser"
    echo "   2. Visit https://app.sayance.localhost"
    echo "   3. Register a new account or login"
    echo "   4. Start chatting and making calls!"
    echo ""
}

# Main deployment flow
main() {
    check_dependencies
    setup_ssl
    build_sayance_web
    update_hosts
    start_services
    wait_for_services
    show_deployment_info
}

# Handle script interruption
trap 'print_error "Deployment interrupted."; exit 1' INT TERM

# Run main function
main "$@" 