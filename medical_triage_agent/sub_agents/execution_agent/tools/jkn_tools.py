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
JKN/BPJS Integration Tools for Medical Triage Agent.

These tools simulate integration with JKN/BPJS system:
- Query registered FKTP (Fasilitas Kesehatan Tingkat Pertama)
- Query nearest healthcare facilities based on location
- Query patient medical history from JKN
"""

import json
from typing import Optional, List, Dict
from google.adk.tools import FunctionTool


def query_fktp_registered(patient_id: str, location: Optional[str] = None) -> str:
    """
    Query FKTP (Fasilitas Kesehatan Tingkat Pertama) terdaftar pasien di JKN/BPJS.
    
    MOCK IMPLEMENTATION untuk Hackathon - Simulasi query FKTP terdaftar.
    Dalam implementasi produksi, ini akan terintegrasi dengan:
    - API BPJS untuk query FKTP terdaftar pasien
    - Database FKTP berdasarkan lokasi
    - Sistem registrasi pasien JKN
    
    Args:
        patient_id: ID pasien BPJS (NIK atau nomor BPJS)
        location: Lokasi pasien (kota/kabupaten) untuk filter FKTP terdekat
        
    Returns:
        JSON string dengan daftar FKTP terdaftar pasien
    """
    # Simulasi: Daftar FKTP terdaftar pasien
    # Dalam implementasi real, ini akan query dari database BPJS
    fktp_list = [
        {
            "fktp_id": "FKTP-001",
            "name": "Puskesmas Kelurahan Sukolilo",
            "address": "Jl. Sukolilo No. 123, Surabaya",
            "type": "Puskesmas",
            "distance_km": 2.5,
            "telehealth_available": True,
            "registration_status": "Aktif",
            "registered_since": "2023-01-15"
        },
        {
            "fktp_id": "FKTP-002",
            "name": "Klinik Pratama Sehat",
            "address": "Jl. Gubeng No. 45, Surabaya",
            "type": "Klinik Pratama",
            "distance_km": 4.1,
            "telehealth_available": True,
            "registration_status": "Aktif",
            "registered_since": "2022-06-20"
        },
        {
            "fktp_id": "FKTP-003",
            "name": "Puskesmas Kelurahan Wonokromo",
            "address": "Jl. Wonokromo No. 78, Surabaya",
            "type": "Puskesmas",
            "distance_km": 6.3,
            "telehealth_available": False,
            "registration_status": "Aktif",
            "registered_since": "2021-03-10"
        }
    ]
    
    # Filter berdasarkan lokasi jika diberikan
    if location:
        # Dalam implementasi real, akan filter berdasarkan lokasi
        filtered_fktp = [f for f in fktp_list if location.lower() in f["address"].lower()]
        if filtered_fktp:
            fktp_list = filtered_fktp
    
    # Sort berdasarkan jarak terdekat
    fktp_list.sort(key=lambda x: x["distance_km"])
    
    result = {
        "status": "success",
        "patient_id": patient_id,
        "total_fktp": len(fktp_list),
        "fktp_list": fktp_list,
        "recommendation": {
            "primary_fktp": fktp_list[0] if fktp_list else None,
            "message": f"Pasien terdaftar di {len(fktp_list)} FKTP. Untuk kasus non-gawat darurat, direkomendasikan ke FKTP terdekat: {fktp_list[0]['name'] if fktp_list else 'Tidak ada'}"
        },
        "note": "[MOCK] Simulasi untuk demo Hackathon. Dalam produksi, ini akan terintegrasi dengan API BPJS untuk query FKTP terdaftar real-time."
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def query_nearest_facility(
    location: str,
    facility_type: str = "all",
    max_distance_km: Optional[float] = None
) -> str:
    """
    Query fasilitas kesehatan terdekat berdasarkan lokasi pasien.
    
    MOCK IMPLEMENTATION untuk Hackathon - Simulasi query faskes terdekat.
    Dalam implementasi produksi, ini akan terintegrasi dengan:
    - API BPJS untuk query faskes berdasarkan lokasi
    - Google Maps API atau geocoding service
    - Database rumah sakit dan IGD
    
    Args:
        location: Lokasi pasien (kota/kabupaten/alamat)
        facility_type: Jenis fasilitas ("rs" untuk rumah sakit, "igd" untuk IGD, "all" untuk semua)
        max_distance_km: Jarak maksimum dalam km (opsional)
        
    Returns:
        JSON string dengan daftar fasilitas kesehatan terdekat
    """
    # Simulasi: Daftar fasilitas kesehatan
    # Dalam implementasi real, ini akan query dari database BPJS berdasarkan koordinat
    facilities = [
        {
            "facility_id": "RS-001",
            "name": "RSUD Dr. Soetomo",
            "type": "Rumah Sakit",
            "address": "Jl. Mayjen Prof. Dr. Moestopo No. 6-8, Surabaya",
            "distance_km": 3.5,
            "igd_available": True,
            "igd_status": "Tersedia",
            "phone": "+62-31-5501076",
            "bpjs_accepted": True
        },
        {
            "facility_id": "RS-002",
            "name": "RS Siloam",
            "type": "Rumah Sakit",
            "address": "Jl. Raya Gubeng No. 70, Surabaya",
            "distance_km": 5.2,
            "igd_available": True,
            "igd_status": "Tersedia",
            "phone": "+62-31-5030000",
            "bpjs_accepted": True
        },
        {
            "facility_id": "RS-003",
            "name": "RSUD Dr. Soedono",
            "type": "Rumah Sakit",
            "address": "Jl. Dr. Soetomo No. 59, Madiun",
            "distance_km": 8.1,
            "igd_available": True,
            "igd_status": "Tersedia",
            "phone": "+62-351-464751",
            "bpjs_accepted": True
        },
        {
            "facility_id": "RS-004",
            "name": "RS Husada Utama",
            "type": "Rumah Sakit",
            "address": "Jl. Raya Darmo No. 90, Surabaya",
            "distance_km": 4.8,
            "igd_available": True,
            "igd_status": "Tersedia",
            "phone": "+62-31-5677575",
            "bpjs_accepted": True
        }
    ]
    
    # Filter berdasarkan jenis fasilitas
    if facility_type == "rs":
        facilities = [f for f in facilities if f["type"] == "Rumah Sakit"]
    elif facility_type == "igd":
        facilities = [f for f in facilities if f.get("igd_available", False)]
    
    # Filter berdasarkan jarak maksimum
    if max_distance_km:
        facilities = [f for f in facilities if f["distance_km"] <= max_distance_km]
    
    # Sort berdasarkan jarak terdekat
    facilities.sort(key=lambda x: x["distance_km"])
    
    # Ambil 3 terdekat
    nearest_facilities = facilities[:3]
    
    result = {
        "status": "success",
        "location": location,
        "total_facilities": len(nearest_facilities),
        "facilities": nearest_facilities,
        "recommendation": {
            "nearest_facility": nearest_facilities[0] if nearest_facilities else None,
            "message": f"Untuk kasus gawat darurat, direkomendasikan ke {nearest_facilities[0]['name'] if nearest_facilities else 'Tidak ada'} (jarak {nearest_facilities[0]['distance_km'] if nearest_facilities else 0} km)"
        },
        "note": "[MOCK] Simulasi untuk demo Hackathon. Dalam produksi, ini akan terintegrasi dengan API BPJS dan geocoding service untuk query faskes terdekat real-time."
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def query_jkn_medical_history(patient_id: str) -> str:
    """
    Query riwayat medis pasien dari sistem JKN/BPJS.
    
    MOCK IMPLEMENTATION untuk Hackathon - Simulasi query riwayat medis JKN.
    Dalam implementasi produksi, ini akan terintegrasi dengan:
    - API BPJS untuk query riwayat kunjungan
    - Database rekam medis elektronik (RME)
    - Sistem history obat dan diagnosis
    
    Args:
        patient_id: ID pasien BPJS (NIK atau nomor BPJS)
        
    Returns:
        JSON string dengan riwayat medis pasien dari JKN
    """
    # Simulasi: Riwayat medis pasien dari JKN
    # Dalam implementasi real, ini akan query dari database BPJS
    medical_history = {
        "patient_id": patient_id,
        "registration_date": "2020-05-15",
        "recent_visits": [
            {
                "visit_date": "2024-10-20",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Hipertensi",
                "icd_code": "I10",
                "medications": [
                    {"name": "Amlodipine", "dosage": "5mg", "frequency": "1x sehari"},
                    {"name": "Captopril", "dosage": "25mg", "frequency": "2x sehari"}
                ],
                "doctor": "Dr. Siti Nurhaliza, Sp.PD"
            },
            {
                "visit_date": "2024-09-15",
                "facility": "Puskesmas Kelurahan Sukolilo",
                "diagnosis": "Diabetes Mellitus Tipe 2",
                "icd_code": "E11",
                "medications": [
                    {"name": "Metformin", "dosage": "500mg", "frequency": "2x sehari"}
                ],
                "doctor": "Dr. Siti Nurhaliza, Sp.PD"
            },
            {
                "visit_date": "2024-08-10",
                "facility": "RSUD Dr. Soetomo",
                "diagnosis": "Gastritis",
                "icd_code": "K29",
                "medications": [
                    {"name": "Omeprazole", "dosage": "20mg", "frequency": "1x sehari"},
                    {"name": "Antasida", "dosage": "500mg", "frequency": "3x sehari setelah makan"}
                ],
                "doctor": "Dr. Ahmad Yani, Sp.PD"
            }
        ],
        "chronic_conditions": [
            {
                "condition": "Hipertensi",
                "diagnosed_date": "2023-01-15",
                "status": "Terpantau",
                "last_checkup": "2024-10-20"
            },
            {
                "condition": "Diabetes Mellitus Tipe 2",
                "diagnosed_date": "2022-06-20",
                "status": "Terpantau",
                "last_checkup": "2024-09-15"
            }
        ],
        "current_medications": [
            {
                "name": "Amlodipine",
                "dosage": "5mg",
                "frequency": "1x sehari",
                "started_date": "2024-10-20",
                "prescribed_by": "Dr. Siti Nurhaliza, Sp.PD"
            },
            {
                "name": "Metformin",
                "dosage": "500mg",
                "frequency": "2x sehari",
                "started_date": "2024-09-15",
                "prescribed_by": "Dr. Siti Nurhaliza, Sp.PD"
            }
        ],
        "allergies": [
            {
                "allergen": "Penicillin",
                "reaction": "Ruam kulit",
                "severity": "Sedang"
            }
        ]
    }
    
    result = {
        "status": "success",
        "medical_history": medical_history,
        "summary": {
            "total_visits": len(medical_history["recent_visits"]),
            "chronic_conditions_count": len(medical_history["chronic_conditions"]),
            "current_medications_count": len(medical_history["current_medications"]),
            "allergies_count": len(medical_history.get("allergies", []))
        },
        "note": "[MOCK] Simulasi untuk demo Hackathon. Dalam produksi, ini akan terintegrasi dengan API BPJS untuk query riwayat medis real-time."
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


# Export tools
query_fktp_registered_tool = FunctionTool(
    func=query_fktp_registered,
)

query_nearest_facility_tool = FunctionTool(
    func=query_nearest_facility,
)

query_jkn_medical_history_tool = FunctionTool(
    func=query_jkn_medical_history,
)

