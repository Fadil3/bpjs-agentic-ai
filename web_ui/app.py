"""Custom Web UI for Medical Triage Agent - FastAPI application."""

import asyncio
import base64
import json
import logging
import os
import warnings
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import our medical triage agent
import sys
from pathlib import Path

# Add parent directory to path to import medical_triage_agent
sys.path.insert(0, str(Path(__file__).parent.parent))
from medical_triage_agent.agent import root_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress Pydantic serialization warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Application name
APP_NAME = "medical-triage-agent"

# ========================================
# Phase 1: Application Initialization
# ========================================

app = FastAPI(title="Medical Triage Agent - Custom UI")

# ========================================
# Chroma Knowledge Base Initialization
# ========================================

@app.on_event("startup")
async def initialize_knowledge_base():
    """
    Initialize Chroma vector database on application startup (non-blocking).
    This runs in the background so the app can start serving requests immediately.
    
    First tries to download from Cloud Storage, then initializes if needed.
    """
    async def _init_chroma():
        """Background task to initialize Chroma."""
        try:
            from medical_triage_agent.knowledge_base.chroma_setup import (
                get_chroma_client,
                initialize_knowledge_base,
                ensure_chroma_from_gcs
            )
            
            logger.info("Checking Chroma knowledge base...")
            
            # First, try to download from Cloud Storage if available
            # This is fast (download) vs slow (re-embedding)
            downloaded = ensure_chroma_from_gcs()
            if downloaded:
                logger.info("Chroma DB downloaded from Cloud Storage. Verifying...")
            
            # Check if knowledge base already exists (either downloaded or local)
            client = get_chroma_client()
            # In Chroma v0.6.0+, list_collections() returns list of names (strings)
            collection_names = client.list_collections()
            
            expected_collections = ["bpjs_criteria", "ppk_kemenkes", "bates_guide"]
            missing_collections = [c for c in expected_collections if c not in collection_names]
            
            if missing_collections:
                logger.info(f"Missing collections: {missing_collections}. Initializing knowledge base in background...")
                # Run in thread pool to avoid blocking
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(initialize_knowledge_base, False)
                    results = future.result()
                logger.info(f"Knowledge base initialized: {results}")
            else:
                # Verify collections have data
                all_have_data = True
                for coll_name in expected_collections:
                    try:
                        collection = client.get_collection(coll_name)
                        if collection.count() == 0:
                            all_have_data = False
                            break
                    except Exception:
                        all_have_data = False
                        break
                
                if not all_have_data:
                    logger.info("Some collections are empty. Re-initializing in background...")
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(initialize_knowledge_base, True)
                        results = future.result()
                    logger.info(f"Knowledge base re-initialized: {results}")
                else:
                    logger.info("Chroma knowledge base is already initialized and ready.")
        
        except Exception as e:
            logger.warning(f"Could not initialize Chroma knowledge base: {e}")
            logger.warning("The app will continue, but knowledge base features may not work.")
            # Don't fail startup if Chroma init fails - app can still run
    
    # Run initialization in background task
    asyncio.create_task(_init_chroma())

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (React build output)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# Mount assets directory for JS/CSS files
assets_dir = static_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Mount static directory for other static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Define session service
session_service = InMemorySessionService()

# Define runner
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service
)

# ========================================
# HTTP Endpoints
# ========================================

@app.get("/")
async def root():
    """Serve the index.html page."""
    return FileResponse(static_dir / "index.html")

@app.get("/health")
async def health():
    """Health check endpoint."""
    chroma_status = "unknown"
    try:
        from medical_triage_agent.knowledge_base.chroma_setup import get_chroma_client
        client = get_chroma_client()
        # In Chroma v0.6.0+, list_collections() returns list of names (strings)
        collection_names = client.list_collections()
        expected = ["bpjs_criteria", "ppk_kemenkes", "bates_guide"]
        
        if all(c in collection_names for c in expected):
            # Check if collections have data
            total_chunks = 0
            for coll_name in expected:
                try:
                    collection = client.get_collection(coll_name)
                    total_chunks += collection.count()
                except Exception:
                    pass
            if total_chunks > 0:
                chroma_status = f"ready ({total_chunks} chunks)"
            else:
                chroma_status = "initializing"
        else:
            chroma_status = "initializing"
    except Exception:
        chroma_status = "error"
    
    return {
        "status": "ok",
        "app": APP_NAME,
        "chroma_knowledge_base": chroma_status
    }

@app.get("/api/reverse-geocode")
async def reverse_geocode(lat: float, lon: float):
    """
    Reverse geocoding endpoint to avoid CORS issues.
    Proxies request to OpenStreetMap Nominatim API.
    """
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1",
                headers={
                    "User-Agent": "MedicalTriageAgent/1.0"
                },
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"Reverse geocoding failed: {response.status_code}")
                return {"error": "Reverse geocoding failed"}
    except Exception as e:
        logger.error(f"Error in reverse geocoding: {e}")
        return {"error": str(e)}

# ========================================
# WebSocket Endpoint
# ========================================

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str) -> None:
    """
    WebSocket endpoint for streaming with ADK.
    
    Note: This uses run_async() for non-Live API models (gemini-2.5-flash).
    For Live API models (gemini-2.5-flash-native-audio), use run_live() with LiveRequestQueue.
    See: https://google.github.io/adk-docs/get-started/streaming/quickstart-streaming/
    """
    logger.info(f"WebSocket connection: user_id={user_id}, session_id={session_id}")
    await websocket.accept()
    
    # Get or create session
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )
    if not session:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
    
    try:
        while True:
            # Receive message from client
            try:
                message = await websocket.receive()
            except RuntimeError as e:
                # Handle disconnect gracefully
                if "disconnect" in str(e).lower():
                    logger.info("WebSocket disconnected")
                    break
                raise
            
            if "text" in message:
                text_data = message["text"]
                try:
                    json_message = json.loads(text_data)
                    message_type = json_message.get("type", "text")
                    
                    # Handle location message (standalone)
                    if message_type == "location":
                        location = json_message.get("location")
                        if location:
                            # Save location to session state
                            session.state["patient_location"] = location
                            logger.info(f"Location saved to session state: {location}")
                            continue  # Don't process as regular message
                    
                    # Handle regular text/attachment messages
                    user_message = json_message.get("content", json_message.get("text", text_data))
                    attachments = json_message.get("attachments", [])
                    
                    # Handle location sent together with first message
                    location = json_message.get("location")
                    if location:
                        # For InMemorySessionService, we need to update the stored session directly
                        # because get_session returns a copy
                        try:
                            # Access the internal storage directly (InMemorySessionService specific)
                            stored_session = session_service.sessions[APP_NAME][user_id][session_id]
                            stored_session.state["patient_location"] = location
                            logger.info(f"Location saved to session state with first message: {location}")
                            logger.info(f"Session state updated. Current state keys: {list(stored_session.state.keys())}")
                            # Re-fetch session to get updated state for agent
                            session = await session_service.get_session(
                                app_name=APP_NAME,
                                user_id=user_id,
                                session_id=session_id
                            )
                            logger.info(f"Session re-fetched. State keys: {list(session.state.keys())}, patient_location: {session.state.get('patient_location')}")
                        except (KeyError, AttributeError) as e:
                            # Fallback: update the session object directly (may not persist in InMemorySessionService)
                            session.state["patient_location"] = location
                            logger.warning(f"Could not update stored session directly, updated session object: {e}")
                            logger.info(f"Location saved to session state with first message: {location}")
                except json.JSONDecodeError:
                    user_message = text_data
                    attachments = []
                
                # Check if we have content or attachments
                has_content = user_message and user_message.strip() != ""
                has_attachments = attachments and len(attachments) > 0
                
                if not has_content and not has_attachments:
                    continue
                
                logger.debug(f"Received message: {user_message[:100] if user_message else 'No text'}...")
                if has_attachments:
                    logger.debug(f"Received {len(attachments)} attachment(s)")
                
                # Build parts for content
                parts = []
                
                # Add text part if available
                if has_content:
                    parts.append(types.Part.from_text(text=user_message))
                
                # Add attachment parts (images and audio)
                for attachment in attachments:
                    att_type = attachment.get("type")
                    att_data = attachment.get("data")
                    att_mime = attachment.get("mimeType", "")
                    
                    if att_type == "image" and att_data:
                        # Extract base64 data (remove data:image/...;base64, prefix if present)
                        base64_data = att_data
                        if "," in att_data:
                            base64_data = att_data.split(",", 1)[1]
                        
                        try:
                            image_data = base64.b64decode(base64_data)
                            parts.append(types.Part.from_bytes(
                                data=image_data,
                                mime_type=att_mime or "image/jpeg"
                            ))
                            logger.debug(f"Added image part: {att_mime}")
                        except Exception as e:
                            logger.error(f"Error processing image: {e}")
                    
                    elif att_type == "audio" and att_data:
                        # Extract base64 data (remove data:audio/...;base64, prefix if present)
                        base64_data = att_data
                        if "," in att_data:
                            base64_data = att_data.split(",", 1)[1]
                        
                        try:
                            audio_data = base64.b64decode(base64_data)
                            parts.append(types.Part.from_bytes(
                                data=audio_data,
                                mime_type=att_mime or "audio/webm"
                            ))
                            logger.debug(f"Added audio part: {att_mime}")
                        except Exception as e:
                            logger.error(f"Error processing audio: {e}")
                
                # Create content for agent
                if not parts:
                    continue
                    
                content = types.Content(
                    role="user",
                    parts=parts
                )
                
                # Log state before calling agent
                logger.info(f"Calling agent with session state: {dict(session.state)}")
                logger.info(f"patient_location in state: {session.state.get('patient_location')}")
                
                # Stream response from agent using run_async
                # This works with non-Live API models like gemini-2.5-flash
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session.id,
                    new_message=content
                ):
                    # Send event to client
                    try:
                        # Extract text content from event for display
                        event_data = {
                            "type": event.__class__.__name__,
                            "author": getattr(event, "author", None),
                            "content": None,
                            "text": None
                        }
                        
                        # Extract text from event content
                        if hasattr(event, "content") and event.content:
                            if hasattr(event.content, "parts"):
                                text_parts = []
                                for part in event.content.parts:
                                    if hasattr(part, "text") and part.text:
                                        text_parts.append(part.text)
                                if text_parts:
                                    # Only set text, don't duplicate in content.parts
                                    event_data["text"] = "".join(text_parts)
                                    # Don't include content.parts to avoid duplication
                                    # Frontend will use data.text if available
                        
                        # Include full event data for structured parsing
                        event_data["full_event"] = json.loads(event.model_dump_json(exclude_none=True, by_alias=True))
                        
                        await websocket.send_text(json.dumps(event_data, ensure_ascii=False))
                        
                        # Safe logging - handle None text
                        text_preview = event_data.get('text') or ''
                        if text_preview:
                            text_preview = text_preview[:50] + '...' if len(text_preview) > 50 else text_preview
                        logger.debug(f"Sent event: {event.__class__.__name__}, text: {text_preview}")
                    except Exception as e:
                        logger.error(f"Error sending event: {e}", exc_info=True)
            elif "bytes" in message:
                # Handle binary data (for future image/video support)
                logger.warning("Binary data received but not yet supported")
                        
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket connection: {e}", exc_info=True)
    finally:
        logger.info(f"WebSocket connection closed: user_id={user_id}, session_id={session_id}")

# Serve React app index.html for all non-API routes (must be last)
@app.get("/{path:path}")
async def serve_react_app(path: str):
    """Serve React app for all routes except API, WebSocket, and static files."""
    # Don't interfere with API, WebSocket, static files, or assets
    if (path.startswith("api/") or 
        path.startswith("ws/") or 
        path.startswith("static/") or 
        path.startswith("assets/")):
        return {"error": "Not found"}, 404
    
    # Serve index.html for all other routes (SPA routing)
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        return {"error": "Frontend not built. Run 'npm run build' in frontend directory."}, 503

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

