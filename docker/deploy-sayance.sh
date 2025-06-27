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

# Global variables for ngrok URLs
NGROK_WEB_URL=""
NGROK_MATRIX_URL=""
NGROK_RTC_URL=""
NGROK_CALL_URL=""
USE_NGROK=false

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

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --ngrok)
                USE_NGROK=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_warning "Unknown option: $1"
                shift
                ;;
        esac
    done
}

# Show help information
show_help() {
    echo "Sayance Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --ngrok     Enable ngrok tunneling for mobile/emulator testing"
    echo "  -h, --help  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Deploy locally only"
    echo "  $0 --ngrok         # Deploy with ngrok tunneling"
}

# Check if docker, docker-compose, and optionally ngrok are installed
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
    
    if [ "$USE_NGROK" = true ]; then
        if ! command -v ngrok &> /dev/null; then
            print_error "ngrok is not installed. Please install ngrok first."
            print_status "Install ngrok from: https://ngrok.com/download"
            exit 1
        fi
        
        # Check if ngrok is authenticated
        if ! ngrok config check &> /dev/null; then
            print_warning "ngrok might not be authenticated. Please run 'ngrok authtoken YOUR_TOKEN'"
            print_status "Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken"
        fi
    fi
    
    print_success "All dependencies are available."
}

# Setup ngrok tunnels
setup_ngrok_tunnels() {
    if [ "$USE_NGROK" != true ]; then
        return 0
    fi
    
    print_status "Setting up ngrok tunnels for mobile/emulator access..."
    
    # Kill any existing ngrok processes
    pkill -f ngrok || true
    sleep 2
    
    # Create ngrok config file for multiple tunnels in single session
    print_status "Creating ngrok configuration for multiple tunnels..."
    cat > /tmp/sayance-ngrok.yml << EOF
version: "2"
authtoken: ${NG_ROK_TOKEN}
api_key: ${NG_ROK_API_KEY}
tunnels:
  sayance-web:
    proto: http
    addr: 443
    host_header: app.sayance.localhost
    domain: sayance-web.ngrok.app
  matrix-api:
    proto: http
    addr: 8008
    host_header: sayance.localhost
    domain: sayance-server.ngrok.app
  sayance-call:
    proto: http
    addr: 443
    host_header: call.sayance.localhost
    domain: sayance-call.ngrok.app
EOF
    
    # Start all tunnels in a single ngrok session
    print_status "Starting ngrok with multiple tunnels (single session)..."
    print_status "Configuration file: /tmp/sayance-ngrok.yml"s
    
    # Start ngrok with all tunnels
    ngrok start --all --config=/tmp/sayance-ngrok.yml > /tmp/ngrok-all.log 2>&1 &
    NGROK_PID=$!
    
    # Wait for startup
    sleep 10
    
    # Check if the process is still running
    if ! kill -0 $NGROK_PID 2>/dev/null; then
        print_error "ngrok tunnels failed to start!"
        print_status "Full log output:"
        cat /tmp/ngrok-all.log
        return 1
    fi
    
    print_success "ngrok tunnels started in single session."
    print_status "Check ngrok dashboard at: http://localhost:4040"
    print_status "Log file: /tmp/ngrok-all.log"
}

# Get ngrok URLs
get_ngrok_urls() {
    if [ "$USE_NGROK" != true ]; then
        return 0
    fi
    
    print_status "Retrieving ngrok tunnel URLs..."
    
    # Wait for ngrok to fully start
    sleep 5
    
    local max_attempts=12
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Attempt $attempt/$max_attempts to retrieve ngrok URLs..."
        
        # Check if ngrok API is responding
        if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
            local tunnels_json=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)
            
            # Extract all URLs using simple grep
            local all_urls=$(echo "$tunnels_json" | grep -o 'https://[^"]*\.ngrok[^"]*\.app' | sort -u)
            
                         if [ -n "$all_urls" ]; then
                 print_success "Found ngrok tunnel URLs:"
                 echo ""
                 local url_count=1
                 while IFS= read -r url; do
                     if [ $url_count -eq 1 ]; then
                         NGROK_WEB_URL="$url"
                         echo "   🏠 Sayance Web App:   $url"
                     elif [ $url_count -eq 2 ]; then
                         NGROK_MATRIX_URL="$url"
                         echo "   🔐 Matrix API:        $url"
                     elif [ $url_count -eq 3 ]; then
                         NGROK_CALL_URL="$url"
                         echo "   📹 Sayance Call:      $url"
                     else
                         echo "   📍 Additional URL:    $url"
                     fi
                     ((url_count++))
                 done <<< "$all_urls"
                 echo ""
                 
                 # All services are now accessible via their specific ngrok URLs
                 print_success "ngrok URLs retrieved successfully."
                 break
             fi
        else
            print_status "ngrok API not ready yet..."
        fi
        
        sleep 3
        ((attempt++))
    done
    
    if [ -z "$NGROK_WEB_URL" ]; then
        print_error "Could not retrieve ngrok URLs after $max_attempts attempts."
        print_status "Manual steps:"
        echo "   1. Check ngrok dashboard: http://localhost:4040"
        echo "   2. Check ngrok processes: ps aux | grep ngrok"
        echo "   3. Check logs: tail -f /tmp/ngrok-all.log"
        echo ""
        
        # Show what we can find manually
        print_status "Attempting manual URL extraction..."
        local raw_response=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)
        if [ -n "$raw_response" ]; then
            echo "Raw API response (first 10 lines):"
            echo "$raw_response" | head -10
            echo ""
            
            # Try to find any URLs in the response
            local found_urls=$(echo "$raw_response" | grep -o 'https://[^"]*' | head -5)
            if [ -n "$found_urls" ]; then
                echo "Potential URLs found:"
                echo "$found_urls"
            fi
        fi
    fi
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
    echo "📋 Local Service URLs:"
    echo "   🏠 Sayance Web:       https://app.sayance.localhost"
    echo "   🔐 Matrix Homeserver: https://sayance.localhost"
    echo "   📞 RTC Backend:       https://rtc.sayance.localhost"
    echo "   📹 Sayance Call:      https://call.sayance.localhost"
    
    if [ "$USE_NGROK" = true ]; then
        echo ""
        echo "🌐 Public URLs (for mobile/emulator testing):"
        if [ -n "$NGROK_WEB_URL" ]; then
            echo "   🏠 Sayance Web App:   $NGROK_WEB_URL"
            echo "   🔐 Matrix Homeserver: $NGROK_MATRIX_URL"
            echo "   📹 Sayance Call:      ${NGROK_CALL_URL:-'Check dashboard'}"
        else
            echo "   ⚠️  Check ngrok dashboard: http://localhost:4040"
        fi
        echo ""
        echo "📱 Mobile Testing Instructions:"
        echo "   1. Use the Sayance Web App URL for general access"
        echo "   2. Use the Sayance Call URL for video call features"
        echo "   3. ngrok provides HTTPS by default (no cert issues)"
        echo "   4. Share URLs with team members for testing"
        echo ""
        echo "🔧 ngrok Management:"
        echo "   📊 Dashboard:         http://localhost:4040"
        echo "   🛑 Stop tunnels:      pkill -f ngrok"
        echo "   📋 View all tunnels:  curl -s http://localhost:4040/api/tunnels | grep public_url"
    fi
    
    echo ""
    echo "🔧 Management Commands:"
    echo "   📊 View logs:         docker-compose -f docker-compose.sayance-full.yml logs -f"
    echo "   🔄 Restart services:  docker-compose -f docker-compose.sayance-full.yml restart"
    echo "   🛑 Stop services:     docker-compose -f docker-compose.sayance-full.yml down"
    echo ""
    echo "🔐 SSL Certificate Info:"
    echo "   📄 CA Certificate:    $(pwd)/element-call-backend/ssl/sayance-ca.crt"
    echo "   ⚠️  Add the CA certificate to your browser's trusted certificates (local only)"
    echo ""
    echo "🚀 Getting Started:"
    if [ "$USE_NGROK" = true ]; then
        echo "   📱 Mobile/Emulator: Use the public URLs above"
        echo "   💻 Local Browser: Add CA certificate, then visit https://app.sayance.localhost"
    else
        echo "   1. Add the CA certificate to your browser"
        echo "   2. Visit https://app.sayance.localhost"
    fi
    echo "   3. Register a new account or login"
    echo "   4. Start chatting and making calls!"
    echo ""
}

# Clean up function
cleanup() {
    if [ "$USE_NGROK" = true ]; then
        print_status "Cleaning up ngrok tunnels..."
        pkill -f ngrok || true
        rm -f /tmp/ngrok-*.log
        rm -f /tmp/ngrok_urls.txt
        rm -f /tmp/sayance-ngrok.yml
    fi
}

# Main deployment flow
main() {
    parse_arguments "$@"
    check_dependencies
    setup_ssl
    build_sayance_web
    # update_hosts
    start_services
    wait_for_services
    
    if [ "$USE_NGROK" = true ]; then
        setup_ngrok_tunnels
        if [ $? -eq 0 ]; then
            get_ngrok_urls
        else
            print_error "ngrok setup failed. Continuing without ngrok..."
            print_status "To debug: ./debug-ngrok.sh"
        fi
    fi
    
    show_deployment_info
}

# Handle script interruption
trap 'print_error "Deployment interrupted."; cleanup; exit 1' INT TERM

# Run main function
main "$@" 