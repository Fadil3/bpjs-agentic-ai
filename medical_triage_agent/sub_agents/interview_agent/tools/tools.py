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

import json
import os
import re
from pathlib import Path
from google import genai
from google.genai import types
from google.adk.tools import FunctionTool

# Get environment variables
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Path to knowledge PDF
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
BATES_PDF_PATH = KNOWLEDGE_DIR / "Bates_Guide_to_Physical_Examination.pdf"


def extract_symptoms(conversation_transcript: str) -> str:
    """
    Mengekstrak dan strukturkan data gejala dari transkrip percakapan wawancara
    menggunakan Gemini LLM untuk ekstraksi entitas medis.
    
    Args:
        conversation_transcript: Transkrip lengkap percakapan dengan pasien
        
    Returns:
        JSON string yang berisi data gejala terstruktur dengan:
        - gejala_utama: [list gejala utama]
        - gejala_penyerta: [list gejala penyerta]
        - durasi: [durasi dalam format yang jelas]
        - tingkat_keparahan: [deskripsi atau skala]
        - riwayat_medis: [riwayat relevan]
        - obat: [obat yang sedang dikonsumsi]
        - alergi: [alergi jika ada]
    """
    if not conversation_transcript or not conversation_transcript.strip():
        # Return empty structure if transcript is empty
        return json.dumps({
            "gejala_utama": [],
            "gejala_penyerta": [],
            "durasi": "",
            "tingkat_keparahan": "",
            "riwayat_medis": [],
            "obat": [],
            "alergi": []
        }, ensure_ascii=False, indent=2)
    
    # Initialize Gemini client
    client = genai.Client(
        vertexai=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
    )
    
    # Read Bates Guide PDF if available
    bates_pdf_content = None
    if BATES_PDF_PATH.exists():
        try:
            with open(BATES_PDF_PATH, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
                bates_pdf_content = types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type="application/pdf"
                )
                print(f"[INFO] Loaded Bates Guide to Physical Examination PDF: {BATES_PDF_PATH.name}")
        except Exception as e:
            print(f"Warning: Could not read Bates Guide PDF: {e}")
    
    # Build prompt for symptom extraction
    prompt_text = """
Anda adalah ahli ekstraksi informasi medis yang berpengalaman. Tugas Anda adalah 
menganalisis transkrip percakapan wawancara medis dan mengekstrak informasi gejala 
dan medis yang relevan ke dalam format JSON terstruktur.

**Transkrip Percakapan:**
{transcript}

**Instruksi Ekstraksi:**
1. Identifikasi dan ekstrak gejala utama (primary symptoms) yang disebutkan pasien
2. Identifikasi dan ekstrak gejala penyerta (secondary/associated symptoms)
3. Ekstrak durasi gejala (kapan mulai, berapa lama sudah berlangsung)
4. Ekstrak tingkat keparahan gejala (jika disebutkan, bisa berupa skala 1-10 atau deskripsi)
5. Ekstrak riwayat medis yang relevan (penyakit sebelumnya, kondisi kronis)
6. Ekstrak obat-obatan yang sedang dikonsumsi (jika disebutkan)
7. Ekstrak alergi (jika disebutkan)

**Panduan Ekstraksi:**
- Gejala utama: Gejala yang paling dominan atau yang paling mengganggu pasien
- Gejala penyerta: Gejala tambahan yang menyertai gejala utama
- Durasi: Format jelas seperti "3 hari", "sejak pagi", "2 minggu terakhir"
- Tingkat keparahan: Bisa berupa skala numerik (1-10) atau deskripsi (ringan/sedang/berat)
- Riwayat medis: Penyakit sebelumnya, kondisi kronis, operasi sebelumnya yang relevan
- Obat: Nama obat yang sedang dikonsumsi (jika disebutkan)
- Alergi: Alergi terhadap obat, makanan, atau zat tertentu (jika disebutkan)

**Referensi Pemeriksaan Fisik:**
Jika tersedia, gunakan Bates Guide to Physical Examination sebagai referensi untuk 
mengidentifikasi temuan pemeriksaan fisik yang mungkin disebutkan dalam transkrip, 
seperti tanda-tanda vital abnormal, temuan inspeksi, palpasi, atau auskultasi.

**Output Format (JSON):**
{{
    "gejala_utama": ["gejala 1", "gejala 2", ...],
    "gejala_penyerta": ["gejala penyerta 1", "gejala penyerta 2", ...],
    "durasi": "durasi gejala dalam format jelas",
    "tingkat_keparahan": "tingkat keparahan (skala atau deskripsi)",
    "riwayat_medis": ["riwayat 1", "riwayat 2", ...],
    "obat": ["obat 1", "obat 2", ...],
    "alergi": ["alergi 1", "alergi 2", ...]
}}

**Penting:**
- Jika informasi tidak disebutkan dalam transkrip, gunakan array kosong [] atau string kosong ""
- Pastikan semua gejala diekstrak dengan akurat
- Gunakan terminologi medis yang tepat jika disebutkan dalam percakapan
- Jika pasien menyebutkan gejala dalam Bahasa Indonesia sehari-hari, pertahankan dalam format aslinya
- Output HARUS valid JSON, tidak ada komentar atau teks tambahan di luar JSON
""".format(transcript=conversation_transcript)
    
    # Prepare content parts
    parts = [types.Part.from_text(text=prompt_text)]
    if bates_pdf_content:
        parts.append(bates_pdf_content)
    
    contents = [
        types.Content(
            role="user",
            parts=parts
        )
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=0.1,  # Low temperature untuk konsistensi ekstraksi
        top_p=0.95,
        max_output_tokens=4096,
        response_mime_type="application/json",  # Force JSON output
    )
    
    try:
        # Generate response using Gemini
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
        
        # Try to parse as JSON
        try:
            result = json.loads(response_text)
            
            # Validate and ensure all required fields exist
            validated_result = {
                "gejala_utama": result.get("gejala_utama", []),
                "gejala_penyerta": result.get("gejala_penyerta", []),
                "durasi": result.get("durasi", ""),
                "tingkat_keparahan": result.get("tingkat_keparahan", ""),
                "riwayat_medis": result.get("riwayat_medis", []),
                "obat": result.get("obat", []),
                "alergi": result.get("alergi", [])
            }
            
            # Ensure lists are actually lists
            for key in ["gejala_utama", "gejala_penyerta", "riwayat_medis", "obat", "alergi"]:
                if not isinstance(validated_result[key], list):
                    validated_result[key] = []
            
            # Ensure strings are actually strings
            for key in ["durasi", "tingkat_keparahan"]:
                if not isinstance(validated_result[key], str):
                    validated_result[key] = str(validated_result[key]) if validated_result[key] else ""
            
            return json.dumps(validated_result, ensure_ascii=False, indent=2)
            
        except json.JSONDecodeError:
            # If not JSON, try to extract JSON from response
            # Sometimes Gemini includes markdown formatting
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    # Validate same as above
                    validated_result = {
                        "gejala_utama": result.get("gejala_utama", []),
                        "gejala_penyerta": result.get("gejala_penyerta", []),
                        "durasi": result.get("durasi", ""),
                        "tingkat_keparahan": result.get("tingkat_keparahan", ""),
                        "riwayat_medis": result.get("riwayat_medis", []),
                        "obat": result.get("obat", []),
                        "alergi": result.get("alergi", [])
                    }
                    return json.dumps(validated_result, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    pass
            
            # Fallback: return structured response with extracted info in justification
            return json.dumps({
                "gejala_utama": [],
                "gejala_penyerta": [],
                "durasi": "",
                "tingkat_keparahan": "",
                "riwayat_medis": [],
                "obat": [],
                "alergi": [],
                "note": "Ekstraksi otomatis gagal. Mohon review manual transkrip berikut: " + response_text[:200]
            }, ensure_ascii=False, indent=2)
            
    except Exception as e:
        # Error handling: return empty structure with error note
        return json.dumps({
            "gejala_utama": [],
            "gejala_penyerta": [],
            "durasi": "",
            "tingkat_keparahan": "",
            "riwayat_medis": [],
            "obat": [],
            "alergi": [],
            "error": f"Error extracting symptoms: {str(e)}",
            "note": "Terjadi error dalam ekstraksi gejala. Mohon review manual transkrip percakapan."
        }, ensure_ascii=False, indent=2)


def query_interview_guide(question: str) -> str:
    """
    Mengquery Bates Guide to Physical Examination untuk mendapatkan panduan 
    teknik wawancara, pertanyaan yang tepat, atau informasi tentang pemeriksaan fisik.
    
    Tool ini membantu agent untuk:
    - Mempelajari teknik wawancara medis yang efektif
    - Mengetahui pertanyaan yang tepat untuk kondisi tertentu
    - Memahami cara mengeksplorasi gejala lebih dalam
    - Mempelajari cara melakukan anamnesis yang komprehensif
    
    Args:
        question: Pertanyaan atau topik yang ingin dipelajari dari Bates Guide
                 Contoh: "bagaimana cara menanyakan riwayat nyeri dada",
                        "teknik wawancara untuk gejala pernapasan",
                        "pertanyaan untuk mengeksplorasi gejala demam"
        
    Returns:
        String yang berisi informasi relevan dari Bates Guide
    """
    if not question or not question.strip():
        return "Silakan berikan pertanyaan atau topik yang ingin dipelajari dari Bates Guide."
    
    # Initialize Gemini client
    client = genai.Client(
        vertexai=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
    )
    
    # Read Bates Guide PDF if available
    bates_pdf_content = None
    if BATES_PDF_PATH.exists():
        try:
            with open(BATES_PDF_PATH, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
                bates_pdf_content = types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type="application/pdf"
                )
                print(f"[INFO] Loaded Bates Guide for query: {BATES_PDF_PATH.name}")
        except Exception as e:
            print(f"Warning: Could not read Bates Guide PDF: {e}")
            return f"Error: Tidak dapat membaca Bates Guide PDF: {str(e)}"
    else:
        return "Error: Bates Guide PDF tidak ditemukan."
    
    # Build prompt for querying the guide
    prompt_text = f"""
Anda adalah asisten yang membantu mengekstrak informasi dari Bates Guide to Physical Examination.

**Pertanyaan/Topik:**
{question}

**Instruksi:**
1. Cari informasi yang relevan dengan pertanyaan/topik di atas dalam Bates Guide
2. Fokus pada:
   - Teknik wawancara medis (interview techniques)
   - Pertanyaan yang tepat untuk kondisi/gejala tertentu
   - Cara mengeksplorasi gejala lebih dalam
   - Panduan anamnesis yang komprehensif
   - Cara menanyakan riwayat medis yang efektif
3. Berikan ringkasan yang jelas dan praktis dalam Bahasa Indonesia
4. Jika informasi tidak ditemukan, beri tahu bahwa informasi tidak tersedia dalam guide

**Output:**
Berikan ringkasan informasi yang relevan dalam format yang mudah dipahami untuk digunakan dalam wawancara medis.
"""
    
    # Prepare content parts
    parts = [types.Part.from_text(text=prompt_text)]
    if bates_pdf_content:
        parts.append(bates_pdf_content)
    
    contents = [
        types.Content(
            role="user",
            parts=parts
        )
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,  # Low temperature untuk konsistensi
        top_p=0.95,
        max_output_tokens=2048,
    )
    
    try:
        # Generate response
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
        
        return response_text if response_text else "Tidak ada informasi yang ditemukan untuk pertanyaan ini."
        
    except Exception as e:
        return f"Error saat mengquery Bates Guide: {str(e)}"


extract_symptoms_tool = FunctionTool(
    func=extract_symptoms,
)

query_interview_guide_tool = FunctionTool(
    func=query_interview_guide,
)

