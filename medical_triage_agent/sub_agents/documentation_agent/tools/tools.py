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
from google.adk.tools import FunctionTool


def format_soap(
    symptoms_data: str,
    triage_result: str,
    execution_result: str,
    conversation_transcript: str = ""
) -> str:
    """
    Memformat dokumentasi medis ke format SOAP (Subjektif, Objektif, Asesmen, Plan).
    
    Args:
        symptoms_data: Data gejala terstruktur dari interview
        triage_result: Hasil triage dari reasoning agent
        execution_result: Hasil eksekusi dari execution agent
        conversation_transcript: Transkrip percakapan (opsional)
        
    Returns:
        JSON string dengan dokumentasi SOAP yang terstruktur
    """
    try:
        symptoms = json.loads(symptoms_data)
        triage = json.loads(triage_result)
        execution = json.loads(execution_result)
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"error": "Invalid input data format"})
    
    # Format SOAP
    soap_document = {
        "S (Subjektif)": {
            "keluhan_utama": symptoms.get("gejala_utama", []),
            "gejala_penyerta": symptoms.get("gejala_penyerta", []),
            "durasi": symptoms.get("durasi", ""),
            "riwayat_medis": symptoms.get("riwayat_medis", []),
            "obat": symptoms.get("obat", []),
            "alergi": symptoms.get("alergi", [])
        },
        "O (Objektif)": {
            "triage_level": triage.get("triage_level", ""),
            "matched_criteria": triage.get("matched_criteria", []),
            "tingkat_keparahan": symptoms.get("tingkat_keparahan", "")
        },
        "A (Asesmen)": {
            "diagnosis_kerja": "Berdasarkan gejala yang dikumpulkan",
            "triage_level": triage.get("triage_level", ""),
            "justifikasi": triage.get("justification", "")
        },
        "P (Plan)": {
            "tindakan": execution.get("action", ""),
            "rencana_tindak_lanjut": execution.get("message", ""),
            "rekomendasi": triage.get("recommendation", "")
        }
    }
    
    return json.dumps(soap_document, ensure_ascii=False, indent=2)


def recommend_icd_code(symptoms_data: str, triage_result: str) -> str:
    """
    Merekomendasikan kode ICD-10/ICD-9 berdasarkan gejala dan triage level.
    
    Args:
        symptoms_data: Data gejala terstruktur
        triage_result: Hasil triage
        
    Returns:
        JSON string dengan rekomendasi kode ICD
    """
    try:
        symptoms = json.loads(symptoms_data)
        triage = json.loads(triage_result)
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"error": "Invalid input data format"})
    
    # TODO: Implementasi mapping gejala ke kode ICD
    # Ini adalah placeholder - perlu database atau API untuk mapping ICD
    
    gejala_utama = symptoms.get("gejala_utama", [])
    recommended_codes = []
    
    # Contoh mapping sederhana (perlu dikembangkan dengan database ICD)
    if any("demam" in str(g).lower() for g in gejala_utama):
        recommended_codes.append({
            "icd10": "R50.9",
            "description": "Demam, tidak ditentukan",
            "confidence": "medium"
        })
    
    if any("sesak" in str(g).lower() or "napas" in str(g).lower() for g in gejala_utama):
        recommended_codes.append({
            "icd10": "R06.0",
            "description": "Dyspnea",
            "confidence": "medium"
        })
    
    result = {
        "recommended_codes": recommended_codes,
        "note": "Kode ICD direkomendasikan berdasarkan gejala. Perlu konfirmasi dokter untuk diagnosis definitif."
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


format_soap_tool = FunctionTool(
    func=format_soap,
)

recommend_icd_code_tool = FunctionTool(
    func=recommend_icd_code,
)

