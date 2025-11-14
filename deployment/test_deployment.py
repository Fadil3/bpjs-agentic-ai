"""
Test the deployed Medical Triage Agent on Vertex AI Agent Engine.

Usage:
    export GOOGLE_CLOUD_PROJECT=your-project-id
    export GOOGLE_CLOUD_LOCATION=us-central1
    export AGENT_ENGINE_ID=your-agent-engine-id
    python deployment/test_deployment.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.cloud import aiplatform
from vertexai.preview import agent_engines

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")

if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable must be set")

if not AGENT_ENGINE_ID:
    # Try to read from .env file
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("AGENT_ENGINE_ID="):
                    AGENT_ENGINE_ID = line.split("=", 1)[1].strip()
                    break

if not AGENT_ENGINE_ID:
    raise ValueError("AGENT_ENGINE_ID environment variable must be set")

# Initialize AI Platform
aiplatform.init(project=PROJECT_ID, location=LOCATION)

# Get remote agent
resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
remote_agent = agent_engines.ReasoningEngine(resource_name=resource_name)

print(f"Testing agent: {resource_name}")
print("Type 'quit' to exit\n")

# Create session
session = remote_agent.create_session()
print(f"Created session: {session.id}\n")

# Interactive loop
while True:
    try:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        # Query agent
        print("\nAgent: ", end="", flush=True)
        response = remote_agent.stream_query(
            session_id=session.id,
            query=user_input
        )
        
        # Stream response
        for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                print(chunk.text, end="", flush=True)
        
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        break
    except Exception as e:
        print(f"\nError: {e}")

