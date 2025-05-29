#!/bin/bash

# Sayance Element Call Setup Script
# This script helps you start Element Call services for your Sayance homeserver

set -e

echo "🚀 Starting Sayance Element Call Setup..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

# Check if required files exist
if [ ! -f "docker-compose.local.yml" ]; then
    echo "❌ docker-compose.local.yml not found. Please run this script from the docker directory."
    exit 1
fi

if [ ! -f "docker-compose.element-call.yml" ]; then
    echo "❌ docker-compose.element-call.yml not found. Please ensure all Element Call files are present."
    exit 1
fi

echo "📋 Checking current services..."
docker-compose -f docker-compose.local.yml ps

echo "🔧 Starting Synapse and PostgreSQL services..."
docker-compose -f docker-compose.local.yml up -d

echo "⏳ Waiting for Synapse to be ready..."
sleep 10

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

echo "🎥 Starting Element Call services..."
docker-compose -f docker-compose.local.yml -f docker-compose.element-call.yml up -d

echo "⏳ Waiting for Element Call services to start..."
sleep 15

echo "🏥 Checking Element Call services..."

# Check JWT service
if curl -s http://localhost:8070 > /dev/null 2>&1; then
    echo "✅ JWT Auth Service is running!"
else
    echo "⚠️  JWT Auth Service may not be ready yet"
fi

# Check LiveKit
if netstat -tlnp 2>/dev/null | grep :7880 > /dev/null; then
    echo "✅ LiveKit SFU is running!"
else
    echo "⚠️  LiveKit SFU may not be ready yet"
fi

echo ""
echo "🎉 Element Call services are starting up!"
echo ""
echo "📝 Next steps:"
echo "1. Configure your reverse proxy (see ELEMENT_CALL_SETUP.md)"
echo "2. Set up DNS for matrixrtc.sayance.org"
echo "3. Copy well-known-matrix-client.json to your web server"
echo "4. Test with a Matrix client"
echo ""
echo "📊 Service Status:"
echo "   Synapse:     http://localhost:8008"
echo "   JWT Service: http://localhost:8070"
echo "   LiveKit SFU: tcp://localhost:7880"
echo ""
echo "📖 For detailed setup instructions, see: ELEMENT_CALL_SETUP.md"
echo ""
echo "🔍 To check logs:"
echo "   docker logs sayance-element-call-jwt"
echo "   docker logs sayance-element-call-livekit"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose -f docker-compose.local.yml -f docker-compose.element-call.yml down" 