#!/bin/bash

# Sayance Element Call Cleanup Script
# This script removes any existing containers and networks for a fresh start

set -e

echo "🧹 Cleaning up existing Sayance services..."

# Stop and remove containers
echo "Stopping containers..."
docker-compose -f docker-compose.local.yml -f docker-compose.element-call.yml down 2>/dev/null || true

# Remove any orphaned containers
echo "Removing orphaned containers..."
docker container prune -f 2>/dev/null || true

# Remove networks
echo "Removing networks..."
docker network ls --format "{{.Name}}" | grep "sayance\|docker_sayance" | xargs -r docker network rm 2>/dev/null || true

# Remove volumes (optional - uncomment if you want to remove data)
# echo "Removing volumes..."
# docker volume ls --format "{{.Name}}" | grep "sayance\|docker" | xargs -r docker volume rm 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "🚀 You can now run ./start-element-call.sh to start fresh" 