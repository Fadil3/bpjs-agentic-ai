"""Custom Web UI for Medical Triage Agent - FastAPI application."""

import asyncio
import base64
import json
import logging
import os
import warnings
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
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
# Chat History & Room Management API
# ========================================

# In-memory storage for chat rooms (in production, use database)
chat_rooms_db: dict[str, dict] = {}
chat_messages_db: dict[str, list] = {}


# Seed data for chat rooms and messages
def seed_chat_data():
    """Seed initial chat data for demonstration."""
    import time
    from datetime import datetime, timedelta
    
    # Create sample user IDs
    user_id_1 = "user_001"
    user_id_2 = "user_002"
    
    # Chat Room 1: Konsultasi Pusing
    room_1_id = "room_001"
    room_1 = {
        "id": room_1_id,
        "userId": user_id_1,
        "sessionId": "session_001",
        "createdAt": (datetime.now() - timedelta(days=2)).isoformat(),
        "lastMessageAt": (datetime.now() - timedelta(days=1, hours=5)).isoformat(),
        "title": "Konsultasi Pusing Ringan",
        "patientName": "Sasmito",
        "isArchived": True,  # Mark as archived/read-only
    }
    chat_rooms_db[room_1_id] = room_1
    chat_messages_db[room_1_id] = [
        {
            "type": "agent",
            "content": "Halo! Saya adalah Smart Triage Agent. Saya akan membantu Anda dalam proses triase medis. Saya sudah mencatat lokasi Anda di Jawa Barat. Untuk siapa Anda menanyakan?",
            "id": "msg_001",
            "timestamp": (datetime.now() - timedelta(days=2, hours=2)).isoformat(),
            "author": "root_agent",
        },
        {
            "type": "human",
            "content": "Untuk saya sendiri",
            "id": "msg_002",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=55)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Baik, saya mengerti. Bisakah Anda ceritakan keluhan yang Anda alami?",
            "id": "msg_003",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=50)).isoformat(),
            "author": "interview_agent",
        },
        {
            "type": "human",
            "content": "Saya pusing ringan setelah bangun tidur",
            "id": "msg_004",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=45)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Terima kasih, saya mencatat Anda merasa pusing ringan setelah bangun tidur. Untuk memahami lebih baik, bisakah Anda ceritakan:\n1. Apakah pusingnya terasa seperti berputar atau seperti melayang?\n2. Sejak kapan pusing ini muncul?\n3. Apakah ada gejala lain yang menyertai?",
            "id": "msg_005",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=40)).isoformat(),
            "author": "interview_agent",
        },
        {
            "type": "human",
            "content": "Tidak berputar, sudah 10 menit, tidak ada gejala lain",
            "id": "msg_006",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=35)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Baik, saya mencatat pusing tidak berputar selama 10 menit tanpa gejala lain. Apakah Anda sudah minum obat untuk mengatasi pusing ini?",
            "id": "msg_007",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=30)).isoformat(),
            "author": "interview_agent",
        },
        {
            "type": "human",
            "content": "Belum minum obat",
            "id": "msg_008",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=25)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Terima kasih, data gejala telah berhasil diekstrak dan disimpan. Informasi ini akan digunakan untuk analisis lebih lanjut.",
            "id": "msg_009",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=20)).isoformat(),
            "author": "interview_agent",
        },
        {
            "type": "agent",
            "content": "Berdasarkan analisis kondisi Anda, dengan gejala **pusing ringan setelah bangun tidur yang sudah membaik**, kondisi ini dikategorikan sebagai **Non-Urgen**.\n\n**Justifikasi Detail dengan Referensi Knowledge Base:**\n\nKlasifikasi ini berdasarkan Pedoman Pelayanan Primer Kesehatan (PPK) Kemenkes dan Pedoman BPJS Kriteria Gawat Darurat.\n\nGejala pusing yang Anda alami, yaitu timbul mendadak saat perubahan posisi (bangun tidur) dan berlangsung singkat (10 menit) serta sudah membaik, sangat konsisten dengan kondisi seperti vertigo posisi paroksismal jinak (BPPV) atau hipotensi ortostatik.\n\n**Tindakan yang telah diambil:**\n1. Saya telah mengambil panduan perawatan mandiri (self-care guide) untuk pusing ringan.\n2. Saya telah mengidentifikasi Fasilitas Kesehatan Tingkat Pertama (FKTP) terdaftar Anda.\n\n**Instruksi selanjutnya:**\n1. **Ikuti Panduan Perawatan Mandiri:**\n   - Istirahat yang cukup\n   - Minum air putih yang banyak\n   - Hindari aktivitas berat\n2. **Konsultasi Lanjut ke FKTP:**\n   Sangat disarankan untuk melakukan konsultasi rutin dengan dokter di **Puskesmas Kelurahan Sukolilo** untuk evaluasi lebih lanjut.",
            "id": "msg_010",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1, minutes=15)).isoformat(),
            "author": "execution_agent",
        },
    ]
    
    # Chat Room 2: Konsultasi Batuk
    room_2_id = "room_002"
    room_2 = {
        "id": room_2_id,
        "userId": user_id_1,
        "sessionId": "session_002",
        "createdAt": (datetime.now() - timedelta(days=5)).isoformat(),
        "lastMessageAt": (datetime.now() - timedelta(days=4, hours=3)).isoformat(),
        "title": "Konsultasi Batuk dan Demam",
        "patientName": "Sasmito",
        "isArchived": True,
    }
    chat_rooms_db[room_2_id] = room_2
    chat_messages_db[room_2_id] = [
        {
            "type": "agent",
            "content": "Halo! Saya adalah Smart Triage Agent. Saya akan membantu Anda dalam proses triase medis. Saya sudah mencatat lokasi Anda di Jawa Barat. Untuk siapa Anda menanyakan?",
            "id": "msg_011",
            "timestamp": (datetime.now() - timedelta(days=5, hours=2)).isoformat(),
            "author": "root_agent",
        },
        {
            "type": "human",
            "content": "Untuk saya sendiri",
            "id": "msg_012",
            "timestamp": (datetime.now() - timedelta(days=5, hours=1, minutes=55)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Baik, saya mengerti. Bisakah Anda ceritakan keluhan yang Anda alami?",
            "id": "msg_013",
            "timestamp": (datetime.now() - timedelta(days=5, hours=1, minutes=50)).isoformat(),
            "author": "interview_agent",
        },
        {
            "type": "human",
            "content": "Saya batuk kering dan demam ringan sudah 3 hari",
            "id": "msg_014",
            "timestamp": (datetime.now() - timedelta(days=5, hours=1, minutes=45)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Terima kasih, saya mencatat batuk kering dan demam ringan selama 3 hari. Untuk memahami lebih baik:\n1. Berapa suhu tubuh Anda saat ini?\n2. Apakah ada sesak napas?\n3. Apakah ada gejala lain seperti sakit tenggorokan atau pilek?",
            "id": "msg_015",
            "timestamp": (datetime.now() - timedelta(days=5, hours=1, minutes=40)).isoformat(),
            "author": "interview_agent",
        },
        {
            "type": "human",
            "content": "Suhu 37.8°C, tidak sesak napas, ada sakit tenggorokan ringan",
            "id": "msg_016",
            "timestamp": (datetime.now() - timedelta(days=5, hours=1, minutes=35)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Berdasarkan analisis kondisi Anda, dengan gejala **batuk kering, demam ringan (37.8°C), dan sakit tenggorokan ringan selama 3 hari**, kondisi ini dikategorikan sebagai **Non-Urgen**.\n\n**Tindakan yang telah diambil:**\n1. Saya telah mengambil panduan perawatan mandiri untuk ISPA ringan.\n\n**Instruksi selanjutnya:**\n1. **Ikuti Panduan Perawatan Mandiri:**\n   - Istirahat yang cukup\n   - Minum air putih banyak\n   - Paracetamol 500mg 3x sehari jika demam\n2. **Konsultasi Lanjut ke FKTP jika gejala memburuk.**",
            "id": "msg_017",
            "timestamp": (datetime.now() - timedelta(days=5, hours=1, minutes=30)).isoformat(),
            "author": "execution_agent",
        },
    ]
    
    # Chat Room 3: Konsultasi untuk Anak
    room_3_id = "room_003"
    room_3 = {
        "id": room_3_id,
        "userId": user_id_1,
        "sessionId": "session_003",
        "createdAt": (datetime.now() - timedelta(days=7)).isoformat(),
        "lastMessageAt": (datetime.now() - timedelta(days=6, hours=2)).isoformat(),
        "title": "Konsultasi Sakit Perut Anak",
        "patientName": "Ahmad Rizki",
        "isArchived": True,
    }
    chat_rooms_db[room_3_id] = room_3
    chat_messages_db[room_3_id] = [
        {
            "type": "agent",
            "content": "Halo! Saya adalah Smart Triage Agent. Saya akan membantu Anda dalam proses triase medis. Saya sudah mencatat lokasi Anda di Jawa Barat. Untuk siapa Anda menanyakan?",
            "id": "msg_018",
            "timestamp": (datetime.now() - timedelta(days=7, hours=2)).isoformat(),
            "author": "root_agent",
        },
        {
            "type": "human",
            "content": "Untuk anak saya, Ahmad Rizki",
            "id": "msg_019",
            "timestamp": (datetime.now() - timedelta(days=7, hours=1, minutes=55)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Baik, saya mengerti. Bisakah Anda ceritakan keluhan yang dialami oleh Ahmad Rizki?",
            "id": "msg_020",
            "timestamp": (datetime.now() - timedelta(days=7, hours=1, minutes=50)).isoformat(),
            "author": "interview_agent",
        },
        {
            "type": "human",
            "content": "Anak saya mengeluh sakit perut di bagian kanan bawah, mual dan tidak nafsu makan sejak pagi",
            "id": "msg_021",
            "timestamp": (datetime.now() - timedelta(days=7, hours=1, minutes=45)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Terima kasih, saya mencatat Ahmad Rizki mengeluh sakit perut kanan bawah dengan mual dan tidak nafsu makan. Untuk memahami lebih baik:\n1. Berapa lama gejala ini muncul?\n2. Apakah ada demam?\n3. Apakah ada muntah?",
            "id": "msg_022",
            "timestamp": (datetime.now() - timedelta(days=7, hours=1, minutes=40)).isoformat(),
            "author": "interview_agent",
        },
        {
            "type": "human",
            "content": "Sudah 6 jam, ada demam 38.2°C, belum muntah",
            "id": "msg_023",
            "timestamp": (datetime.now() - timedelta(days=7, hours=1, minutes=35)).isoformat(),
        },
        {
            "type": "agent",
            "content": "Berdasarkan analisis kondisi Ahmad Rizki, dengan gejala **sakit perut kanan bawah, demam 38.2°C, dan mual selama 6 jam**, kondisi ini dikategorikan sebagai **Mendesak**.\n\n**Kecurigaan:** Apendisitis akut. Perlu evaluasi lebih lanjut di faskes dengan fasilitas bedah.\n\n**Tindakan yang telah diambil:**\n1. Saya telah menghubungi layanan darurat.\n2. Saya telah mengidentifikasi fasilitas kesehatan terdekat dengan fasilitas bedah.\n\n**Instruksi selanjutnya:**\n1. **Segera bawa ke rumah sakit** untuk evaluasi bedah.\n2. **Jangan beri makan atau minum** (NPO) sampai dievaluasi dokter.\n3. **Observasi ketat** gejala anak.",
            "id": "msg_024",
            "timestamp": (datetime.now() - timedelta(days=7, hours=1, minutes=30)).isoformat(),
            "author": "execution_agent",
        },
    ]
    
    logger.info(f"Seeded {len(chat_rooms_db)} chat rooms with messages")


# Initialize seed data on startup
seed_chat_data()


@app.get("/api/chat-rooms")
async def get_chat_rooms(user_id: str = Query(..., alias="userId")):
    """
    Get all chat rooms for a user.
    Accepts userId as query parameter (camelCase to match frontend).
    """
    user_rooms = [
        room for room in chat_rooms_db.values() if room.get("userId") == user_id
    ]
    # Sort by last message time
    user_rooms.sort(key=lambda x: x.get("lastMessageAt", ""), reverse=True)
    return user_rooms


@app.get("/api/chat-rooms/{room_id}/messages")
async def get_room_messages(room_id: str):
    """
    Get all messages for a specific chat room.
    """
    messages = chat_messages_db.get(room_id, [])
    return messages


@app.post("/api/chat-rooms/{room_id}/messages")
async def save_chat_message(room_id: str, message: dict):
    """
    Save a message to a chat room.
    This allows real-time saving of messages as they're sent/received.
    """
    if room_id not in chat_messages_db:
        chat_messages_db[room_id] = []
    
    # Add message to the room's message list
    chat_messages_db[room_id].append(message)
    
    # Update room's lastMessageAt timestamp
    if room_id in chat_rooms_db:
        chat_rooms_db[room_id]["lastMessageAt"] = datetime.now().isoformat()
    
    return {"success": True, "messageId": message.get("id")}


@app.post("/api/chat-rooms/{room_id}/messages/batch")
async def save_chat_messages_batch(room_id: str, messages: list[dict]):
    """
    Save multiple messages to a chat room at once.
    Useful for restoring chat history.
    """
    if room_id not in chat_messages_db:
        chat_messages_db[room_id] = []
    
    # Replace all messages (for restoration)
    chat_messages_db[room_id] = messages
    
    # Update room's lastMessageAt timestamp
    if room_id in chat_rooms_db and messages:
        last_message = max(messages, key=lambda m: m.get("timestamp", ""))
        chat_rooms_db[room_id]["lastMessageAt"] = last_message.get("timestamp", datetime.now().isoformat())
    
    return {"success": True, "count": len(messages)}


@app.post("/api/chat-rooms")
async def create_chat_room(user_id: str = Query(..., alias="userId"), title: str = Query(None, alias="title")):
    """
    Create a new chat room.
    Accepts userId as query parameter (camelCase to match frontend).
    """
    import time
    room_id = f"room_{int(time.time() * 1000)}"
    room = {
        "id": room_id,
        "userId": user_id,
        "sessionId": f"session_{int(time.time() * 1000)}",
        "createdAt": datetime.now().isoformat(),
        "lastMessageAt": datetime.now().isoformat(),
        "title": title or "Konsultasi Medis",
        "isArchived": False,  # New rooms are not archived
    }
    chat_rooms_db[room_id] = room
    chat_messages_db[room_id] = []
    return room


# ========================================
# Doctor API Endpoints
# ========================================

@app.get("/api/doctor/patients")
async def get_patients():
    """
    Get list of all patients (for doctor view).
    MOCK IMPLEMENTATION - In production, query from database.
    """
    # Mock data - in production, query from database
    patients = [
        {
            "id": "patient_001",
            "name": "Sasmito",
            "nik": "3201234567890123",
            "age": 35,
            "gender": "Laki-laki",
            "lastVisit": "2025-01-16T10:30:00",
        },
        {
            "id": "patient_002",
            "name": "Siti Nurhaliza",
            "nik": "3201234567890124",
            "age": 32,
            "gender": "Perempuan",
            "lastVisit": "2025-01-15T14:20:00",
        },
        {
            "id": "patient_003",
            "name": "Ahmad Rizki",
            "nik": "3201234567890125",
            "age": 8,
            "gender": "Laki-laki",
            "lastVisit": "2025-01-14T09:15:00",
        },
        {
            "id": "patient_004",
            "name": "Putri",
            "nik": "3201234567890126",
            "age": 5,
            "gender": "Perempuan",
            "lastVisit": "2025-01-13T11:45:00",
        },
        {
            "id": "patient_005",
            "name": "Bambang Sutrisno",
            "nik": "3201234567890127",
            "age": 65,
            "gender": "Laki-laki",
            "lastVisit": "2025-01-12T16:20:00",
        },
    ]
    return patients


@app.get("/api/doctor/patients/{patient_id}/soap")
async def get_patient_soap(patient_id: str):
    """
    Get SOAP notes for a specific patient.
    MOCK IMPLEMENTATION - In production, query from database.
    """
    # Mock data - in production, query from database
    # This should query from session state where medical_documentation is stored
    
    # Different SOAP notes based on patient_id
    soap_data = {
        "patient_001": [
            {
                "id": "soap_001",
                "patientId": patient_id,
                "patientName": "Sasmito",
                "createdAt": "2025-01-16T10:30:00",
                "subjective": "Pasien mengeluh pusing berputar yang sangat mengganggu aktivitas selama 3 hari. Disertai telinga berdengung dan pusing bertambah saat bergerak. Riwayat Hipertensi dan Diabetes Mellitus Tipe 2.",
                "objective": "Gejala: pusing berputar, telinga berdengung\nDurasi: 3 hari\nTingkat keparahan: Sangat mengganggu aktivitas\nTriage Level: Gawat Darurat\nTekanan darah: 140/90 mmHg\nNadi: 78 bpm",
                "assessment": "Berdasarkan analisis kondisi Anda, dengan gejala **pusing berputar** yang **sangat mengganggu aktivitas** selama 3 hari, disertai **telinga berdengung** dan **pusing bertambah saat bergerak**, kondisi ini dikategorikan sebagai **Gawat Darurat**.\n\n**Justifikasi berdasarkan Pedoman BPJS Kriteria Gawat Darurat dan PPK Kemenkes:**\n\nBerdasarkan **Pedoman BPJS Kriteria Gawat Darurat**, kondisi Anda memenuhi kriteria gawat darurat karena termasuk dalam kategori **\"VIII THT, 13 Vertigo (berat)\"**. Tingkat keparahan gejala Anda yang \"sangat mengganggu aktivitas\" mendukung klasifikasi vertigo ini sebagai \"berat\".\n\n**Pedoman Pelayanan Primer Kesehatan (PPK) Kemenkes** juga menjelaskan bahwa gejala yang Anda alami, yaitu \"pusing berputar\", \"pusing bertambah saat bergerak\", dan \"telinga berdengung\", sangat sesuai dengan deskripsi **Vertigo Vestibular Perifer**. Kondisi ini ditandai dengan sensasi berputar yang timbul episodik, diprovokasi oleh gerakan kepala, dan bisa disertai gangguan pendengaran berupa tinitus. Meskipun PPK Kemenkes membahas penanganan vertigo di layanan primer, kriteria BPJS secara spesifik menggolongkan vertigo yang berat sebagai gawat darurat. Riwayat medis Anda dengan **Hipertensi** dan **Diabetes Mellitus Tipe 2** juga memerlukan evaluasi yang cermat untuk menyingkirkan penyebab vertigo yang lebih serius atau komplikasi.",
                "plan": "**Tindakan yang telah diambil:**\n\nKami telah mengaktifkan layanan darurat untuk Anda.\n\n1. **Fasilitas Kesehatan Terdekat:** Kami telah mengidentifikasi **RSUD Dr. Soetomo** sebagai fasilitas kesehatan terdekat dengan IGD yang tersedia di Jawa Barat.\n\n2. **Panggilan Darurat:** Ambulans dengan ID **AMB-5483** telah diberangkatkan menuju lokasi Anda dan diperkirakan tiba dalam **16 menit** (sekitar pukul 14:38 WIB). Status ambulans saat ini adalah \"Dalam perjalanan ke lokasi pasien\".\n\n3. **Notifikasi Rumah Sakit:** IGD RSUD Dr. Soetomo di Jl. Mayjen Prof. Dr. Moestopo No. 6-8, Surabaya, telah diberitahu dan siap menerima Anda.\n\n**Instruksi selanjutnya:**\n\n1. **Tetap tenang** dan jangan melakukan aktivitas berat.\n\n2. **Segera menuju IGD RSUD Dr. Soetomo** setelah ambulans tiba. Sesuai prosedur BPJS, kondisi gawat darurat tidak memerlukan surat rujukan.\n\n3. Jika ambulans belum tiba dalam 20 menit, segera hubungi **119**.\n\n4. Setibanya di RSUD Dr. Soetomo, langsung ke IGD dan beri tahu bahwa Anda telah didaftarkan melalui sistem triase Mobile JKN.\n\n5. Anda dapat melacak posisi ambulans melalui tautan ini: https://mobile-jkn.bpjs-kesehatan.go.id/track/AMB-5483.\n\n6. Untuk informasi lebih lanjut atau jika ada perubahan kondisi, Anda bisa menghubungi rumah sakit di nomor +62-31-XXXX-XXXX.",
                "triageLevel": "Gawat Darurat",
                "icdCodes": [
                    {"code": "H81.9", "description": "Disorder of vestibular function, unspecified"},
                ],
            },
        ],
        "patient_002": [
            {
                "id": "soap_002",
                "patientId": patient_id,
                "patientName": "Siti Nurhaliza",
                "createdAt": "2025-01-15T14:20:00",
                "subjective": "Pasien mengeluh batuk kering disertai demam ringan selama 3 hari. Tidak ada sesak napas.",
                "objective": "Gejala: batuk kering, demam\nDurasi: 3 hari\nSuhu tubuh: 37.8°C\nTriage Level: Non-Urgen\nSpO2: 98%",
                "assessment": "Berdasarkan analisis kondisi pasien, dengan gejala **batuk kering disertai demam ringan** (37.8°C) selama 3 hari, tanpa sesak napas dan dengan SpO2 normal (98%), kondisi ini dikategorikan sebagai **Non-Urgen**.\n\n**Justifikasi berdasarkan Pedoman BPJS Kriteria Gawat Darurat dan PPK Kemenkes:**\n\nBerdasarkan **Pedoman BPJS Kriteria Gawat Darurat**, kondisi pasien **tidak memenuhi** kriteria gawat darurat karena:\n- Tidak ada \"**Sesak napas berat**\" atau gangguan jalan napas yang mengancam nyawa.\n- Demam ringan (37.8°C) tidak termasuk \"**Demam tinggi**\" yang memerlukan penanganan darurat.\n- Tidak ada tanda-tanda \"**Gangguan kesadaran**\" atau komplikasi serius.\n- SpO2 normal (98%) menunjukkan fungsi pernapasan masih baik.\n\n**Pedoman Pelayanan Primer Kesehatan (PPK) Kemenkes** menjelaskan bahwa **Infeksi Saluran Pernapasan Atas (ISPA) ringan** dengan gejala stabil seperti batuk kering, demam ringan, tanpa sesak napas, dan tanpa tanda-tanda komplikasi dapat ditangani di FKTP. Menurut PPK Kemenkes, ISPA ringan yang tidak disertai komplikasi (seperti pneumonia, dehidrasi berat, atau gangguan kesadaran) merupakan kondisi yang dapat ditangani dengan perawatan suportif, istirahat, dan pengobatan simtomatik di tingkat pelayanan primer.\n\nKondisi ini kemungkinan besar disebabkan oleh **viral infection** yang dapat sembuh sendiri dengan perawatan suportif dan tidak memerlukan antibiotik kecuali ada indikasi infeksi bakteri sekunder.",
                "plan": "Istirahat yang cukup, minum air putih banyak. Paracetamol 500mg 3x sehari jika demam. Kontrol jika gejala memburuk.",
                "triageLevel": "Non-Urgen",
                "icdCodes": [
                    {"code": "J06.9", "description": "Acute upper respiratory infection, unspecified"},
                ],
            },
        ],
        "patient_003": [
            {
                "id": "soap_003",
                "patientId": patient_id,
                "patientName": "Ahmad Rizki",
                "createdAt": "2025-01-14T09:15:00",
                "subjective": "Anak mengeluh sakit perut di bagian kanan bawah. Mual dan tidak nafsu makan sejak pagi.",
                "objective": "Gejala: nyeri perut kanan bawah\nDurasi: 6 jam\nTriage Level: Mendesak\nNyeri tekan di McBurney point\nSuhu: 38.2°C",
                "assessment": "Berdasarkan analisis kondisi pasien, dengan gejala **nyeri perut kanan bawah** yang **sangat mengganggu aktivitas** selama 6 jam, disertai **mual**, **tidak nafsu makan**, dan **demam** (38.2°C), serta ditemukan **nyeri tekan di McBurney point**, kondisi ini dikategorikan sebagai **Mendesak**.\n\n**Justifikasi berdasarkan Pedoman BPJS Kriteria Gawat Darurat dan PPK Kemenkes:**\n\nBerdasarkan **Pedoman BPJS Kriteria Gawat Darurat**, kondisi pasien memerlukan penanganan **mendesak** karena:\n- Gejala menunjukkan **kecurigaan apendisitis akut** yang dapat berkembang menjadi komplikasi serius (perforasi, peritonitis) jika tidak ditangani dalam 24-48 jam.\n- Nyeri perut akut dengan tanda-tanda peritonitis lokal (nyeri tekan di McBurney point) memerlukan evaluasi bedah segera.\n- Demam (38.2°C) dan gejala sistemik (mual, tidak nafsu makan) menunjukkan proses inflamasi aktif yang dapat memburuk.\n\n**Pedoman Pelayanan Primer Kesehatan (PPK) Kemenkes** menjelaskan bahwa **nyeri perut akut** dengan karakteristik seperti yang dialami pasien (lokalisasi di kuadran kanan bawah, nyeri tekan lokal, disertai demam dan gejala sistemik) sangat sesuai dengan deskripsi apendisitis akut. Menurut PPK Kemenkes, kondisi ini memerlukan **rujukan segera** ke faskes dengan fasilitas bedah untuk evaluasi dan penanganan lebih lanjut. Meskipun tidak termasuk dalam kategori \"gawat darurat\" yang mengancam nyawa secara langsung, kondisi ini diklasifikasikan sebagai \"mendesak\" karena memerlukan penanganan dalam 24-48 jam untuk mencegah komplikasi yang dapat mengancam nyawa.\n\nKondisi ini **tidak dapat ditangani di FKTP** karena memerlukan evaluasi bedah dan kemungkinan intervensi bedah yang tidak tersedia di tingkat pelayanan primer.",
                "plan": "Rujuk ke rumah sakit untuk evaluasi bedah. NPO (nothing per oral). Observasi ketat.",
                "triageLevel": "Mendesak",
                "icdCodes": [
                    {"code": "K35.9", "description": "Acute appendicitis, unspecified"},
                ],
            },
        ],
    }
    
    # Return data for specific patient or default
    return soap_data.get(patient_id, [
        {
            "id": f"soap_{patient_id}",
            "patientId": patient_id,
            "patientName": "Pasien",
            "createdAt": datetime.now().isoformat(),
            "subjective": "Data tidak tersedia.",
            "objective": "Data tidak tersedia.",
            "assessment": "Data tidak tersedia.",
            "plan": "Data tidak tersedia.",
            "triageLevel": "Tidak tersedia",
            "icdCodes": [],
        },
    ])


@app.get("/api/doctor/patients/{patient_id}/history")
async def get_patient_history(patient_id: str):
    """
    Get medical history for a specific patient.
    MOCK IMPLEMENTATION - In production, query from JKN/BPJS API.
    """
    # Mock data - in production, query from JKN/BPJS API
    from medical_triage_agent.sub_agents.execution_agent.tools.jkn_tools import query_jkn_medical_history
    
    # Different history based on patient_id
    history_data = {
        "patient_001": [
            {
                "visitDate": "2024-12-15T10:00:00",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Hipertensi Esensial",
                "icdCode": "I10",
                "medications": [
                    {"name": "Amlodipine", "dosage": "5mg", "frequency": "1x sehari"},
                    {"name": "Metformin", "dosage": "500mg", "frequency": "2x sehari"},
                ],
                "doctor": "Dr. Budi Santoso, Sp.PD",
            },
            {
                "visitDate": "2024-11-20T14:30:00",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Diabetes Mellitus Tipe 2",
                "icdCode": "E11.9",
                "medications": [
                    {"name": "Metformin", "dosage": "500mg", "frequency": "2x sehari"},
                ],
                "doctor": "Dr. Budi Santoso, Sp.PD",
            },
            {
                "visitDate": "2024-10-10T09:15:00",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Common Cold",
                "icdCode": "J00",
                "medications": [
                    {"name": "Paracetamol", "dosage": "500mg", "frequency": "3x sehari"},
                ],
                "doctor": "Dr. Siti Aisyah",
            },
        ],
        "patient_002": [
            {
                "visitDate": "2024-12-10T11:00:00",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Anemia Defisiensi Besi",
                "icdCode": "D50.9",
                "medications": [
                    {"name": "Ferrous Sulfate", "dosage": "200mg", "frequency": "2x sehari"},
                    {"name": "Vitamin C", "dosage": "500mg", "frequency": "1x sehari"},
                ],
                "doctor": "Dr. Siti Aisyah",
            },
            {
                "visitDate": "2024-11-05T15:20:00",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Upper Respiratory Tract Infection",
                "icdCode": "J06.9",
                "medications": [
                    {"name": "Paracetamol", "dosage": "500mg", "frequency": "3x sehari"},
                    {"name": "Guaifenesin", "dosage": "200mg", "frequency": "3x sehari"},
                ],
                "doctor": "Dr. Budi Santoso, Sp.PD",
            },
        ],
        "patient_003": [
            {
                "visitDate": "2024-12-20T08:30:00",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Acute Gastroenteritis",
                "icdCode": "A09",
                "medications": [
                    {"name": "Oral Rehydration Salt", "dosage": "1 sachet", "frequency": "Sesuai kebutuhan"},
                    {"name": "Probiotics", "dosage": "1 kapsul", "frequency": "2x sehari"},
                ],
                "doctor": "Dr. Siti Aisyah",
            },
        ],
        "patient_004": [
            {
                "visitDate": "2024-12-18T10:15:00",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Atopic Dermatitis",
                "icdCode": "L20.9",
                "medications": [
                    {"name": "Hydrocortisone Cream", "dosage": "1%", "frequency": "2x sehari"},
                    {"name": "Cetirizine", "dosage": "5mg", "frequency": "1x sehari"},
                ],
                "doctor": "Dr. Siti Aisyah",
            },
        ],
        "patient_005": [
            {
                "visitDate": "2024-12-12T13:00:00",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Osteoarthritis",
                "icdCode": "M19.90",
                "medications": [
                    {"name": "Paracetamol", "dosage": "500mg", "frequency": "3x sehari"},
                    {"name": "Glucosamine", "dosage": "500mg", "frequency": "2x sehari"},
                ],
                "doctor": "Dr. Budi Santoso, Sp.PD",
            },
            {
                "visitDate": "2024-11-25T09:45:00",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Hypertension",
                "icdCode": "I10",
                "medications": [
                    {"name": "Amlodipine", "dosage": "5mg", "frequency": "1x sehari"},
                ],
                "doctor": "Dr. Budi Santoso, Sp.PD",
            },
        ],
    }
    
    # Return history for specific patient or try to get from JKN tool
    if patient_id in history_data:
        return history_data[patient_id]
    
    # Fallback: try to get from JKN tool
    try:
        history_json = query_jkn_medical_history(patient_id)
        jkn_data = json.loads(history_json)
        
        formatted_history = []
        for visit in jkn_data.get("recent_visits", []):
            formatted_history.append({
                "visitDate": visit.get("visit_date"),
                "facility": visit.get("facility"),
                "diagnosis": visit.get("diagnosis"),
                "icdCode": visit.get("icd_code"),
                "medications": visit.get("medications", []),
                "doctor": visit.get("doctor"),
            })
        return formatted_history
    except Exception as e:
        logger.warning(f"Could not get history from JKN tool: {e}")
        return []

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
                try:
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
                            
                            # Try to send event, catch RuntimeError if WebSocket is closed
                            await websocket.send_text(json.dumps(event_data, ensure_ascii=False))
                            
                            # Safe logging - handle None text
                            text_preview = event_data.get('text') or ''
                            if text_preview:
                                text_preview = text_preview[:50] + '...' if len(text_preview) > 50 else text_preview
                            logger.debug(f"Sent event: {event.__class__.__name__}, text: {text_preview}")
                        except RuntimeError as e:
                            if "close message has been sent" in str(e) or "Cannot call" in str(e):
                                logger.warning("WebSocket was closed, stopping event stream")
                                break
                            else:
                                logger.error(f"RuntimeError sending event: {e}", exc_info=True)
                                break
                        except Exception as e:
                            logger.error(f"Error sending event: {e}", exc_info=True)
                            # Don't break on other errors, continue trying to send
                except Exception as e:
                    logger.error(f"Error in event stream: {e}", exc_info=True)
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
    # Note: API routes should be matched before this catch-all route
    if (path.startswith("api/") or 
        path.startswith("ws/") or 
        path.startswith("static/") or 
        path.startswith("assets/")):
        # If we reach here, the API route wasn't found
        return {"error": "Not found", "path": path}, 404
    
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

