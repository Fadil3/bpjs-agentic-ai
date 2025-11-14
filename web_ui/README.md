# Custom Web UI untuk Medical Triage Agent

Custom Web UI yang dibuat khusus untuk menampilkan informasi triase medis dengan visualisasi yang lebih baik.

## Fitur

### 1. Chat Interface
- Percakapan real-time dengan agent
- History percakapan yang jelas
- Input yang user-friendly

### 2. Triage Level Indicator
- Badge dengan color coding:
  - 🔴 **Merah** = Gawat Darurat
  - 🟡 **Kuning** = Mendesak
  - 🟢 **Hijau** = Non-Urgen
- Justifikasi triage level

### 3. Structured Data Display
- **Gejala yang Ditemukan**: Gejala utama, gejala penyerta, durasi, tingkat keparahan
- **Analisis Klinis**: Kriteria BPJS yang terpenuhi, justifikasi
- **Tindakan yang Diambil**: Info ambulans, appointment, atau self-care guide
- **Dokumentasi SOAP**: Format SOAP yang terstruktur

---

## 🚀 Quick Start - Menjalankan Backend

### Cara Paling Mudah

```bash
cd /home/seryu/projects/bpjs-agentic-ai
./start_custom_ui.sh
```

Script ini akan otomatis:
- ✅ Load environment variables
- ✅ Kill process lama di port 8000
- ✅ Start backend FastAPI
- ✅ Serve React frontend (jika sudah di-build)

### Manual Setup

#### 1. Pastikan Environment Variables

File `.env` harus ada di root project:
```bash
cd /home/seryu/projects/bpjs-agentic-ai
cat .env
```

Harus ada:
```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

#### 2. Pastikan Authentication

```bash
gcloud auth application-default login
```

#### 3. Jalankan Backend

```bash
cd web_ui
uv run python app.py
```

Backend akan running di: **http://localhost:8000**

---

## 🎨 React Frontend Setup

Frontend sekarang menggunakan React dengan Vite, TypeScript, dan shadcn/ui components.

### Prerequisites

1. **Node.js dan npm** harus sudah terinstall
   ```bash
   node --version  # Should be v18+ or v20+
   npm --version
   ```

2. **Backend harus running** di port 8000
   ```bash
   cd web_ui
   uv run python app.py
   ```

### Setup Steps

#### 1. Install Dependencies

```bash
cd web_ui/frontend
npm install
```

Ini akan menginstall semua dependencies termasuk:
- React 19
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui components
- React Markdown

#### 2. Development Mode

Jalankan frontend di development mode (dengan hot reload):

```bash
npm run dev
```

Frontend akan berjalan di `http://localhost:5173` dengan proxy ke backend di `http://localhost:8000`.

#### 3. Production Build

Build untuk production:

```bash
npm run build
```

Build output akan di-export ke `web_ui/static/` dan akan di-serve oleh FastAPI backend.

#### 4. Run Backend dengan React Build

Setelah build, jalankan backend seperti biasa:

```bash
cd web_ui
uv run python app.py
```

Backend akan serve React app dari `static/` directory.

---

## Development Workflow

### Option 1: Separate Dev Servers (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd /home/seryu/projects/bpjs-agentic-ai
./start_custom_ui.sh
```

**Terminal 2 - Frontend (React Dev Server):**
```bash
cd /home/seryu/projects/bpjs-agentic-ai/web_ui/frontend
npm install  # Hanya pertama kali
npm run dev
```

**Akses:**
- Frontend (Vite): http://localhost:5173
- Backend: http://localhost:8000

### Option 2: Build and Serve (Production-like)

**Terminal 1 - Build Frontend:**
```bash
cd web_ui/frontend
npm run build
```

**Terminal 2 - Run Backend:**
```bash
cd web_ui
uv run python app.py
```

**Akses:** http://localhost:8000 (Backend serve React build)

---

## Tech Stack

- **Backend**: FastAPI + WebSocket
- **Frontend**: React 19 dengan TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v4
- **Components**: shadcn/ui (Radix UI primitives)
- **Markdown**: React Markdown
- **Integration**: ADK Runner dengan `run_async()` untuk non-Live API models

---

## Features

✅ Real-time WebSocket communication  
✅ Markdown rendering dengan syntax highlighting  
✅ Agent transition indicators dengan badges  
✅ Copy message functionality  
✅ Responsive design  
✅ Dark theme  
✅ Smooth animations  
✅ Type-safe dengan TypeScript  

---

## Struktur File

```
web_ui/
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/        # shadcn/ui components
│   │   │   ├── ChatMessagesView.tsx
│   │   │   ├── InputForm.tsx
│   │   │   └── ConnectionStatus.tsx
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── global.css
│   │   └── utils.ts
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── static/                # Build output (generated)
│   ├── index.html
│   └── assets/
├── app.py                 # FastAPI backend
└── README.md              # This file
```

---

## Perbedaan dengan ADK Web UI Built-in

| Fitur | ADK Web UI | Custom UI |
|-------|-----------|-----------|
| Chat Interface | ✅ | ✅ |
| Triage Level Badge | ❌ | ✅ |
| Color Coding | ❌ | ✅ |
| Structured Data Display | ❌ | ✅ |
| Symptoms Panel | ❌ | ✅ |
| Reasoning Panel | ❌ | ✅ |
| Execution Panel | ❌ | ✅ |
| SOAP Documentation | ❌ | ✅ |

---

## Catatan tentang Streaming

**Model yang Digunakan**: `gemini-2.5-flash`

Karena model ini **tidak mendukung Live API**, custom UI menggunakan `run_async()` untuk streaming events, bukan `run_live()` dengan `LiveRequestQueue`.

**Untuk Live API (voice/video streaming):**
- Perlu model yang mendukung Live API seperti `gemini-2.5-flash-native-audio-preview-09-2025`
- Gunakan `run_live()` dengan `LiveRequestQueue` untuk bidirectional streaming
- Lihat dokumentasi: https://google.github.io/adk-docs/get-started/streaming/quickstart-streaming/

**Implementasi Saat Ini:**
- Menggunakan `run_async()` untuk request-response streaming
- Support text input/output
- Streaming events dari agent ke client
- Tidak support real-time voice/video (karena model tidak mendukung Live API)

---

## Port Configuration

Backend default berjalan di port **8000**. Untuk mengubah port:

```bash
PORT=8080 uv run python app.py
```

Atau set di `.env`:
```
PORT=8080
```

---

## Troubleshooting

### Port 8000 sudah digunakan

```bash
# Kill process di port 8000
lsof -ti:8000 | xargs kill -9

# Atau gunakan port lain
PORT=8080 uv run python app.py
```

### Environment variables tidak ter-load

Pastikan `.env` file ada di root project:
```bash
cd /home/seryu/projects/bpjs-agentic-ai
ls -la .env
```

### WebSocket connection refused

**Penyebab:** Backend belum running

**Solusi:**
1. Pastikan backend sudah running (lihat Terminal 1)
2. Tunggu sampai muncul: `Uvicorn running on http://0.0.0.0:8000`
3. Baru start frontend

### WebSocket Connection Refused (Frontend)

**Error:** `ECONNREFUSED 127.0.0.1:8000`

**Solution:**
1. Pastikan backend sudah running:
   ```bash
   cd web_ui
   uv run python app.py
   ```
2. Check apakah port 8000 sudah digunakan:
   ```bash
   lsof -i :8000
   ```
3. Jika port sudah digunakan, kill process atau ubah port di `app.py`

### Google Cloud authentication error

```bash
# Re-authenticate
gcloud auth application-default login

# Verify
gcloud auth application-default print-access-token
```

### npm install fails

**Solution:**
```bash
# Clear cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors

**Solution:**
```bash
# Check TypeScript version
npx tsc --version

# Build to see all errors
npm run build
```

### Vite Proxy Not Working

Jika WebSocket proxy tidak bekerja, check `vite.config.ts`:
- Pastikan `target` adalah `ws://127.0.0.1:8000` untuk WebSocket
- Pastikan `ws: true` sudah di-set

---

## Verifikasi Backend Running

Setelah backend running, test dengan:

```bash
curl http://localhost:8000/health
```

Response yang diharapkan:
```json
{"status":"ok","app":"medical-triage-agent"}
```

---

## Logs

Backend akan menampilkan logs real-time di terminal:
- ✅ WebSocket connections
- ✅ Agent interactions  
- ✅ Function calls
- ✅ Errors (jika ada)

---

## Catatan

- Custom UI ini menggunakan WebSocket untuk real-time communication
- Data structured di-parse dari agent responses (JSON)
- UI akan otomatis update ketika agent mengirim structured data
- Responsive design untuk desktop dan mobile

---

## Next Steps

Setelah setup selesai:
1. Test WebSocket connection
2. Test dengan berbagai skenario triage
3. Customize UI sesuai kebutuhan
4. Deploy ke production (lihat `../DEPLOYMENT.md`)
