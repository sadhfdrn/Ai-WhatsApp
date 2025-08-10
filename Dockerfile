# WhatsApp AI Bot with Full AI Models Support
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Deployment and monitoring configuration
ENV LOG_LEVEL=INFO
ENV USE_STREAMING=true
ENV STREAM_MODELS=true
ENV MODEL_DOWNLOAD_ON_DEMAND=true
ENV LOW_MEMORY_MODE=true
ENV WHOOGLE_INSTANCE_ACTIVE=true
ENV WHOOGLE_URL=https://search.whoogle.io

# Docker container detection
ENV DOCKER_CONTAINER=true

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    ffmpeg \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    festival \
    festvox-kallpc16k \
    alsa-utils \
    libasound2-dev \
    pkg-config \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
COPY pyproject.toml uv.lock ./

# Install Node.js dependencies
RUN npm install

# Install Python dependencies with AI models support
RUN pip install --no-cache-dir \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    torchaudio==2.1.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install transformers and AI model dependencies
RUN pip install --no-cache-dir \
    transformers==4.35.2 \
    accelerate==0.24.1 \
    sentence-transformers==2.2.2 \
    torch-audio==0.13.1 \
    datasets==2.14.6 \
    tokenizers==0.15.0 \
    safetensors==0.4.0 \
    huggingface-hub==0.17.3

# Install additional Python dependencies
RUN pip install --no-cache-dir \
    asyncio \
    aiohttp \
    requests \
    beautifulsoup4 \
    trafilatura \
    python-dotenv \
    pytz \
    langdetect \
    gtts \
    pydub \
    speechrecognition \
    pillow \
    psutil \
    sqlalchemy \
    psycopg2-binary \
    alembic

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p model_cache \
    && mkdir -p wa-auth \
    && mkdir -p data \
    && mkdir -p logs

# Set permissions
RUN chmod +x main.py whatsapp_bridge.js

# Configure AI models for streaming (no pre-download)
RUN python3 -c "
import os
os.environ['TRANSFORMERS_CACHE'] = '/app/model_cache'
os.environ['HF_HOME'] = '/app/model_cache'

print('🚀 AI models configured for streaming download on demand')
print('Models will be downloaded and streamed efficiently during first use')
print('This reduces container size and startup time significantly')
"

# Environment configuration for optimal AI performance
ENV TRANSFORMERS_CACHE=/app/model_cache
ENV HF_HOME=/app/model_cache
ENV TOKENIZERS_PARALLELISM=false
ENV OMP_NUM_THREADS=4
ENV MKL_NUM_THREADS=4

# Configuration for unlimited web search with Whoogle instance
ENV SEARCH_ENABLED=true
ENV WHOOGLE_URL=https://search.whoogle.io
ENV WHOOGLE_FALLBACK_URL=https://whoogle.sdf.org
ENV MAX_SEARCH_RESULTS=10
ENV AUTO_SEARCH_ON_QUESTIONS=true
ENV WHOOGLE_INSTANCE_ACTIVE=true

# AI Model configuration with streaming enabled
ENV USE_STREAMING=true
ENV STREAM_MODELS=true
ENV AI_MODEL=microsoft/DialoGPT-small
ENV MAX_RESPONSE_LENGTH=500
ENV TEMPERATURE=0.8
ENV LOW_MEMORY_MODE=true
ENV MODEL_DOWNLOAD_ON_DEMAND=true

# Auto-translation and timezone
ENV AUTO_TRANSLATE=true
ENV TARGET_LANGUAGE=en
ENV TIMEZONE=Africa/Lagos

# Expose ports for health checks and web interface
EXPOSE 8080 3000

# Enhanced health check with comprehensive monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python3 -c "
import requests
import sys
try:
    # Check main health endpoint
    resp = requests.get('http://localhost:8080/health', timeout=5)
    if resp.status_code == 200:
        print('✅ Health check passed')
        sys.exit(0)
    else:
        print(f'❌ Health check failed: {resp.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'❌ Health check error: {e}')
    sys.exit(1)
" || exit 1

# Create startup script
RUN cat > start.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting WhatsApp AI Bot with Full AI Models..."

# Start enhanced health check server in background
python3 -c "
import http.server
import socketserver
import threading
import json
import psutil
import os
from datetime import datetime

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            try:
                # Basic health check
                health_data = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'memory_usage': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'whoogle_enabled': os.getenv('WHOOGLE_INSTANCE_ACTIVE', 'false') == 'true',
                    'streaming_enabled': os.getenv('STREAM_MODELS', 'false') == 'true',
                    'database_url_set': bool(os.getenv('DATABASE_URL'))
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(health_data).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_data = {'status': 'unhealthy', 'error': str(e)}
                self.wfile.write(json.dumps(error_data).encode())
        elif self.path == '/status':
            # Detailed status endpoint
            try:
                status_data = {
                    'whatsapp_bridge': 'running',
                    'ai_models': 'streaming_ready',
                    'database': 'connected' if os.getenv('DATABASE_URL') else 'not_configured',
                    'whoogle_instance': 'active' if os.getenv('WHOOGLE_INSTANCE_ACTIVE') == 'true' else 'inactive'
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(status_data).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Status check failed: {e}'.encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    with socketserver.TCPServer(('0.0.0.0', 8080), HealthHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()
print('🏥 Enhanced health check server started on port 8080')
print('Endpoints: /health, /status')

# Keep the health server running
import time
while True:
    time.sleep(1)
" &

# Start WhatsApp Bridge
echo "🌉 Starting WhatsApp Bridge..."
node whatsapp_bridge.js &

# Wait a moment for bridge to initialize
sleep 5

# Start Python AI Bot
echo "🤖 Starting AI Bot with enhanced models..."
python3 main.py

# Keep container running
wait
EOF

RUN chmod +x start.sh

# Start command
CMD ["./start.sh"]