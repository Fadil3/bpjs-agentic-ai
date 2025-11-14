"""
Deploy Medical Triage Agent to Vertex AI Agent Engine.

Usage:
    export GOOGLE_CLOUD_PROJECT=your-project-id
    export GOOGLE_CLOUD_LOCATION=us-central1
    python deployment/deploy.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.cloud import aiplatform
from vertexai.preview import agent_engines
from google.adk.apps import AdkApp
from medical_triage_agent.agent import root_agent

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable must be set")

# Find wheel file
dist_dir = Path(__file__).parent.parent / "dist"
wheel_files = list(dist_dir.glob("medical_triage_agent-*.whl"))

if not wheel_files:
    print("Error: Wheel file not found. Please run 'uv build' first.")
    sys.exit(1)

WHEEL_FILE = str(wheel_files[0])
print(f"Using wheel file: {WHEEL_FILE}")

# Initialize AI Platform
aiplatform.init(project=PROJECT_ID, location=LOCATION)

# Create ADK App
app = AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

print(f"Deploying to Vertex AI Agent Engine...")
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")

# Deploy to Agent Engine
try:
    remote_agent = agent_engines.create(
        app,
        display_name="medical-triage-agent",
        requirements=[WHEEL_FILE],
        extra_packages=[WHEEL_FILE],
        env_vars={
            "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
            "GOOGLE_CLOUD_LOCATION": LOCATION,
            "GOOGLE_GENAI_USE_VERTEXAI": "true",
        }
    )
    
    print(f"\n✅ Successfully deployed!")
    print(f"Resource name: {remote_agent.resource_name}")
    print(f"\nTo test the deployment, use:")
    print(f"  python deployment/test_deployment.py")
    
except Exception as e:
    print(f"\n❌ Deployment failed: {e}")
    sys.exit(1)

