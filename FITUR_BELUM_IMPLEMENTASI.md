# Fitur yang Belum Diimplementasikan

Dokumen ini merangkum fitur-fitur yang disebutkan di README.md tetapi belum sepenuhnya diimplementasikan.

## Status Implementasi

### ✅ Sudah Diimplementasikan

1. **Struktur Multi-Agent System**

   - ✅ Agent Orkestrator (root_agent)
   - ✅ Agent Wawancara (interview_agent)
   - ✅ Agent Penalaran Klinis (reasoning_agent)
   - ✅ Agent Eksekusi (execution_agent)
   - ✅ Agent Dokumentasi (documentation_agent)

2. **Integrasi Knowledge Base**

   - ✅ Integrasi PDF "Pedoman-BPJS-Kriteria-Gawat-Darurat.pdf"
   - ✅ Tool `check_bpjs_criteria` yang membaca dan menganalisis PDF
   - ✅ Analisis gejala menggunakan Gemini dengan referensi ke dokumen BPJS

3. **Basic Workflow**

   - ✅ Alur kerja orchestrator dengan delegasi ke sub-agents
   - ✅ Session state management untuk passing data antar agents

4. **Mock API Integrations (Untuk Demo Hackathon)**

   - ✅ Mock API Layanan Darurat dengan simulasi realistis
   - ✅ Mock API Mobile JKN dengan simulasi scan jadwal dan booking
   - ✅ Output lengkap dan siap untuk demonstrasi

5. **Ekstraksi Gejala dengan LLM**

   - ✅ Implementasi menggunakan Gemini untuk ekstraksi entitas medis
   - ✅ Parsing transkrip percakapan ke format JSON terstruktur
   - ✅ Validasi dan error handling yang robust

6. **Optimasi Prompt Interview Agent**

   - ✅ Prompt dioptimalkan untuk tidak mengulang pertanyaan yang sudah dijawab
   - ✅ Instruksi eksplisit untuk efisiensi wawancara
   - ✅ Ekstraksi gejala segera setelah informasi minimal terkumpul

7. **Perbaikan Reasoning Agent**
   - ✅ Perbaikan untuk menangani gejala yang tidak terstruktur dengan baik
   - ✅ Raw data fallback jika struktur gejala kosong
   - ✅ Instruksi eksplisit untuk tidak mengasumsikan "tidak ada gejala"
   - ✅ Debug logging untuk troubleshooting

8. **Perbaikan Duplikasi Respons (Nov 2025)**
   - ✅ Orchestrator prompt dioptimalkan untuk menyapa hanya sekali dan segera mendelegasikan
   - ✅ Interview Agent prompt dioptimalkan untuk tidak mengulang sapaan/perkenalan
   - ✅ Frontend deduplication logic untuk mencegah duplikasi pesan di UI
   - ✅ Implementasi fuzzy matching dan similarity checking untuk deteksi duplikasi

---

## ❌ Belum Diimplementasikan (Masih Placeholder)

### 1. Agent Wawancara - Ekstraksi Gejala & Optimasi Prompt

**File:**

- `medical_triage_agent/sub_agents/interview_agent/tools/tools.py` (Ekstraksi gejala)
- `medical_triage_agent/sub_agents/interview_agent/prompt.py` (Optimasi prompt)

**Status:** ✅ **IMPLEMENTED & IMPROVED** - Menggunakan Gemini LLM untuk ekstraksi + Prompt dioptimalkan

**Yang Sudah Diimplementasikan:**

- ✅ Implementasi ekstraksi gejala menggunakan Gemini LLM
- ✅ Parsing transkrip percakapan untuk mengekstrak:
  - ✅ Gejala utama dan gejala penyerta
  - ✅ Durasi gejala
  - ✅ Tingkat keparahan
  - ✅ Riwayat medis
  - ✅ Obat yang sedang dikonsumsi
  - ✅ Alergi
- ✅ Validasi dan strukturisasi data gejala
- ✅ Error handling dan fallback mechanism
- ✅ JSON output validation

**Fitur Implementasi:**

- Menggunakan Gemini 2.5 Flash dengan temperature rendah (0.1) untuk konsistensi
- Force JSON output dengan `response_mime_type="application/json"`
- Validasi struktur output untuk memastikan semua field ada
- Fallback mechanism jika JSON parsing gagal
- Error handling yang robust

**Perbaikan Prompt (Interview Agent):**

- ✅ Instruksi eksplisit untuk tidak mengulang pertanyaan yang sudah dijawab
- ✅ Akui informasi yang sudah diberikan oleh pasien
- ✅ Ekstraksi gejala segera setelah informasi minimal terkumpul (tidak menunggu informasi lengkap)
- ✅ Hanya menanyakan informasi yang benar-benar belum ada
- ✅ Contoh interaksi yang benar dan salah untuk guidance
- ✅ **Perbaikan Duplikasi (Nov 2025)**: Instruksi untuk tidak mengulang sapaan/perkenalan yang sudah dilakukan orchestrator

**Perbaikan Prompt (Orchestrator):**

- ✅ **Perbaikan Duplikasi (Nov 2025)**: Instruksi untuk menyapa hanya sekali dan segera mendelegasikan ke interview agent tanpa menambahkan pertanyaan tambahan

---

### 2. Agent Eksekusi - Integrasi API

**File:** `medical_triage_agent/sub_agents/execution_agent/tools/tools.py`

#### 2.1. API Layanan Darurat

**Status:** ✅ **Mock Implementation** - Siap untuk demo Hackathon

**Yang Sudah Diimplementasikan (Mock):**

- ✅ Simulasi pencarian rumah sakit terdekat
- ✅ Generate ambulance ID dan tracking
- ✅ Estimasi waktu kedatangan (dynamic)
- ✅ Notifikasi ke IGD rumah sakit
- ✅ Instruksi lengkap untuk pasien
- ✅ Tracking URL dan informasi kontak

**Catatan:** Mock implementation sudah realistis dan siap untuk demo. Untuk produksi, perlu integrasi dengan API real:

- [ ] Integrasi dengan API layanan darurat (119, rumah sakit)
- [ ] Sistem notifikasi real-time ke rumah sakit terdekat
- [ ] Koordinasi dengan sistem ambulans real-time
- [ ] Tracking status layanan darurat real-time

**Fungsi:** `call_emergency_service()`

#### 2.2. API Mobile JKN

**Perbaikan Type Annotation:**

- ✅ Fixed type annotation untuk `preferred_location: Optional[str] = None` (sebelumnya `str = None`)

#### 2.3. Perbaikan Reasoning Agent - Robustness Handling Gejala

**File:** `medical_triage_agent/sub_agents/reasoning_agent/tools/tools.py`

**Status:** ✅ **IMPROVED** - Perbaikan untuk menangani gejala yang tidak terstruktur

**Perbaikan yang Dilakukan:**

- ✅ Menambahkan raw symptoms JSON ke prompt agar Gemini bisa melihat data mentah
- ✅ Instruksi eksplisit untuk tidak mengasumsikan "tidak ada gejala" jika ada durasi/tingkat keparahan
- ✅ Fallback mechanism: jika struktur gejala kosong, gunakan raw data untuk inferensi
- ✅ Menambahkan riwayat medis dan obat ke symptoms summary
- ✅ Debug logging untuk troubleshooting
- ✅ Perbaikan error handling dengan default ke "Mendesak" jika parsing gagal
- ✅ Mengubah "Tidak ada" menjadi "Tidak disebutkan secara eksplisit" untuk menghindari misinterpretasi

**Fungsi:** `check_bpjs_criteria()`

#### 2.4. API Mobile JKN (Lanjutan)

**Status:** ✅ **Mock Implementation** - Siap untuk demo Hackathon

**Yang Sudah Diimplementasikan (Mock):**

- ✅ Simulasi pencarian FKTP terdekat
- ✅ Scan jadwal dokter yang tersedia
- ✅ Booking slot telehealth dengan 3 skenario:
  - Immediate: slot dalam 1-2 jam
  - Same day: slot hari ini
  - Scheduled: booking untuk besok
- ✅ Generate booking ID dan nomor antrian
- ✅ Instruksi lengkap untuk pasien
- ✅ Tracking URL untuk booking

**Catatan:** Mock implementation sudah realistis dan siap untuk demo. Untuk produksi, perlu integrasi dengan API real:

- [ ] Integrasi dengan API Mobile JKN resmi
- [ ] Pencarian FKTP real-time berdasarkan lokasi
- [ ] Pemesanan slot dokter real-time
- [ ] Validasi ID pasien BPJS
- [ ] Konfirmasi jadwal dan pengiriman notifikasi real-time

**Fungsi:** `schedule_mobile_jkn()`

#### 2.5. RAG System untuk Self-Care

**Status:** ❌ Placeholder - hanya return hardcoded guide

**Yang Perlu Diimplementasikan:**

- [ ] Setup Vertex AI RAG Engine atau database
- [ ] Upload/ingest panduan self-care yang tervalidasi
- [ ] Query RAG berdasarkan gejala pasien
- [ ] Retrieval panduan yang relevan dan terpercaya
- [ ] Formatting panduan untuk pasien

**Fungsi:** `get_self_care_guide()`

---

### 3. Agent Dokumentasi - ICD Code Mapping

**File:** `medical_triage_agent/sub_agents/documentation_agent/tools/tools.py`

**Status:** ❌ Placeholder - hanya mapping sederhana untuk beberapa gejala

**Yang Perlu Diimplementasikan:**

- [ ] Database atau API untuk mapping gejala ke kode ICD-10/ICD-9
- [ ] Logika mapping yang lebih kompleks dan akurat
- [ ] Confidence scoring untuk rekomendasi kode ICD
- [ ] Multiple code recommendations dengan prioritas
- [ ] Validasi kode ICD dengan standar resmi

**Fungsi:** `recommend_icd_code()`

---

## 📋 TODO dari README.md

Berdasarkan bagian "TODO / Next Steps" di README.md:

### High Priority

- [x] **Implementasi ekstraksi gejala menggunakan LLM/NLP** ✅ **SELESAI**

  - File: `interview_agent/tools/tools.py`
  - Status: Sudah diimplementasikan menggunakan Gemini LLM
  - Fitur: Ekstraksi entitas medis dari transkrip dengan validasi JSON

- [x] **Mock API Layanan Darurat** ✅ **SELESAI (Mock untuk Hackathon)**

  - File: `execution_agent/tools/tools.py`
  - Status: Mock implementation sudah dibuat dan siap untuk demo
  - Catatan: Untuk produksi, perlu integrasi dengan API real

- [x] **Mock API Mobile JKN** ✅ **SELESAI (Mock untuk Hackathon)**

  - File: `execution_agent/tools/tools.py`
  - Status: Mock implementation sudah dibuat dan siap untuk demo
  - Catatan: Untuk produksi, perlu integrasi dengan API real

### Medium Priority

- [ ] **Setup RAG system untuk panduan self-care**

  - File: `execution_agent/tools/tools.py`
  - Prioritas: **Sedang** - Penting untuk kasus non-urgen

- [ ] **Database mapping gejala ke kode ICD-10/ICD-9**
  - File: `documentation_agent/tools/tools.py`
  - Prioritas: **Sedang** - Penting untuk dokumentasi medis

### Low Priority / Nice to Have

- [ ] **Integrasi dengan API BPJS resmi untuk kriteria gawat darurat**

  - Status: Sudah menggunakan PDF Pedoman BPJS, tapi bisa ditingkatkan dengan API real-time
  - Prioritas: **Rendah** - PDF sudah cukup untuk sekarang

- [ ] **Evaluasi dan fine-tuning dengan data real**

  - Prioritas: **Rendah** - Setelah semua fitur dasar selesai

- [ ] **Testing end-to-end dengan berbagai skenario**
  - Prioritas: **Rendah** - Setelah implementasi selesai

---

## 🏗️ Fitur Tambahan yang Disarankan

### Testing & Quality Assurance

- [ ] Unit tests untuk setiap tool
- [ ] Integration tests untuk workflow end-to-end
- [ ] Test cases dengan berbagai skenario triage
- [ ] Error handling dan edge cases

### Deployment & Infrastructure

- [ ] Deployment scripts untuk Vertex AI Agent Engine
- [ ] Environment configuration management
- [ ] Logging dan monitoring
- [ ] Error tracking dan alerting

### Security & Compliance

- [ ] Enkripsi data medis
- [ ] Audit logging
- [ ] Compliance dengan regulasi privasi data medis
- [ ] Authentication dan authorization

### Documentation

- [ ] API documentation untuk tools
- [ ] Architecture diagram yang lebih detail
- [ ] User guide untuk setup dan konfigurasi
- [ ] Troubleshooting guide

---

## 📊 Ringkasan Prioritas

| Fitur                       | Prioritas | Status                   | File                                 |
| --------------------------- | --------- | ------------------------ | ------------------------------------ |
| Ekstraksi gejala dengan LLM | 🔴 Tinggi | ✅ **IMPLEMENTED**       | `interview_agent/tools/tools.py`     |
| Optimasi Prompt Interview   | 🔴 Tinggi | ✅ **IMPROVED**          | `interview_agent/prompt.py`          |
| Perbaikan Duplikasi Respons | 🔴 Tinggi | ✅ **IMPROVED**          | `prompt.py`, `interview_agent/prompt.py`, `frontend/src/App.tsx` |
| Robustness Reasoning        | 🔴 Tinggi | ✅ **IMPROVED**          | `reasoning_agent/tools/tools.py`     |
| API Layanan Darurat         | 🔴 Tinggi | ✅ Mock (Ready for Demo) | `execution_agent/tools/tools.py`     |
| API Mobile JKN              | 🔴 Tinggi | ✅ Mock (Ready for Demo) | `execution_agent/tools/tools.py`     |
| RAG Self-Care               | 🟡 Sedang | ❌ Placeholder           | `execution_agent/tools/tools.py`     |
| ICD Code Mapping            | 🟡 Sedang | ❌ Placeholder           | `documentation_agent/tools/tools.py` |
| Testing                     | 🟢 Rendah | ❌ Belum ada             | -                                    |
| Deployment                  | 🟢 Rendah | ❌ Belum ada             | -                                    |

---

## 🎯 Rekomendasi Urutan Implementasi

1. **Phase 1: Core Functionality**

   - ✅ Mock API Mobile JKN (SELESAI - siap untuk demo)
   - ✅ Mock API Layanan Darurat (SELESAI - siap untuk demo)
   - ✅ Ekstraksi gejala dengan LLM (SELESAI - menggunakan Gemini)
   - ✅ Optimasi Prompt Interview Agent (SELESAI - tidak mengulang pertanyaan)
   - ✅ Perbaikan Reasoning Agent (SELESAI - robust handling gejala)
   - ✅ Perbaikan Duplikasi Respons (SELESAI - Nov 2025 - orchestrator & interview agent prompt + frontend deduplication)

2. **Phase 2: Critical Features**

   - Setup RAG untuk self-care
   - (API integrations sudah di-mock untuk Hackathon)

3. **Phase 3: Documentation & Quality**

   - ICD code mapping database
   - Testing dan error handling

4. **Phase 4: Production Ready**
   - Deployment scripts
   - Monitoring dan logging
   - Security hardening

---

## Catatan

- Semua struktur dasar sudah ada dan siap untuk implementasi
- Tools sudah didefinisikan dengan signature yang benar
- Hanya perlu mengisi implementasi dari placeholder ke real functionality
- PDF BPJS sudah terintegrasi dan berfungsi dengan baik
