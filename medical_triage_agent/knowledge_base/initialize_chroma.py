#!/usr/bin/env python3
"""
Script to initialize Chroma vector database with PDF knowledge base.

Usage:
    python -m medical_triage_agent.knowledge_base.initialize_chroma
    python -m medical_triage_agent.knowledge_base.initialize_chroma --force-reload
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Path: medical_triage_agent/knowledge_base/initialize_chroma.py
# Go up: knowledge_base -> medical_triage_agent -> root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}")
    print("Make sure GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are set")

from .chroma_setup import initialize_knowledge_base


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Chroma vector database with PDF knowledge base"
    )
    parser.add_argument(
        "--force-reload",
        action="store_true",
        help="Delete existing collections and reload all PDFs"
    )
    
    args = parser.parse_args()
    
    # Verify environment variables
    google_project = os.getenv("GOOGLE_CLOUD_PROJECT")
    google_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    if not google_project:
        print("❌ Error: GOOGLE_CLOUD_PROJECT environment variable is not set!")
        print("\nPlease set it in your .env file or export it:")
        print("  export GOOGLE_CLOUD_PROJECT=your-project-id")
        print("  export GOOGLE_CLOUD_LOCATION=us-central1")
        return
    
    print("=" * 60)
    print("Chroma Knowledge Base Initialization")
    print("=" * 60)
    print(f"Project: {google_project}")
    print(f"Location: {google_location}")
    print()
    
    if args.force_reload:
        print("⚠️  Force reload enabled - existing collections will be deleted")
        print()
    
    results = initialize_knowledge_base(force_reload=args.force_reload)
    
    print("\n✅ Initialization complete!")
    print("\nYou can now use the knowledge base tools in your agents.")
    print("Example:")
    print("  from medical_triage_agent.knowledge_base import query_knowledge_base_tool")


if __name__ == "__main__":
    main()

