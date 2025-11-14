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
from pathlib import Path
from google import genai
from google.genai import types
from google.adk.tools import FunctionTool

# Get environment variables
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Path to knowledge PDFs
# Note: Folder name is "knowlegde" (typo in original, but keeping it as is)
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowlegde"
BPJS_PDF_PATH = KNOWLEDGE_DIR / "Pedoman-BPJS-Kriteria-Gawat-Darurat.pdf"
PPK_KEMENKES_PDF_PATH = KNOWLEDGE_DIR / "ppk-kemenkes.pdf"


def check_bpjs_criteria(symptoms_data: str) -> str:
    """
    Memetakan gejala ke Kriteria Gawat Darurat BPJS menggunakan Pedoman BPJS 
    dan menentukan triage level (Gawat Darurat / Mendesak / Non-Urgen).
    
    Args:
        symptoms_data: JSON string yang berisi data gejala terstruktur
        
    Returns:
        JSON string dengan triage level, kriteria yang terpenuhi, dan justifikasi
    """
    # Debug: Log raw input
    print(f"[DEBUG] check_bpjs_criteria received: {symptoms_data[:200]}...")
    
    try:
        symptoms = json.loads(symptoms_data)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse symptoms_data as JSON: {e}")
        print(f"[ERROR] Raw data: {symptoms_data[:500]}")
        return json.dumps({
            "error": "Invalid symptoms data format",
            "triage_level": "Mendesak",  # Default to Mendesak if we can't parse
            "matched_criteria": [],
            "justification": "Terjadi error dalam parsing data gejala. Mohon evaluasi manual.",
            "recommendation": "Konsultasi dengan dokter untuk evaluasi lebih lanjut"
        }, ensure_ascii=False, indent=2)
    
    # Initialize Gemini client
    client = genai.Client(
        vertexai=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
    )
    
    # Read knowledge PDFs if available
    pdf_parts = []
    
    # Load BPJS criteria PDF
    if BPJS_PDF_PATH.exists():
        try:
            with open(BPJS_PDF_PATH, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
                pdf_parts.append(types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type="application/pdf"
                ))
                print(f"[INFO] Loaded BPJS criteria PDF: {BPJS_PDF_PATH.name}")
        except Exception as e:
            print(f"Warning: Could not read BPJS PDF: {e}")
    
    # Load PPK Kemenkes PDF
    if PPK_KEMENKES_PDF_PATH.exists():
        try:
            with open(PPK_KEMENKES_PDF_PATH, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
                pdf_parts.append(types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type="application/pdf"
                ))
                print(f"[INFO] Loaded PPK Kemenkes PDF: {PPK_KEMENKES_PDF_PATH.name}")
        except Exception as e:
            print(f"Warning: Could not read PPK Kemenkes PDF: {e}")
    
    # Prepare symptoms summary
    gejala_utama = symptoms.get("gejala_utama", [])
    gejala_penyerta = symptoms.get("gejala_penyerta", [])
    durasi = symptoms.get("durasi", "")
    tingkat_keparahan = symptoms.get("tingkat_keparahan", "")
    riwayat_medis = symptoms.get("riwayat_medis", [])
    obat = symptoms.get("obat", [])
    
    # Check if symptoms are actually empty or if there's an issue
    all_symptoms_empty = (
        not gejala_utama and 
        not gejala_penyerta and 
        not durasi and 
        not tingkat_keparahan
    )
    
    # If symptoms appear empty but we have raw data, include the raw JSON for context
    raw_symptoms_json = json.dumps(symptoms, ensure_ascii=False, indent=2)
    
    symptoms_summary = f"""
Gejala Utama: {', '.join(gejala_utama) if gejala_utama else 'Tidak disebutkan secara eksplisit'}
Gejala Penyerta: {', '.join(gejala_penyerta) if gejala_penyerta else 'Tidak disebutkan secara eksplisit'}
Durasi: {durasi if durasi else 'Tidak disebutkan secara eksplisit'}
Tingkat Keparahan: {tingkat_keparahan if tingkat_keparahan else 'Tidak disebutkan secara eksplisit'}
Riwayat Medis: {', '.join(riwayat_medis) if riwayat_medis else 'Tidak disebutkan'}
Obat yang Dikonsumsi: {', '.join(obat) if obat else 'Tidak disebutkan'}

**Data Mentah (untuk referensi jika gejala tidak terdeteksi):**
{raw_symptoms_json}
"""
    
    # Build prompt
    knowledge_sources = []
    if BPJS_PDF_PATH.exists():
        knowledge_sources.append("Pedoman BPJS Kriteria Gawat Darurat")
    if PPK_KEMENKES_PDF_PATH.exists():
        knowledge_sources.append("Pedoman Pelayanan Primer Kesehatan (PPK) Kemenkes")
    
    knowledge_ref = " dan ".join(knowledge_sources) if knowledge_sources else "Pedoman BPJS"
    
    prompt_text = f"""
Anda adalah ahli triase medis yang berpengalaman. Tugas Anda adalah menganalisis 
gejala pasien dan memetakannya ke Kriteria Gawat Darurat BPJS berdasarkan 
{knowledge_ref} yang tersedia dalam knowledge base.

**PENTING - INSTRUKSI KRITIS:**
1. **SELALU ANALISIS DATA MENTAH**: Jika gejala utama/penyerta tampak kosong, PERIKSA data mentah (raw data) di bawah. 
   Gejala mungkin ada di data mentah meskipun tidak terstruktur dengan benar.
2. **JANGAN MENGASUMSIKAN TIDAK ADA GEJALA**: Jika gejala tidak terdeteksi di struktur, cari di data mentah atau 
   gunakan informasi durasi, tingkat keparahan, atau riwayat medis untuk inferensi.
3. Analisis gejala yang diberikan dengan cermat - termasuk data mentah jika tersedia
4. Bandingkan dengan kriteria dalam {knowledge_ref}
5. Tentukan triage level: "Gawat Darurat", "Mendesak", atau "Non-Urgen"
6. Sebutkan kriteria spesifik dari {knowledge_ref} yang terpenuhi
7. Berikan justifikasi yang jelas dan dapat diaudit dengan referensi ke dokumen yang tersedia

**Gejala Pasien:**
{symptoms_summary}

**Contoh Analisis:**
- Jika data menunjukkan "demam 40 derajat, mual, muntah selama 4 hari" → Ini adalah gejala yang jelas memerlukan evaluasi
- Jika durasi disebutkan (misalnya "4 hari") tetapi gejala utama kosong → Gunakan durasi dan konteks untuk inferensi
- Jika tingkat keparahan disebutkan → Gunakan sebagai indikator penting

**Output Format (JSON):**
{{
    "triage_level": "Gawat Darurat" | "Mendesak" | "Non-Urgen",
    "matched_criteria": ["kriteria spesifik dari {knowledge_ref}"],
    "justification": "Penjelasan detail mengapa level ini dipilih, dengan referensi ke {knowledge_ref}. Jika gejala tidak terstruktur dengan benar, jelaskan bagaimana Anda menginterpretasikan data yang tersedia.",
    "recommendation": "Rekomendasi tindakan selanjutnya"
}}

**Penting:**
- Jika gejala mengancam nyawa atau memerlukan penanganan segera (< 1 jam), klasifikasikan sebagai "Gawat Darurat"
- Jika gejala memerlukan penanganan dalam 24-48 jam, klasifikasikan sebagai "Mendesak"
- Jika gejala ringan dan stabil, klasifikasikan sebagai "Non-Urgen"
- **JANGAN PERNAH mengatakan "tidak ada gejala" jika ada informasi durasi, tingkat keparahan, atau data mentah yang menunjukkan gejala**
- Selalu referensikan ke {knowledge_ref} dalam justifikasi
- Jika ragu antara dua level, pilih level yang lebih tinggi (lebih aman)
- Gunakan Pedoman PPK Kemenkes untuk konteks pelayanan primer kesehatan dan Pedoman BPJS untuk kriteria gawat darurat
"""
    
    # Prepare content parts
    parts = [types.Part.from_text(text=prompt_text)]
    # Add all available PDF knowledge sources
    parts.extend(pdf_parts)
    
    contents = [
        types.Content(
            role="user",
            parts=parts
        )
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=0.1,  # Low temperature untuk konsistensi
        top_p=0.95,
        max_output_tokens=8192,
        response_mime_type="application/json",  # Force JSON output
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
        
        # Try to parse as JSON
        try:
            result = json.loads(response_text)
            # Ensure required fields
            if "triage_level" not in result:
                result["triage_level"] = "Non-Urgen"
            if "matched_criteria" not in result:
                result["matched_criteria"] = []
            if "justification" not in result:
                result["justification"] = "Analisis berdasarkan gejala yang dikumpulkan"
            if "recommendation" not in result:
                result["recommendation"] = "Ikuti rekomendasi berdasarkan triage level"
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            # If not JSON, try to extract JSON from response
            # Sometimes Gemini includes markdown formatting
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                # Fallback: return structured response
                return json.dumps({
                    "triage_level": "Non-Urgen",
                    "matched_criteria": [],
                    "justification": response_text,
                    "recommendation": "Konsultasi dengan dokter untuk evaluasi lebih lanjut"
                }, ensure_ascii=False, indent=2)
                
    except Exception as e:
        return json.dumps({
            "error": f"Error analyzing criteria: {str(e)}",
            "triage_level": "Non-Urgen",
            "matched_criteria": [],
            "justification": "Terjadi error dalam analisis. Mohon konsultasi dengan dokter."
        }, ensure_ascii=False, indent=2)


check_bpjs_criteria_tool = FunctionTool(
    func=check_bpjs_criteria,
)

