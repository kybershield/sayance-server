#!/bin/bash

# Sayance Element Call Stop Script
# This script stops all Element Call and Synapse services

set -e

echo "🛑 Stopping Sayance Element Call services..."

# Stop all services
docker-compose -f docker-compose.local.yml -f docker-compose.element-call.yml down

echo "✅ All services stopped!"
echo ""
echo "🧹 To remove all data (including databases), run:"
echo "   docker-compose -f docker-compose.local.yml -f docker-compose.element-call.yml down -v" 