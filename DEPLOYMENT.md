# Deployment Guide - Medical Triage Agent

Panduan lengkap untuk deploy Medical Triage Agent ke production.

## 🚀 Quick Start (5 Menit)

### Prerequisites
```bash
# Set project
export PROJECT_ID=your-project-id
export REGION=us-central1

# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### Deploy ke Cloud Run (Recommended)
```bash
cd /home/seryu/projects/bpjs-agentic-ai

# Build and deploy in one command
gcloud builds submit --config cloudbuild.yaml

# Atau manual:
# 1. Build frontend
cd web_ui/frontend && npm install && npm run build && cd ../..

# 2. Build and push image
gcloud builds submit --tag gcr.io/${PROJECT_ID}/medical-triage-agent:latest

# 3. Deploy
gcloud run deploy medical-triage-agent \
  --image gcr.io/${PROJECT_ID}/medical-triage-agent:latest \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=true"
```

### Get Service URL
```bash
gcloud run services describe medical-triage-agent \
  --region ${REGION} \
  --format 'value(status.url)'
```

### Verify Deployment
```bash
# Health check
curl https://your-service-url/health

# Expected: {"status":"ok","app":"medical-triage-agent"}
```

---

## 📋 Prerequisites

1. **Google Cloud Project** dengan billing enabled
2. **Google Cloud SDK** (`gcloud`) terinstall dan ter-authenticate
3. **Docker** (untuk containerized deployment)
4. **Environment Variables** yang diperlukan:
   - `GOOGLE_CLOUD_PROJECT`: Project ID Anda
   - `GOOGLE_CLOUD_LOCATION`: Region (e.g., `us-central1`)
   - `GOOGLE_GENAI_USE_VERTEXAI=true`

---

## 🚀 Opsi Deployment

### Option 1: Google Cloud Run (Recommended)

**Keuntungan:**
- ✅ Serverless, auto-scaling
- ✅ Pay-per-use
- ✅ Support WebSocket
- ✅ Easy deployment dengan Docker
- ✅ HTTPS included

#### Step 1: Build dan Push Docker Image

```bash
cd /home/seryu/projects/bpjs-agentic-ai

# Set project
export PROJECT_ID=your-project-id
export REGION=us-central1

# Build image
gcloud builds submit --tag gcr.io/${PROJECT_ID}/medical-triage-agent:latest

# Atau build lokal lalu push
docker build -t gcr.io/${PROJECT_ID}/medical-triage-agent:latest .
docker push gcr.io/${PROJECT_ID}/medical-triage-agent:latest
```

#### Step 2: Deploy ke Cloud Run

```bash
# Deploy dengan environment variables
gcloud run deploy medical-triage-agent \
  --image gcr.io/${PROJECT_ID}/medical-triage-agent:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=true" \
  --service-account your-service-account@${PROJECT_ID}.iam.gserviceaccount.com
```

**Catatan:**
- `--allow-unauthenticated`: Hapus jika ingin authentication
- `--memory 2Gi`: Sesuaikan dengan kebutuhan
- `--timeout 3600`: 1 jam untuk long-running conversations
- `--max-instances 10`: Limit concurrent instances

#### Step 3: Verifikasi

```bash
# Get service URL
gcloud run services describe medical-triage-agent --region ${REGION} --format 'value(status.url)'

# Test health endpoint
curl https://your-service-url.run.app/health
```

#### Step 4: Update Frontend untuk Production

Jika frontend perlu di-build ulang dengan production URL:

```bash
cd web_ui/frontend
# Update vite.config.ts jika perlu (untuk API proxy)
npm run build
```

### Option 2: Vertex AI Agent Engine

**Keuntungan:**
- ✅ Fully managed ADK deployment
- ✅ Built-in session management
- ✅ Observability integration
- ✅ Auto-scaling

**Keterbatasan:**
- ⚠️ Tidak support custom WebSocket UI (menggunakan ADK UI default)
- ⚠️ Perlu build wheel file

#### Step 1: Install Deployment Dependencies

```bash
cd /home/seryu/projects/bpjs-agentic-ai
uv sync --extra deployment
```

#### Step 2: Build Wheel File

```bash
# Build package
uv build

# Wheel file akan ada di dist/
ls dist/medical_triage_agent-*.whl
```

#### Step 3: Deploy ke Agent Engine

Buat file `deployment/deploy.py`:

```python
import os
from pathlib import Path
from google.cloud import aiplatform
from vertexai.preview import agent_engines
from google.adk.apps import AdkApp
from medical_triage_agent.agent import root_agent

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
WHEEL_FILE = str(Path(__file__).parent.parent / "dist" / "medical_triage_agent-0.1.0-py3-none-any.whl")

aiplatform.init(project=PROJECT_ID, location=LOCATION)

app = AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

remote_agent = agent_engines.create(
    app,
    display_name="medical-triage-agent",
    requirements=[WHEEL_FILE],
    extra_packages=[WHEEL_FILE],
    env_vars={
        "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
        "GOOGLE_CLOUD_LOCATION": LOCATION,
        "GOOGLE_GENAI_USE_VERTEXAI": "true",
    }
)

print(f"Deployed to: {remote_agent.resource_name}")
```

#### Step 4: Run Deployment

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
python deployment/deploy.py
```

### Option 3: Docker Compose (Local/VM)

Untuk deployment di VM atau server sendiri:

#### Step 1: Build Image

```bash
docker build -t medical-triage-agent:latest .
```

#### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  medical-triage-agent:
    image: medical-triage-agent:latest
    ports:
      - "8000:8080"
    environment:
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}
      - GOOGLE_GENAI_USE_VERTEXAI=true
      - PORT=8080
    volumes:
      # Mount credentials if using service account key
      - ./credentials.json:/app/credentials.json:ro
    restart: unless-stopped
```

#### Step 3: Run

```bash
docker-compose up -d
```

### Option 4: Docker Local

```bash
# Build
docker build -t medical-triage-agent:latest .

# Run
docker run -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=your-project-id \
  -e GOOGLE_CLOUD_LOCATION=us-central1 \
  -e GOOGLE_GENAI_USE_VERTEXAI=true \
  medical-triage-agent:latest
```

### Option 5: Manual Deployment (VM/Server)

#### Step 1: Setup Server

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3.12 python3-pip nodejs npm curl

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Step 2: Clone dan Setup

```bash
cd /opt
git clone <your-repo> medical-triage-agent
cd medical-triage-agent

# Install Python dependencies
uv sync

# Build frontend
cd web_ui/frontend
npm install
npm run build
cd ../..
```

#### Step 3: Setup Systemd Service

Create `/etc/systemd/system/medical-triage-agent.service`:

```ini
[Unit]
Description=Medical Triage Agent
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/medical-triage-agent
Environment="GOOGLE_CLOUD_PROJECT=your-project-id"
Environment="GOOGLE_CLOUD_LOCATION=us-central1"
Environment="GOOGLE_GENAI_USE_VERTEXAI=true"
Environment="PORT=8080"
ExecStart=/opt/medical-triage-agent/.venv/bin/uvicorn web_ui.app:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Step 4: Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable medical-triage-agent
sudo systemctl start medical-triage-agent
```

---

## 🔐 Authentication & Security

### Service Account

Untuk production, gunakan Service Account:

```bash
# Create service account
gcloud iam service-accounts create medical-triage-agent \
  --display-name="Medical Triage Agent Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:medical-triage-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create credentials.json \
  --iam-account=medical-triage-agent@${PROJECT_ID}.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Secret Manager (Recommended)

Untuk environment variables sensitif:

```bash
# Create secrets
echo -n "your-project-id" | gcloud secrets create google-cloud-project --data-file=-
echo -n "us-central1" | gcloud secrets create google-cloud-location --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding google-cloud-project \
  --member="serviceAccount:medical-triage-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Update `web_ui/app.py` untuk read dari Secret Manager:

```python
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

---

## 📊 Monitoring & Logging

### Cloud Logging

Logs otomatis terkirim ke Cloud Logging jika menggunakan Cloud Run atau Agent Engine.

### Custom Metrics

Tambahkan custom metrics di `web_ui/app.py`:

```python
from google.cloud import monitoring_v3

def record_metric(metric_name: str, value: float):
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}"
    # ... implement metric recording
```

---

## 🔄 CI/CD dengan Cloud Build

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build frontend
  - name: 'node:20'
    entrypoint: 'npm'
    args: ['ci']
    dir: 'web_ui/frontend'
  
  - name: 'node:20'
    entrypoint: 'npm'
    args: ['run', 'build']
    dir: 'web_ui/frontend'

  # Build and push Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/medical-triage-agent:$SHORT_SHA', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/medical-triage-agent:$SHORT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'medical-triage-agent'
      - '--image'
      - 'gcr.io/$PROJECT_ID/medical-triage-agent:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'

images:
  - 'gcr.io/$PROJECT_ID/medical-triage-agent:$SHORT_SHA'
```

Trigger build:

```bash
gcloud builds submit --config cloudbuild.yaml
```

---

## 🧪 Testing Deployment

### Health Check

```bash
curl https://your-service-url/health
```

Expected response:
```json
{"status":"ok","app":"medical-triage-agent"}
```

### WebSocket Test

```javascript
const ws = new WebSocket('wss://your-service-url/ws/user123/session456');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
ws.send(JSON.stringify({type: 'text', content: 'Halo'}));
```

---

## 📝 Checklist Pre-Deployment

- [ ] Environment variables configured
- [ ] Google Cloud APIs enabled (Vertex AI, Secret Manager)
- [ ] Service account created with proper permissions
- [ ] Frontend built (`npm run build`)
- [ ] Docker image tested locally
- [ ] Health endpoint working
- [ ] WebSocket connection working
- [ ] Logging configured
- [ ] Monitoring alerts set up
- [ ] Backup strategy in place

---

## 🆘 Troubleshooting

### Error: Permission Denied

```bash
# Verify service account permissions
gcloud projects get-iam-policy ${PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:medical-triage-agent@${PROJECT_ID}.iam.gserviceaccount.com"
```

### Error: WebSocket Connection Failed

- Check Cloud Run timeout settings (should be 3600s for long conversations)
- Verify WebSocket support in Cloud Run (enabled by default)
- Check CORS settings in `app.py`

### Error: Out of Memory

- Increase `--memory` in Cloud Run deployment
- Check for memory leaks in agent code
- Monitor memory usage in Cloud Monitoring

### Error: Service Not Found

```bash
# Check service status
gcloud run services describe medical-triage-agent --region us-central1

# Check logs
gcloud run services logs read medical-triage-agent --region us-central1 --limit 50
```

---

## 📊 Example Deployment Success

Berikut adalah contoh deployment yang berhasil:

### Service URL
**Production URL:** https://medical-triage-agent-429582292005.us-central1.run.app

### Deployment Details
- **Project:** japanese-coach-458816
- **Region:** us-central1
- **Service Name:** medical-triage-agent
- **Status:** ✅ Deployed and serving 100% of traffic

### Endpoints
- **Health Check:** https://medical-triage-agent-429582292005.us-central1.run.app/health
- **Web UI:** https://medical-triage-agent-429582292005.us-central1.run.app/
- **WebSocket:** wss://medical-triage-agent-429582292005.us-central1.run.app/ws/{user_id}/{session_id}

### Configuration
- **Memory:** 2Gi
- **CPU:** 2
- **Timeout:** 3600s (1 hour)
- **Max Instances:** 10
- **Port:** 8080
- **Authentication:** Public (unauthenticated)

### Update Deployment

Untuk update deployment dengan code terbaru:

```bash
cd /home/seryu/projects/bpjs-agentic-ai
./deploy_cloud_run.sh
```

Atau manual:
```bash
# Build and push
gcloud builds submit --tag gcr.io/japanese-coach-458816/medical-triage-agent:latest .

# Deploy
gcloud run deploy medical-triage-agent \
  --image gcr.io/japanese-coach-458816/medical-triage-agent:latest \
  --region us-central1
```

### Monitoring

Monitor deployment di:
- **Cloud Console:** https://console.cloud.google.com/run/detail/us-central1/medical-triage-agent?project=japanese-coach-458816
- **Logs:** `gcloud run services logs read medical-triage-agent --region us-central1`

---

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [ADK Deployment Guide](https://google.github.io/adk-docs/deploy/)
