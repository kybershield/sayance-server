#!/bin/bash

# ngrok Debug Script
# This script helps diagnose ngrok issues

echo "🔍 ngrok Debug Information"
echo "=========================="

# Check if ngrok is installed
echo "1. Checking ngrok installation..."
if command -v ngrok &> /dev/null; then
    echo "   ✅ ngrok is installed: $(which ngrok)"
    echo "   📄 Version: $(ngrok version)"
else
    echo "   ❌ ngrok is not installed"
    echo "   📥 Install from: https://ngrok.com/download"
    exit 1
fi

echo ""
echo "2. Checking ngrok authentication..."
if ngrok config check &> /dev/null; then
    echo "   ✅ ngrok is authenticated"
else
    echo "   ❌ ngrok authentication failed"
    echo "   🔑 Run: ngrok authtoken YOUR_TOKEN"
    echo "   🌐 Get token from: https://dashboard.ngrok.com/get-started/your-authtoken"
fi

echo ""
echo "3. Checking running ngrok processes..."
NGROK_PROCESSES=$(ps aux | grep ngrok | grep -v grep)
if [ -n "$NGROK_PROCESSES" ]; then
    echo "   🔄 Found running ngrok processes:"
    echo "$NGROK_PROCESSES" | sed 's/^/   /'
else
    echo "   ⭕ No ngrok processes running"
fi

echo ""
echo "4. Checking ngrok API endpoint..."
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "   ✅ ngrok API is accessible"
    echo "   🌐 Dashboard: http://localhost:4040"
    
    # Show current tunnels
    echo ""
    echo "   📋 Current tunnels:"
    TUNNELS=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)
    if [ -n "$TUNNELS" ]; then
        echo "$TUNNELS" | grep -o '"public_url":"[^"]*' | sed 's/"public_url":"//g' | sed 's/^/      /'
    else
        echo "      No active tunnels"
    fi
else
    echo "   ❌ ngrok API not accessible"
fi

echo ""
echo "5. Checking log files..."
LOG_FILES="/tmp/ngrok-*.log"
for log_file in $LOG_FILES; do
    if [ -f "$log_file" ]; then
        echo "   📄 Found log: $log_file"
        echo "      Last 5 lines:"
        tail -5 "$log_file" | sed 's/^/         /'
    fi
done

echo ""
echo "6. Testing simple ngrok command..."
echo "   🧪 Testing: ngrok http 8080 --log=stdout (5 seconds)"
timeout 5s ngrok http 8080 --log=stdout 2>&1 | head -10 | sed 's/^/   /'
echo "   ⏹️  Test completed"

echo ""
echo "7. Account limits check..."
echo "   💡 Free ngrok accounts are limited to:"
echo "      - 1 simultaneous agent session"
echo "      - 4 tunnels per agent"
echo "      - Basic authentication"
echo ""
echo "   🔗 Check your account: https://dashboard.ngrok.com/agents"

echo ""
echo "🔧 Quick Fixes:"
echo "   🛑 Kill all ngrok: pkill -f ngrok"
echo "   🚀 Start simple tunnel: ngrok http 443"
echo "   📊 Open dashboard: open http://localhost:4040"
echo "   🔄 Restart deployment: ./deploy-sayance.sh --ngrok" 