#!/bin/bash
# Script to start Custom Web UI server with proper environment variables

cd "$(dirname "$0")"

# Add paths
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# Load environment variables from .env file
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Ensure required variables are set
export GOOGLE_GENAI_USE_VERTEXAI=true

# Kill any process using port 8000
echo "Checking for processes on port 8000..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Killing existing process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
    echo "Port 8000 cleared"
else
    echo "Port 8000 is free"
fi
echo ""

# Verify environment
echo "Starting Custom Web UI server with:"
echo "  GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT:-NOT SET}"
echo "  GOOGLE_CLOUD_LOCATION: ${GOOGLE_CLOUD_LOCATION:-NOT SET}"
echo "  GOOGLE_GENAI_USE_VERTEXAI: ${GOOGLE_GENAI_USE_VERTEXAI:-NOT SET}"
echo ""
echo "Custom UI will be available at: http://127.0.0.1:8000"
echo ""

# Start custom UI server
cd web_ui
uv run python app.py

