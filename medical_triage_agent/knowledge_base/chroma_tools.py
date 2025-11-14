# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Chroma Tools for Querying Vector Database.

This module provides tools for querying the Chroma vector database
to retrieve relevant information from the knowledge base.
"""

import os
from typing import List, Optional
from google import genai
from google.adk.tools import FunctionTool
from google.genai import types
from .chroma_setup import (
    get_chroma_client,
    COLLECTION_BPJS,
    COLLECTION_PPK,
    COLLECTION_BATES,
)


# Environment variables will be read when needed
def get_google_cloud_project():
    """Get GOOGLE_CLOUD_PROJECT, loading .env if needed."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        from pathlib import Path
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            project = os.getenv("GOOGLE_CLOUD_PROJECT")
    return project

def get_google_cloud_location():
    """Get GOOGLE_CLOUD_LOCATION, loading .env if needed."""
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        from pathlib import Path
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    return location


def query_knowledge_base(
    query: str,
    collection_names: Optional[List[str]] = None,
    n_results: int = 5
) -> str:
    """
    Query the medical knowledge base using semantic search. Searches across BPJS criteria, PPK Kemenkes guidelines, and Bates Guide to Physical Examination.
    
    Args:
        query: Search query/question
        collection_names: List of collection names to search. If None, searches all.
        n_results: Number of results to return per collection
        
    Returns:
        Formatted string with relevant information from knowledge base
    """
    if collection_names is None:
        collection_names = [COLLECTION_BPJS, COLLECTION_PPK, COLLECTION_BATES]
    
    client = get_chroma_client()
    
    # Generate embedding for query using Google GenAI
    google_project = get_google_cloud_project()
    google_location = get_google_cloud_location()
    
    if not google_project:
        return "Error: GOOGLE_CLOUD_PROJECT environment variable is not set"
    
    client_genai = genai.Client(
        vertexai=True,
        project=google_project,
        location=google_location,
    )
    
    try:
        # Use gemini-embedding-001 with SEMANTIC_SIMILARITY task type for better search results
        config = types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
        response = client_genai.models.embed_content(
            model="gemini-embedding-001",
            contents=query,  # Can pass string directly
            config=config
        )
        
        # Extract embedding from response.embeddings
        query_embedding = None
        if hasattr(response, 'embeddings') and response.embeddings:
            if isinstance(response.embeddings, list) and len(response.embeddings) > 0:
                content_embedding = response.embeddings[0]
                if hasattr(content_embedding, 'values'):
                    query_embedding = list(content_embedding.values)
        
        if not query_embedding:
            return "Error: Could not extract embedding from response"
    except Exception as e:
        return f"Error generating embedding: {str(e)}"
    
    results_text = []
    
    for collection_name in collection_names:
        try:
            collection = client.get_collection(collection_name)
            
            # Query collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            if results['documents'] and results['documents'][0]:
                results_text.append(f"\n=== {collection_name.upper()} ===")
                for i, doc in enumerate(results['documents'][0], 1):
                    results_text.append(f"\n[Result {i}]")
                    results_text.append(doc)
                    results_text.append("")
        
        except Exception as e:
            print(f"Error querying collection {collection_name}: {e}")
            continue
    
    if not results_text:
        return "No relevant information found in knowledge base."
    
    return "\n".join(results_text)


def query_bpjs_criteria(query: str, n_results: int = 5) -> str:
    """
    Query BPJS emergency criteria knowledge base. Use this to find specific criteria for gawat darurat classification.
    
    Args:
        query: Search query about BPJS criteria
        n_results: Number of results to return
        
    Returns:
        Relevant BPJS criteria information
    """
    return query_knowledge_base(query, [COLLECTION_BPJS], n_results)


def query_ppk_kemenkes(query: str, n_results: int = 5) -> str:
    """
    Query PPK Kemenkes (Primary Health Care Guidelines) knowledge base. Use this for primary care guidelines and protocols.
    
    Args:
        query: Search query about PPK guidelines
        n_results: Number of results to return
        
    Returns:
        Relevant PPK Kemenkes information
    """
    return query_knowledge_base(query, [COLLECTION_PPK], n_results)


def query_bates_guide(query: str, n_results: int = 5) -> str:
    """
    Query Bates Guide to Physical Examination knowledge base. Use this for physical examination techniques and findings.
    
    Args:
        query: Search query about physical examination
        n_results: Number of results to return
        
    Returns:
        Relevant Bates Guide information
    """
    return query_knowledge_base(query, [COLLECTION_BATES], n_results)


# Create ADK tools
# FunctionTool automatically extracts name and description from function docstring
query_knowledge_base_tool = FunctionTool(
    func=query_knowledge_base,
)

query_bpjs_criteria_tool = FunctionTool(
    func=query_bpjs_criteria,
)

query_ppk_kemenkes_tool = FunctionTool(
    func=query_ppk_kemenkes,
)

query_bates_guide_tool = FunctionTool(
    func=query_bates_guide,
)

