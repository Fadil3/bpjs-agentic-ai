# Panduan Testing Kasus Non-Urgen

Dokumen ini menjelaskan cara melakukan testing untuk skenario **Non-Urgen** pada Medical Triage Agent.

## Overview

Kasus **Non-Urgen** adalah kondisi yang:

- Gejala ringan dan stabil
- Tidak mengancam nyawa
- Tidak memerlukan penanganan segera
- Bisa ditangani dengan perawatan di rumah (self-care)
- Bisa ditangani di FKTP untuk konsultasi rutin

## Expected Workflow untuk Non-Urgen

1. **Root Agent** → Delegasi ke **Interview Agent**
2. **Interview Agent** → Wawancara gejala → Ekstrak gejala → Simpan `symptoms_data`
3. **Reasoning Agent** → Analisis gejala → Klasifikasi **Non-Urgen** → Simpan `triage_result`
4. **Execution Agent** → Query FKTP terdaftar → Query knowledge base → Panggil `get_self_care_guide` → Simpan `execution_result`
5. **Documentation Agent** → Generate SOAP → Simpan `medical_documentation`

## Skenario Testing

### Skenario 1: Pusing Ringan Setelah Bangun Tidur

**Input User:**

```
Saya merasa sedikit pusing setelah bangun tidur, tapi sudah membaik sekarang
```

**Expected Behavior:**

1. **Interview Agent** akan menanyakan:

   - Durasi pusing
   - Tingkat keparahan (skala 1-10)
   - Gejala penyerta (mual, muntah, dll)
   - Riwayat medis
   - Obat yang sedang dikonsumsi

2. **Reasoning Agent** akan mengklasifikasikan sebagai **Non-Urgen** karena:

   - Gejala ringan (pusing ringan)
   - Sudah membaik
   - Tidak ada gejala penyerta yang mengkhawatirkan

3. **Execution Agent** akan:
   - ✅ Query `query_fktp_registered` untuk mendapatkan FKTP terdaftar
   - ✅ Query `query_ppk_kemenkes_tool` untuk panduan self-care
   - ✅ Query `query_knowledge_base_tool` untuk informasi umum
   - ✅ Memanggil `get_self_care_guide` dengan gejala pasien
   - ✅ Memberikan rekomendasi perawatan di rumah
   - ✅ Memberikan informasi FKTP terdaftar untuk konsultasi rutin

**Expected Output dari `get_self_care_guide`:**

```json
{
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
```

### Skenario 2: Batuk Pilek Ringan

**Input User:**

```
Saya batuk dan pilek sejak 2 hari lalu, tapi tidak demam. Sudah minum obat bebas tapi belum sembuh total
```

**Expected Behavior:**

1. **Interview Agent** akan menanyakan:

   - Durasi batuk pilek
   - Apakah ada demam
   - Apakah ada gejala lain (sesak napas, nyeri tenggorokan)
   - Obat yang sudah diminum
   - Riwayat medis

2. **Reasoning Agent** akan mengklasifikasikan sebagai **Non-Urgen** karena:

   - Gejala ringan (batuk pilek tanpa demam)
   - Tidak ada gejala penyerta yang mengkhawatirkan
   - Durasi masih dalam batas normal untuk common cold

3. **Execution Agent** akan:
   - ✅ Query FKTP terdaftar
   - ✅ Query knowledge base untuk panduan self-care batuk pilek
   - ✅ Memanggil `get_self_care_guide` dengan gejala batuk pilek
   - ✅ Memberikan rekomendasi perawatan di rumah
   - ✅ Memberikan informasi kapan harus kembali ke dokter

### Skenario 3: Sakit Kepala Ringan

**Input User:**

```
Saya sakit kepala ringan sejak pagi, sekitar 3/10. Tidak ada gejala lain
```

**Expected Behavior:**

1. **Interview Agent** akan menanyakan:

   - Durasi sakit kepala
   - Tingkat keparahan (sudah disebutkan 3/10)
   - Gejala penyerta
   - Riwayat medis (hipertensi, migrain, dll)
   - Obat yang sedang dikonsumsi

2. **Reasoning Agent** akan mengklasifikasikan sebagai **Non-Urgen** karena:

   - Tingkat keparahan rendah (3/10)
   - Tidak ada gejala penyerta yang mengkhawatirkan
   - Tidak ada riwayat yang mengkhawatirkan

3. **Execution Agent** akan:
   - ✅ Query FKTP terdaftar
   - ✅ Query knowledge base untuk panduan self-care sakit kepala
   - ✅ Memanggil `get_self_care_guide` dengan gejala sakit kepala
   - ✅ Memberikan rekomendasi perawatan di rumah

## Cara Testing

### Metode 1: Testing via ADK CLI

```bash
cd /home/seryu/projects/bpjs-agentic-ai
uv run adk run medical_triage_agent
```

**Langkah-langkah:**

1. Agent akan memulai dengan greeting
2. Ketik salah satu skenario di atas
3. Jawab pertanyaan dari interview agent
4. Tunggu reasoning agent mengklasifikasikan
5. Verifikasi execution agent memanggil `get_self_care_guide`
6. Verifikasi output self-care guide

**Contoh Interaksi:**

```
user: Saya merasa sedikit pusing setelah bangun tidur, tapi sudah membaik sekarang

[interview_agent]: Berapa lama Anda mengalami pusing ini?
user: Baru saja, sekitar 30 menit lalu

[interview_agent]: Berapa tingkat keparahan pusing Anda? (skala 1-10)
user: Sekitar 3/10

[interview_agent]: Apakah ada gejala lain yang menyertai?
user: Tidak ada

[reasoning_agent]: Berdasarkan gejala yang Anda sampaikan, kondisi ini dikategorikan sebagai **Non-Urgen**...

[execution_agent]: Berikut adalah panduan perawatan di rumah untuk kondisi Anda...
```

### Metode 2: Testing via Web UI

```bash
cd /home/seryu/projects/bpjs-agentic-ai
uv run adk web
```

**Langkah-langkah:**

1. Buka browser ke `http://localhost:8000`
2. Pilih `medical_triage_agent` dari dropdown
3. Ketik salah satu skenario di atas
4. Jawab pertanyaan dari interview agent
5. Lihat workflow di UI:
   - ✅ Interview agent mengumpulkan gejala
   - ✅ Reasoning agent mengklasifikasikan sebagai Non-Urgen
   - ✅ Execution agent memanggil `get_self_care_guide`
   - ✅ Documentation agent membuat SOAP

### Metode 3: Testing via Custom Web UI

```bash
cd /home/seryu/projects/bpjs-agentic-ai
./start_custom_ui.sh
```

**Langkah-langkah:**

1. Buka browser ke `http://localhost:8000`
2. Ketik salah satu skenario di atas
3. Jawab pertanyaan dari interview agent
4. Lihat structured data di UI:
   - Triage Level: **Non-Urgen** (badge hijau)
   - Execution Result: Self-care guide
   - SOAP Documentation

## Analisis Respons Execution Agent

Untuk melihat analisis lengkap apakah respons execution agent sudah memenuhi requirements, lihat **[ANALISIS_RESPONS_NON_URGEN.md](ANALISIS_RESPONS_NON_URGEN.md)**.

**Quick Check:**

- ✅ Format respons lengkap dengan justifikasi detail
- ✅ Referensi ke knowledge base (PPK Kemenkes, BPJS Criteria)
- ✅ FKTP terdaftar disebutkan dengan spesifik
- ✅ Self-care guide diberikan
- ✅ Instruksi lengkap dengan warning signs

## Checklist Verifikasi

### ✅ Verifikasi Interview Agent

- [ ] Agent menanyakan gejala utama
- [ ] Agent menanyakan durasi gejala
- [ ] Agent menanyakan tingkat keparahan
- [ ] Agent menanyakan gejala penyerta
- [ ] Agent menanyakan riwayat medis
- [ ] Agent menanyakan obat yang sedang dikonsumsi
- [ ] Agent tidak mengulang pertanyaan yang sudah dijawab
- [ ] Agent mengekstrak gejala ke `symptoms_data`

### ✅ Verifikasi Reasoning Agent

- [ ] Agent membaca `symptoms_data` dari state
- [ ] Agent memanggil `check_bpjs_criteria` dengan gejala
- [ ] Agent mengklasifikasikan sebagai **Non-Urgen**
- [ ] Agent memberikan justifikasi yang jelas
- [ ] Agent menyimpan `triage_result` ke state
- [ ] Agent mentransfer ke `execution_agent`

### ✅ Verifikasi Execution Agent

- [ ] Agent membaca `triage_result` dari state
- [ ] Agent query `query_fktp_registered` untuk FKTP terdaftar
- [ ] Agent query `query_ppk_kemenkes_tool` untuk panduan self-care
- [ ] Agent query `query_knowledge_base_tool` untuk informasi umum
- [ ] Agent memanggil `get_self_care_guide` dengan gejala pasien
- [ ] Agent memberikan rekomendasi perawatan di rumah
- [ ] Agent memberikan informasi FKTP terdaftar
- [ ] Agent memberikan saran kapan harus kembali ke dokter
- [ ] Agent menyimpan `execution_result` ke state
- [ ] Agent mentransfer ke `documentation_agent`

### ✅ Verifikasi Documentation Agent

- [ ] Agent membaca semua data dari state (`symptoms_data`, `triage_result`, `execution_result`)
- [ ] Agent memanggil `format_soap` untuk membuat dokumentasi SOAP
- [ ] Agent memanggil `recommend_icd_code` untuk rekomendasi kode ICD
- [ ] Agent menyimpan `medical_documentation` ke state
- [ ] SOAP document lengkap dengan S, O, A, P

## Expected State Values

Setelah workflow selesai, session state harus berisi:

```json
{
  "symptoms_data": {
    "gejala_utama": ["pusing ringan"],
    "gejala_penyerta": [],
    "durasi": "30 menit",
    "tingkat_keparahan": "3/10",
    "riwayat_medis": [],
    "obat": [],
    "alergi": []
  },
  "triage_result": {
    "triage_level": "Non-Urgen",
    "matched_criteria": [],
    "justification": "Gejala ringan dan stabil, tidak memerlukan penanganan segera",
    "recommendation": "Perawatan di rumah dengan self-care guide"
  },
  "execution_result": {
    "status": "success",
    "action": "self_care_guide_provided",
    "guide": {
      "title": "Panduan Perawatan di Rumah",
      "recommendations": [...],
      "medications": [...],
      "when_to_seek_help": "...",
      "warning_signs": [...]
    },
    "fktp_registered": {
      "name": "...",
      "address": "..."
    }
  },
  "medical_documentation": {
    "S (Subjektif)": {...},
    "O (Objektif)": {...},
    "A (Asesmen)": {...},
    "P (Plan)": {...}
  }
}
```

## Troubleshooting

### Problem: Execution Agent tidak memanggil `get_self_care_guide`

**Kemungkinan Penyebab:**

- Reasoning agent tidak mengklasifikasikan sebagai Non-Urgen
- Execution agent tidak membaca `triage_result` dengan benar
- Prompt execution agent tidak jelas

**Solusi:**

1. Cek log untuk melihat triage level yang diklasifikasikan
2. Verifikasi `triage_result` di session state
3. Cek apakah execution agent membaca state dengan benar

### Problem: Self-care guide terlalu generic

**Kemungkinan Penyebab:**

- `get_self_care_guide` masih placeholder (hardcoded)
- Tidak ada RAG system untuk self-care

**Solusi:**

- Untuk sekarang, ini expected behavior karena RAG belum diimplementasikan
- Untuk produksi, perlu setup RAG system dengan panduan self-care yang spesifik

### Problem: Execution Agent tidak query knowledge base

**Kemungkinan Penyebab:**

- Prompt tidak jelas tentang kewajiban query knowledge base
- Agent tidak mengikuti instruksi

**Solusi:**

1. Cek log untuk melihat apakah agent memanggil query tools
2. Verifikasi prompt execution agent sudah jelas tentang kewajiban query
3. Pastikan tools tersedia di agent

## Tips Testing

1. **Gunakan gejala yang jelas non-urgen**: Pusing ringan, batuk pilek tanpa demam, sakit kepala ringan
2. **Jawab pertanyaan dengan lengkap**: Berikan durasi, tingkat keparahan, dan gejala penyerta
3. **Monitor state**: Gunakan logging untuk melihat state changes
4. **Verifikasi setiap step**: Pastikan setiap agent melakukan tugasnya dengan benar
5. **Test edge cases**: Gejala yang borderline antara Non-Urgen dan Mendesak

## Next Steps

Setelah testing manual, pertimbangkan untuk:

- [ ] Membuat automated tests untuk skenario non-urgen
- [ ] Setup RAG system untuk self-care guide yang lebih spesifik
- [ ] Improve `get_self_care_guide` dengan gejala-specific recommendations
