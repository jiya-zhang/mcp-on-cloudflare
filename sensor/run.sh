#!/bin/bash

# MacBook Camera Busyness Monitor - Run Script
# This script helps you run the busyness monitor with your Cloudflare Worker URL

# Check if required arguments are provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <WORKER_URL> [CAMERA_INDEX] [INTERVAL]"
    echo ""
    echo "Arguments:"
    echo "  WORKER_URL   - Your deployed Cloudflare Worker URL (e.g., https://your-worker.your-subdomain.workers.dev)"
    echo "  CAMERA_INDEX - Camera index (optional, default: 0)"
    echo "  INTERVAL     - Capture interval in seconds (optional, default: 30)"
    echo ""
    echo "Example:"
    echo "  $0 https://starter-mcp-cloudflare.your-subdomain.workers.dev"
    echo "  $0 https://starter-mcp-cloudflare.your-subdomain.workers.dev 0 60"
    echo ""
    echo "First, deploy your worker with:"
    echo "  cd ../beezee && npx wrangler deploy"
    exit 1
fi

WORKER_URL=$1
CAMERA_INDEX=${2:-0}
INTERVAL=${3:-30}

echo "Starting MacBook Camera Busyness Monitor..."
echo "Worker URL: $WORKER_URL"
echo "Camera Index: $CAMERA_INDEX"
echo "Interval: ${INTERVAL}s"
echo "Press Ctrl+C to stop"
echo ""

# Run the Python script
python3 main.py \
    --worker-url "$WORKER_URL" \
    --camera "$CAMERA_INDEX" \
    --interval "$INTERVAL"
