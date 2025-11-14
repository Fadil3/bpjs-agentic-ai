#!/bin/bash
# Script to start ADK web server with proper environment variables

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

# Verify environment
echo "Starting server with:"
echo "  GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT:-NOT SET}"
echo "  GOOGLE_CLOUD_LOCATION: ${GOOGLE_CLOUD_LOCATION:-NOT SET}"
echo "  GOOGLE_GENAI_USE_VERTEXAI: ${GOOGLE_GENAI_USE_VERTEXAI:-NOT SET}"
echo ""

# Start server on port 8000
uv run adk web --port 8000

