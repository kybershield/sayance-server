#!/bin/bash

# Sayance Development Start Script
# This script starts all services in development mode with sayance.local configuration

set -e

echo "🚀 Starting Sayance Development Environment..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

# Check if required files exist
if [ ! -f "docker-compose.dev.yml" ]; then
    echo "❌ docker-compose.dev.yml not found. Please run this script from the docker directory."
    exit 1
fi

echo "🧹 Cleaning up any existing containers..."
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

echo "🔧 Starting development services..."
docker-compose -f docker-compose.dev.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 15

# Wait for Synapse health check
echo "🏥 Checking Synapse health..."
for i in {1..30}; do
    if curl -s http://localhost:8008/_matrix/client/versions > /dev/null 2>&1; then
        echo "✅ Synapse is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Synapse health check failed after 30 attempts"
        exit 1
    fi
    echo "   Attempt $i/30 - waiting for Synapse..."
    sleep 2
done

echo "🏥 Checking Element Call services..."

# Check JWT service
if curl -s http://localhost:8070/healthz > /dev/null 2>&1; then
    echo "✅ JWT Auth Service is running!"
else
    echo "⚠️  JWT Auth Service may not be ready yet"
fi

# Check LiveKit
if curl -s http://localhost:7880/health > /dev/null 2>&1; then
    echo "✅ LiveKit SFU is running!"
else
    echo "⚠️  LiveKit SFU may not be ready yet"
fi

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📊 Service Status:"
echo "   Matrix Homeserver: http://localhost:8008"
echo "   JWT Service:       http://localhost:8070"
echo "   LiveKit SFU:       http://localhost:7880"
echo "   PostgreSQL:        localhost:5432"
echo ""
echo "📱 Mobile App Configuration:"
echo "   Homeserver URL:    http://192.168.1.81:8008"
echo "   Server Name:       sayance.local"
echo ""
echo "👥 Test Accounts:"
echo "   Register accounts like: @alice:sayance.local, @bob:sayance.local"
echo ""
echo "🔍 To check logs:"
echo "   docker logs docker-synapse-1"
echo "   docker logs sayance-element-call-jwt-dev"
echo "   docker logs sayance-element-call-livekit-dev"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose -f docker-compose.dev.yml down"
echo ""
echo "📖 For detailed testing instructions, see: ../sayance-client/LOCAL_TESTING_GUIDE.md" 