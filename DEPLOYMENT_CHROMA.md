# Chroma Vector Database Deployment Guide

## Overview

The Chroma vector database is **NOT stored in Git** (it's 278MB and excluded in `.gitignore`). Instead, embeddings are **generated automatically during deployment**.

## How It Works

### Option 1: Auto-Initialize on Startup (Current Implementation) ✅

The FastAPI app automatically initializes Chroma when it starts:

1. **On container startup**, the app checks if Chroma collections exist
2. **If missing or empty**, it automatically runs the initialization script
3. **PDFs are embedded** using Google's `gemini-embedding-001` model
4. **Chroma DB is created** in the container's filesystem

**Pros:**
- ✅ Simple - no extra steps needed
- ✅ Always up-to-date embeddings
- ✅ Works automatically on deployment

**Cons:**
- ⚠️ First startup takes 5-10 minutes (embedding generation)
- ⚠️ DB is lost when container restarts (unless using persistent volume)

### Option 2: Use Cloud Storage (Recommended for Production)

Store Chroma DB in Cloud Storage and download on startup:

1. **Build Chroma locally** and upload to Cloud Storage
2. **On container startup**, download from Cloud Storage
3. **If not found**, generate embeddings and upload

**Pros:**
- ✅ Faster startup (download is faster than embedding)
- ✅ Persistent across deployments
- ✅ Can share DB across multiple instances

**Cons:**
- ⚠️ Requires Cloud Storage setup
- ⚠️ Need to manage upload/download

### Option 3: Generate During Cloud Build

Add Chroma initialization as a Cloud Build step:

1. **In `cloudbuild.yaml`**, add step to initialize Chroma
2. **Copy Chroma DB** into Docker image
3. **Container starts** with pre-built DB

**Pros:**
- ✅ Fastest startup time
- ✅ DB is baked into image

**Cons:**
- ⚠️ Larger Docker image (~300MB)
- ⚠️ Slower build process

## Current Implementation (Option 1)

The app uses **Option 1** - auto-initialization on startup.

### What Happens:

1. **Container starts** → FastAPI app loads
2. **Startup event** → Checks Chroma collections
3. **If empty/missing** → Runs `initialize_knowledge_base()`
4. **Embeds PDFs** → Creates Chroma DB in container
5. **App ready** → Can serve requests

### First Startup Time:

- **BPJS PDF**: ~1 minute (59 chunks)
- **PPK PDF**: ~5 minutes (2,346 chunks)
- **Bates PDF**: ~6 minutes (2,504 chunks)
- **Total**: ~10-12 minutes for first startup

### Subsequent Starts:

If using **Cloud Run with persistent volume** or **Cloud Storage**, the DB persists and startup is instant.

## Using Cloud Storage (Recommended)

To use Cloud Storage for persistence:

1. **Create bucket:**
   ```bash
   gsutil mb gs://your-project-chroma-db
   ```

2. **Upload Chroma DB (after local initialization):**
   ```bash
   gsutil -m cp -r chroma_db/* gs://your-project-chroma-db/
   ```

3. **Modify startup code** to download from Cloud Storage if not exists locally

## Using Persistent Volume (Cloud Run)

For Cloud Run, you can use a persistent volume:

```yaml
# In cloudbuild.yaml, add to Cloud Run deploy:
- '--volume'
- 'name=chroma-db,type=cloud-storage,bucket=your-chroma-bucket'
- '--volume-mount'
- 'volume=chroma-db,mount-path=/app/chroma_db'
```

## Summary

**Current Setup:**
- ✅ Chroma DB is **NOT in Git** (correctly excluded)
- ✅ Embeddings are **generated on deployment** (auto-initialization)
- ✅ First startup takes ~10 minutes
- ✅ Subsequent starts are instant if using persistent storage

**Recommendation:**
- For **development**: Current setup is fine
- For **production**: Use Cloud Storage or persistent volume for faster startup

