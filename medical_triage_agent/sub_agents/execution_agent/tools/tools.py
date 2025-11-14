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
from typing import Optional
from google.adk.tools import FunctionTool


def call_emergency_service(patient_location: str, symptoms: str, urgency_level: str) -> str:
    """
    Memanggil layanan darurat (ambulans) atau mengirim notifikasi ke rumah sakit.
    
    MOCK IMPLEMENTATION untuk Hackathon - Simulasi panggilan layanan darurat.
    Dalam implementasi produksi, ini akan terintegrasi dengan:
    - API 119 (layanan darurat nasional)
    - API rumah sakit terdekat
    - Sistem koordinasi ambulans
    
    Args:
        patient_location: Lokasi pasien (alamat atau koordinat)
        symptoms: Gejala yang dialami pasien
        urgency_level: Level urgensi (Gawat Darurat)
        
    Returns:
        JSON string dengan status dan informasi layanan darurat
    """
    import random
    from datetime import datetime, timedelta
    
    # Simulasi: Cari rumah sakit terdekat berdasarkan lokasi
    # Dalam implementasi real, ini akan query database/API rumah sakit
    hospitals = [
        {
            "name": "RSUD Dr. Soetomo",
            "address": "Jl. Mayjen Prof. Dr. Moestopo No. 6-8, Surabaya",
            "distance_km": 3.5,
            "igd_available": True
        },
        {
            "name": "RS Siloam",
            "address": "Jl. Raya Gubeng No. 70, Surabaya",
            "distance_km": 5.2,
            "igd_available": True
        },
        {
            "name": "RSUD Dr. Soedono",
            "address": "Jl. Dr. Soetomo No. 59, Madiun",
            "distance_km": 8.1,
            "igd_available": True
        }
    ]
    
    # Simulasi: Pilih rumah sakit terdekat
    nearest_hospital = min(hospitals, key=lambda x: x["distance_km"])
    
    # Simulasi: Estimasi waktu kedatangan ambulans (10-25 menit)
    estimated_minutes = random.randint(10, 25)
    arrival_time = datetime.now() + timedelta(minutes=estimated_minutes)
    
    # Simulasi: Generate nomor tracking ambulans
    ambulance_id = f"AMB-{random.randint(1000, 9999)}"
    
    result = {
        "status": "success",
        "action": "emergency_service_activated",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": {
            "ambulance": {
                "dispatched": True,
                "ambulance_id": ambulance_id,
                "estimated_arrival_minutes": estimated_minutes,
                "estimated_arrival_time": arrival_time.strftime("%H:%M WIB"),
                "status": "Dalam perjalanan ke lokasi pasien"
            },
            "hospital": {
                "name": nearest_hospital["name"],
                "address": nearest_hospital["address"],
                "distance_km": nearest_hospital["distance_km"],
                "igd_notified": True,
                "igd_status": "Siap menerima pasien",
                "message": f"IGD {nearest_hospital['name']} telah diberitahu dan siap menerima pasien"
            },
            "patient_instructions": {
                "primary": f"Segera menuju IGD {nearest_hospital['name']}",
                "address": nearest_hospital["address"],
                "note": "Sesuai prosedur BPJS, kondisi gawat darurat tidak memerlukan surat rujukan",
                "ambulance_info": f"Ambulans {ambulance_id} akan tiba dalam {estimated_minutes} menit"
            }
        },
        "next_steps": [
            "Tetap tenang dan jangan melakukan aktivitas berat",
            "Jika ambulans belum tiba dalam 20 menit, hubungi 119",
            f"Setibanya di {nearest_hospital['name']}, langsung ke IGD dan beri tahu bahwa Anda telah didaftarkan melalui sistem triase Mobile JKN"
        ],
        "tracking": {
            "ambulance_tracking_url": f"https://mobile-jkn.bpjs-kesehatan.go.id/track/{ambulance_id}",
            "hospital_contact": "+62-31-XXXX-XXXX"
        },
        "note": "[MOCK] Simulasi untuk demo Hackathon. Dalam produksi, ini akan terintegrasi dengan sistem layanan darurat real-time."
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def schedule_mobile_jkn(patient_id: str, symptoms: str, preferred_location: Optional[str] = None) -> str:
    """
    Memanggil API penjadwalan Mobile JKN untuk memindai dan memesan slot dokter di FKTP.
    
    MOCK IMPLEMENTATION untuk Hackathon - Simulasi scan jadwal dan booking telehealth.
    Dalam implementasi produksi, ini akan terintegrasi dengan:
    - API Mobile JKN untuk pencarian FKTP
    - API penjadwalan dokter
    - Sistem booking slot telehealth
    
    Args:
        patient_id: ID pasien BPJS
        symptoms: Gejala yang dialami
        preferred_location: Lokasi preferensi (opsional)
        
    Returns:
        JSON string dengan informasi jadwal dan lokasi FKTP
    """
    import random
    from datetime import datetime, timedelta
    
    # Simulasi: Daftar FKTP yang tersedia
    fktp_list = [
        {
            "name": "Puskesmas Kelurahan Sukolilo",
            "address": "Jl. Sukolilo No. 123, Surabaya",
            "distance_km": 2.5,
            "telehealth_available": True
        },
        {
            "name": "Puskesmas Kelurahan Gubeng",
            "address": "Jl. Gubeng No. 45, Surabaya",
            "distance_km": 4.1,
            "telehealth_available": True
        },
        {
            "name": "Puskesmas Kelurahan Wonokromo",
            "address": "Jl. Wonokromo No. 78, Surabaya",
            "distance_km": 6.3,
            "telehealth_available": True
        }
    ]
    
    # Simulasi: Cari FKTP terdekat (atau sesuai preferensi)
    if preferred_location:
        # Dalam implementasi real, akan query berdasarkan lokasi
        selected_fktp = random.choice(fktp_list)
    else:
        selected_fktp = min(fktp_list, key=lambda x: x["distance_km"])
    
    # Simulasi: Scan jadwal dokter yang tersedia
    # Dalam implementasi real, ini akan query database jadwal dokter
    doctors = [
        {"name": "Dr. Siti Nurhaliza, Sp.PD", "specialization": "Penyakit Dalam", "available": True},
        {"name": "Dr. Budi Santoso, Sp.A", "specialization": "Anak", "available": True},
        {"name": "Dr. Ahmad Yani, Sp.JP", "specialization": "Jantung", "available": False},
    ]
    
    # Simulasi: Cari dokter yang tersedia
    available_doctors = [d for d in doctors if d["available"]]
    if not available_doctors:
        # Jika tidak ada dokter tersedia hari ini, cari jadwal berikutnya
        selected_doctor = random.choice(doctors)
        appointment_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        appointment_time = "08:30"
        appointment_type = "scheduled"
        message = f"Dokter tidak tersedia hari ini, namun saya telah menjadwalkan Anda untuk konsultasi video besok jam {appointment_time} WIB"
    else:
        # Dokter tersedia hari ini atau dalam beberapa jam
        selected_doctor = random.choice(available_doctors)
        # Simulasi: Cek apakah ada slot dalam 2 jam ke depan
        hours_ahead = random.randint(1, 4)
        if hours_ahead <= 2:
            appointment_date = datetime.now().strftime("%Y-%m-%d")
            appointment_time = (datetime.now() + timedelta(hours=hours_ahead)).strftime("%H:00")
            appointment_type = "immediate"
            message = f"Berhasil! Saya telah memesan slot konsultasi video dengan {selected_doctor['name']} hari ini jam {appointment_time} WIB"
        else:
            appointment_date = datetime.now().strftime("%Y-%m-%d")
            appointment_time = (datetime.now() + timedelta(hours=hours_ahead)).strftime("%H:00")
            appointment_type = "same_day"
            message = f"Berhasil! Saya telah memesan slot konsultasi video dengan {selected_doctor['name']} hari ini jam {appointment_time} WIB"
    
    # Simulasi: Generate nomor antrian
    queue_number = f"{random.choice(['A', 'B', 'C'])}-{random.randint(10, 99)}"
    
    # Simulasi: Generate booking ID
    booking_id = f"JKN-{random.randint(100000, 999999)}"
    
    result = {
        "status": "success",
        "action": "appointment_scheduled",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "booking_id": booking_id,
        "patient_id": patient_id,
        "fktp": {
            "name": selected_fktp["name"],
            "address": selected_fktp["address"],
            "distance_km": selected_fktp["distance_km"],
            "telehealth_enabled": True
        },
        "appointment": {
            "type": appointment_type,  # "immediate", "same_day", "scheduled"
            "date": appointment_date,
            "time": appointment_time,
            "timezone": "WIB",
            "format": "Telehealth (Video Call)",
            "doctor": {
                "name": selected_doctor["name"],
                "specialization": selected_doctor["specialization"]
            },
            "queue_number": queue_number,
            "estimated_duration_minutes": 15,
            "platform": "Mobile JKN Telehealth"
        },
        "instructions": {
            "before_appointment": [
                "Pastikan koneksi internet stabil",
                "Siapkan dokumen BPJS (kartu atau aplikasi Mobile JKN)",
                "Siapkan ruangan yang tenang dan privasi terjaga"
            ],
            "on_appointment_time": [
                f"Buka aplikasi Mobile JKN",
                f"Masuk ke menu 'Telehealth'",
                f"Klik 'Mulai Konsultasi' pada booking ID: {booking_id}",
                f"Tunggu dokter bergabung dalam video call"
            ]
        },
        "message": message,
        "next_steps": [
            "Anda akan menerima notifikasi reminder 30 menit sebelum jadwal konsultasi",
            "Jika perlu membatalkan atau mengubah jadwal, bisa dilakukan melalui aplikasi Mobile JKN",
            "Untuk pertanyaan, hubungi layanan pelanggan Mobile JKN"
        ],
        "tracking": {
            "booking_url": f"https://mobile-jkn.bpjs-kesehatan.go.id/booking/{booking_id}",
            "cancel_url": f"https://mobile-jkn.bpjs-kesehatan.go.id/booking/{booking_id}/cancel"
        },
        "note": "[MOCK] Simulasi untuk demo Hackathon. Dalam produksi, ini akan terintegrasi dengan API Mobile JKN real-time untuk scan jadwal dan booking."
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_self_care_guide(symptoms: str) -> str:
    """
    Mengambil panduan self-care dari database atau RAG system.
    
    Args:
        symptoms: Gejala yang dialami pasien
        
    Returns:
        JSON string dengan panduan self-care yang tervalidasi
    """
    # TODO: Implementasi RAG atau database query untuk panduan self-care
    # Bisa menggunakan Vertex AI RAG atau database lokal
    
    result = {
        "status": "success",
        "action": "self_care_guide_provided",
        "guide": {
            "title": "Panduan Perawatan di Rumah",
            "recommendations": [
                "Istirahat yang cukup",
                "Minum air putih yang banyak",
                "Hindari aktivitas berat",
                "Monitor gejala secara berkala"
            ],
            "medications": [
                {
                    "name": "Paracetamol",
                    "dosage": "500mg",
                    "frequency": "3x sehari setelah makan"
                }
            ],
            "when_to_seek_help": "Jika gejala memburuk atau tidak membaik dalam 3 hari, segera hubungi dokter",
            "warning_signs": [
                "Demam tinggi (>39°C)",
                "Sesak napas",
                "Nyeri yang tidak tertahankan"
            ]
        }
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


call_emergency_service_tool = FunctionTool(
    func=call_emergency_service,
)

schedule_mobile_jkn_tool = FunctionTool(
    func=schedule_mobile_jkn,
)

get_self_care_guide_tool = FunctionTool(
    func=get_self_care_guide,
)

