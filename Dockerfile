# Multi-stage build for Medical Triage Agent
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy frontend files
COPY web_ui/frontend/package*.json ./web_ui/frontend/
RUN cd web_ui/frontend && npm ci

COPY web_ui/frontend/ ./web_ui/frontend/
RUN cd web_ui/frontend && npm run build

# Stage 2: Python backend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY medical_triage_agent/ ./medical_triage_agent/
COPY web_ui/app.py ./web_ui/
COPY web_ui/__init__.py ./web_ui/

# Copy built frontend from stage 1 (vite outputs to ../static from frontend dir)
COPY --from=frontend-builder /app/web_ui/static ./web_ui/static/

# Install Python dependencies
RUN uv sync --frozen

# Expose port
ENV PORT=8080
EXPOSE 8080

# Set environment variables
ENV GOOGLE_GENAI_USE_VERTEXAI=true
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["uv", "run", "python", "web_ui/app.py"]

