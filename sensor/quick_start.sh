#!/bin/bash

# Quick Start Script for MacBook Camera Busyness Monitor
# This script will help you get everything running quickly

echo "🚀 MacBook Camera Busyness Monitor - Quick Start"
echo "=" * 50

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Please run this script from the sensor directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Deploy the worker
echo "🌐 Deploying Cloudflare Worker..."
cd ../beezee
npx wrangler deploy
WORKER_URL=$(npx wrangler whoami 2>/dev/null | grep -o 'https://[^/]*\.workers\.dev' | head -1)

if [ -z "$WORKER_URL" ]; then
    echo "❌ Could not get worker URL. Please check your deployment."
    echo "   You can find your worker URL in the Cloudflare dashboard."
    read -p "Enter your worker URL: " WORKER_URL
fi

cd ../sensor

# Test the system
echo "🧪 Testing the system..."
python test_system.py

if [ $? -eq 0 ]; then
    echo "✅ System test passed!"
    echo ""
    echo "🎉 Ready to start monitoring!"
    echo ""
    echo "To start monitoring, run:"
    echo "  ./run.sh $WORKER_URL"
    echo ""
    echo "Or for a test run (once):"
    echo "  python main.py --worker-url $WORKER_URL --once"
    echo ""
    echo "To view your data, visit:"
    echo "  $WORKER_URL/busyness"
else
    echo "❌ System test failed. Please check the errors above."
    exit 1
fi
