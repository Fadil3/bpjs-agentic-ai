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
Chroma Vector Database Setup for Medical Triage Agent Knowledge Base.

This module handles:
- Initializing Chroma client
- Extracting text from PDFs
- Chunking text for vectorization
- Generating embeddings using Google's text-embedding-004
- Storing vectors in Chroma
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.config import Settings
from pypdf import PdfReader
from google import genai
from google.genai import types
from google.cloud import logging as cloud_logging


# Environment variables will be read when needed (not at module import time)
# This allows .env file to be loaded first
def get_google_cloud_project():
    """Get GOOGLE_CLOUD_PROJECT, loading .env if needed."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        # Try loading .env file
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
        # Try loading .env file if project not set
        from pathlib import Path
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    return location

# Chroma database path
CHROMA_DB_PATH = Path(__file__).parent.parent.parent / "chroma_db"

# Collection names
COLLECTION_BPJS = "bpjs_criteria"
COLLECTION_PPK = "ppk_kemenkes"
COLLECTION_BATES = "bates_guide"


def get_chroma_client(persist_directory: Optional[Path] = None) -> chromadb.Client:
    """
    Initialize and return Chroma client.
    
    Args:
        persist_directory: Directory to persist Chroma data. If None, uses default.
        
    Returns:
        Chroma client instance
    """
    if persist_directory is None:
        persist_directory = CHROMA_DB_PATH
    
    # Create directory if it doesn't exist
    persist_directory.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(persist_directory),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        )
    )
    
    return client


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text as string
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks for vectorization.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk (in characters)
        chunk_overlap: Overlap between chunks (in characters)
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - chunk_overlap  # Overlap for context
    
    return chunks


def get_logger():
    """Get Google Cloud Logger instance."""
    try:
        google_project = get_google_cloud_project()
        if not google_project:
            return None
        
        logging_client = cloud_logging.Client(project=google_project)
        logger = logging_client.logger("chroma-embeddings")
        return logger
    except Exception as e:
        print(f"Warning: Could not initialize Cloud Logging: {e}")
        return None


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using Google's gemini-embedding-001 model.
    Logs each batch to Google Cloud Logging.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    # Get environment variables (will load .env if needed)
    google_project = get_google_cloud_project()
    google_location = get_google_cloud_location()
    
    # Validate environment variables
    if not google_project:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT environment variable is not set. "
            "Please set it or ensure it's in your .env file."
        )
    
    client = genai.Client(
        vertexai=True,
        project=google_project,
        location=google_location,
    )
    
    # Initialize Cloud Logging
    logger = get_logger()
    
    embeddings = []
    total = len(texts)
    
    # Process in batches to stay under 2,048 token limit per request
    # According to docs: https://ai.google.dev/gemini-api/docs/embeddings
    # - Model: gemini-embedding-001
    # - Input token limit: 2,048 tokens
    # - Can pass multiple texts at once
    import time
    
    # Batch size: ~8 chunks per batch (each chunk ~1000 chars = ~250 tokens)
    # 8 chunks * 250 tokens = ~2000 tokens (safe under 2,048 limit)
    batch_size = 8
    config = types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
    
    print(f"Processing {total} chunks in batches of {batch_size}...")
    
    # Log start (non-blocking)
    if logger:
        try:
            logger.log_text(f"Starting embedding generation: {total} chunks, batch_size={batch_size}")
        except Exception:
            pass  # Ignore logging errors
    
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        batch_start_idx = i
        batch_end_idx = min(i + batch_size, total)
        
        try:
            # Log batch start (non-blocking)
            if logger:
                try:
                    logger.log_struct({
                        "event": "embedding_batch_start",
                        "batch_index": i // batch_size,
                        "chunk_start": batch_start_idx,
                        "chunk_end": batch_end_idx,
                        "batch_size": len(batch),
                        "total_chunks": total
                    })
                except Exception:
                    pass  # Ignore logging errors
            
            # Generate embeddings for batch (can pass list of strings directly)
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=batch,  # Can pass list of strings directly
                config=config
            )
            
            # Extract embeddings from response
            # Response.embeddings is a list matching the input order
            successful_embeddings = 0
            if hasattr(response, 'embeddings') and response.embeddings:
                for idx, content_embedding in enumerate(response.embeddings):
                    if hasattr(content_embedding, 'values'):
                        embedding = list(content_embedding.values)
                        embeddings.append(embedding)
                        successful_embeddings += 1
                    else:
                        embeddings.append([])
            else:
                # If no embeddings, add empty ones for this batch
                embeddings.extend([[]] * len(batch))
            
            # Log batch completion (non-blocking, batched to avoid timeouts)
            if logger:
                try:
                    # Only log batch summary, not individual chunks (too many API calls)
                    logger.log_struct({
                        "event": "embedding_batch_complete",
                        "batch_index": i // batch_size,
                        "chunk_start": batch_start_idx,
                        "chunk_end": batch_end_idx,
                        "successful_embeddings": successful_embeddings,
                        "total_in_batch": len(batch)
                    })
                except Exception as log_error:
                    # Don't let logging errors crash the process
                    if i < 10:  # Only print first few logging errors
                        print(f"Warning: Could not log to Cloud Logging: {log_error}")
            
            # Progress reporting - show every batch for better feedback
            processed = min(i + batch_size, total)
            if processed % 20 == 0 or processed == total:
                progress_pct = 100 * processed // total
                print(f"  Progress: {processed}/{total} chunks ({progress_pct}%)")
                # Log progress (non-blocking, only every 100 chunks to reduce API calls)
                if logger and processed % 100 == 0:
                    try:
                        logger.log_text(f"Embedding progress: {processed}/{total} chunks ({progress_pct}%)")
                    except Exception:
                        pass  # Ignore logging errors
        
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating embeddings for batch {i}: {error_msg}")
            
            # Log error to Google Cloud Logging (non-blocking)
            if logger:
                try:
                    logger.log_struct({
                        "event": "embedding_batch_error",
                        "batch_index": i // batch_size,
                        "chunk_start": batch_start_idx,
                        "chunk_end": batch_end_idx,
                        "error": error_msg
                    }, severity="ERROR")
                except Exception:
                    pass  # Don't let logging errors crash the process
            
            # Add empty embeddings for failed batch
            embeddings.extend([[]] * len(batch))
    
    # Log completion (non-blocking)
    if logger:
        try:
            successful_count = sum(1 for e in embeddings if e)
            logger.log_struct({
                "event": "embedding_generation_complete",
                "total_chunks": total,
                "successful_embeddings": successful_count,
                "failed_embeddings": total - successful_count
            })
        except Exception:
            pass  # Ignore logging errors
    
    return embeddings


def ingest_pdf_to_chroma(
    pdf_path: Path,
    collection_name: str,
    client: Optional[chromadb.Client] = None,
    force_reload: bool = False
) -> int:
    """
    Ingest PDF into Chroma vector database.
    
    Args:
        pdf_path: Path to PDF file
        collection_name: Name of Chroma collection
        client: Chroma client (if None, creates new one)
        force_reload: If True, delete existing collection and reload
        
    Returns:
        Number of chunks ingested
    """
    if client is None:
        client = get_chroma_client()
    
    # Check if collection exists
    try:
        collection = client.get_collection(collection_name)
        if force_reload:
            client.delete_collection(collection_name)
            collection = client.create_collection(name=collection_name)
        else:
            print(f"Collection '{collection_name}' already exists. Use force_reload=True to reload.")
            return collection.count()
    except Exception:
        # Collection doesn't exist, create it
        collection = client.create_collection(name=collection_name)
    
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return 0
    
    print(f"Extracting text from {pdf_path.name}...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print(f"No text extracted from {pdf_path}")
        return 0
    
    print(f"Chunking text...")
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks")
    
    if not chunks:
        return 0
    
    print(f"Generating embeddings...")
    embeddings = generate_embeddings(chunks)
    
    # Filter out empty embeddings
    valid_chunks = []
    valid_embeddings = []
    for chunk, embedding in zip(chunks, embeddings):
        if embedding:
            valid_chunks.append(chunk)
            valid_embeddings.append(embedding)
    
    if not valid_chunks:
        print("No valid embeddings generated")
        return 0
    
    print(f"Storing {len(valid_chunks)} chunks in Chroma...")
    
    # Generate IDs for chunks
    ids = []
    metadata = []
    for i, chunk in enumerate(valid_chunks):
        # Generate unique ID based on content hash
        chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
        ids.append(f"{collection_name}_{i}_{chunk_hash}")
        metadata.append({
            "source": pdf_path.name,
            "chunk_index": i,
            "chunk_size": len(chunk)
        })
    
    # Add to collection
    collection.add(
        documents=valid_chunks,
        embeddings=valid_embeddings,
        ids=ids,
        metadatas=metadata
    )
    
    print(f"Successfully ingested {len(valid_chunks)} chunks from {pdf_path.name}")
    return len(valid_chunks)


def initialize_knowledge_base(force_reload: bool = False) -> dict:
    """
    Initialize knowledge base by ingesting all PDFs into Chroma.
    
    Args:
        force_reload: If True, delete existing collections and reload
        
    Returns:
        Dictionary with ingestion results
    """
    client = get_chroma_client()
    
    results = {}
    
    # Paths to knowledge PDFs
    reasoning_knowledge_dir = Path(__file__).parent.parent / "sub_agents" / "reasoning_agent" / "knowlegde"
    interview_knowledge_dir = Path(__file__).parent.parent / "sub_agents" / "interview_agent" / "knowledge"
    
    bpjs_pdf = reasoning_knowledge_dir / "Pedoman-BPJS-Kriteria-Gawat-Darurat.pdf"
    ppk_pdf = reasoning_knowledge_dir / "ppk-kemenkes.pdf"
    bates_pdf = interview_knowledge_dir / "Bates_Guide_to_Physical_Examination.pdf"
    
    # Ingest BPJS PDF
    if bpjs_pdf.exists():
        print(f"\n{'='*60}")
        print(f"Ingesting BPJS Criteria PDF...")
        print(f"{'='*60}")
        results[COLLECTION_BPJS] = ingest_pdf_to_chroma(
            bpjs_pdf, COLLECTION_BPJS, client, force_reload
        )
    else:
        print(f"BPJS PDF not found: {bpjs_pdf}")
        results[COLLECTION_BPJS] = 0
    
    # Ingest PPK Kemenkes PDF
    if ppk_pdf.exists():
        print(f"\n{'='*60}")
        print(f"Ingesting PPK Kemenkes PDF...")
        print(f"{'='*60}")
        results[COLLECTION_PPK] = ingest_pdf_to_chroma(
            ppk_pdf, COLLECTION_PPK, client, force_reload
        )
    else:
        print(f"PPK PDF not found: {ppk_pdf}")
        results[COLLECTION_PPK] = 0
    
    # Ingest Bates Guide PDF
    if bates_pdf.exists():
        print(f"\n{'='*60}")
        print(f"Ingesting Bates Guide PDF...")
        print(f"{'='*60}")
        results[COLLECTION_BATES] = ingest_pdf_to_chroma(
            bates_pdf, COLLECTION_BATES, client, force_reload
        )
    else:
        print(f"Bates Guide PDF not found: {bates_pdf}")
        results[COLLECTION_BATES] = 0
    
    print(f"\n{'='*60}")
    print(f"Knowledge Base Initialization Complete!")
    print(f"{'='*60}")
    print(f"Results:")
    for collection, count in results.items():
        print(f"  - {collection}: {count} chunks")
    print(f"{'='*60}\n")
    
    return results

