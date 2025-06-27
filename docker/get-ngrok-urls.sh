#!/bin/bash

# Helper script to get ngrok public URLs
# Usage: ./get-ngrok-urls.sh

echo "🔍 Retrieving ngrok tunnel URLs..."
echo "=================================="

# Check if ngrok is running
if ! pgrep -f ngrok > /dev/null; then
    echo "❌ ngrok is not running. Start it first with:"
    echo "   ./deploy-sayance.sh --ngrok"
    exit 1
fi

# Check if ngrok API is accessible
if ! curl -s http://localhost:4040/api/tunnels > /dev/null; then
    echo "❌ ngrok API not accessible at localhost:4040"
    echo "🔧 Try these commands:"
    echo "   ps aux | grep ngrok"
    echo "   netstat -tlnp | grep 4040"
    exit 1
fi

echo "✅ ngrok is running, fetching URLs..."
echo ""

# Get the JSON response
TUNNELS_JSON=$(curl -s http://localhost:4040/api/tunnels)

# Method 1: Using jq (if available)
if command -v jq &> /dev/null; then
    echo "📋 Public URLs (using jq):"
    echo "$TUNNELS_JSON" | jq -r '.tunnels[] | "   \(.name): \(.public_url)"'
else
    # Method 2: Using grep/sed
    echo "📋 Public URLs:"
    echo "$TUNNELS_JSON" | grep -o '"public_url":"[^"]*' | sed 's/"public_url":"/   /' | nl -w1 -s'. '
fi

echo ""
echo "🌐 Quick Access URLs:"
URLS=$(echo "$TUNNELS_JSON" | grep -o 'https://[^"]*\.ngrok[^"]*\.app' | sort -u)

if [ -n "$URLS" ]; then
    URL_COUNT=1
    while IFS= read -r url; do
        case $URL_COUNT in
            1) echo "   🏠 Sayance Web:  $url" ;;
            2) echo "   🔐 Matrix API:   $url" ;;
            3) echo "   📹 Sayance Call: $url" ;;
            *) echo "   📍 Extra URL:    $url" ;;
        esac
        ((URL_COUNT++))
    done <<< "$URLS"
else
    echo "   ❌ No URLs found"
fi

echo ""
echo "🔧 Useful Commands:"
echo "   📊 Open dashboard:    open http://localhost:4040"
echo "   📋 Raw JSON:         curl -s http://localhost:4040/api/tunnels | jq ."
echo "   🔍 Check processes:   ps aux | grep ngrok"
echo "   🛑 Stop tunnels:      pkill -f ngrok" 