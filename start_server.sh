#!/bin/bash
# Script to start ADK web server with proper environment variables

cd "$(dirname "$0")"

# Create logs directory if it doesn't exist
mkdir -p logs

# Generate log filename with timestamp
LOG_FILE="logs/server_$(date +%Y%m%d_%H%M%S).log"

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

# Kill any process using port 8000 (ADK web UI port)
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
echo "Starting ADK web server with:"
echo "  GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT:-NOT SET}"
echo "  GOOGLE_CLOUD_LOCATION: ${GOOGLE_CLOUD_LOCATION:-NOT SET}"
echo "  GOOGLE_GENAI_USE_VERTEXAI: ${GOOGLE_GENAI_USE_VERTEXAI:-NOT SET}"
echo "  Port: 8000"
echo "  Log file: $LOG_FILE"
echo ""

# Start server on port 8000 with logging
# Redirect both stdout and stderr to log file, and also display on terminal
# Note: WebSocket 403 errors from ADK web UI are harmless (see WEBSOCKET_403_FIX.md)
# Uncomment the grep line below to filter out 403 errors for cleaner logs:
# uv run adk web --port 8000 2>&1 | grep -v "403 Forbidden" | tee "$LOG_FILE"
uv run adk web --port 8000 2>&1 | tee "$LOG_FILE"

