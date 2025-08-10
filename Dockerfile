# WhatsApp AI Bot with Full AI Models Support
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

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
    openai \
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

# Pre-download AI models to reduce startup time
RUN python3 -c "
import os
os.environ['TRANSFORMERS_CACHE'] = '/app/model_cache'
os.environ['HF_HOME'] = '/app/model_cache'

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM, pipeline
    from sentence_transformers import SentenceTransformer
    
    print('📥 Pre-downloading AI models...')
    
    # DialoGPT for conversation
    print('Downloading DialoGPT-small...')
    AutoTokenizer.from_pretrained('microsoft/DialoGPT-small')
    AutoModelForCausalLM.from_pretrained('microsoft/DialoGPT-small')
    
    # FLAN-T5 for text generation
    print('Downloading FLAN-T5-small...')
    AutoTokenizer.from_pretrained('google/flan-t5-small')
    AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small')
    
    # Translation model
    print('Downloading translation model...')
    pipeline('translation', model='Helsinki-NLP/opus-mt-en-mul', max_length=512)
    
    # Sentiment analysis
    print('Downloading sentiment model...')
    pipeline('sentiment-analysis', model='cardiffnlp/twitter-roberta-base-sentiment-latest')
    
    # Embeddings model
    print('Downloading embeddings model...')
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    print('✅ All AI models pre-downloaded successfully!')
    
except Exception as e:
    print(f'⚠️ Model pre-download failed: {e}')
    print('Models will be downloaded on first use.')
"

# Environment configuration for optimal AI performance
ENV TRANSFORMERS_CACHE=/app/model_cache
ENV HF_HOME=/app/model_cache
ENV TOKENIZERS_PARALLELISM=false
ENV OMP_NUM_THREADS=4
ENV MKL_NUM_THREADS=4

# Configuration for unlimited web search
ENV SEARCH_ENABLED=true
ENV WHOOGLE_URL=https://search.benbusby.com
ENV MAX_SEARCH_RESULTS=10
ENV AUTO_SEARCH_ON_QUESTIONS=true

# AI Model configuration
ENV USE_STREAMING=true
ENV AI_MODEL=microsoft/DialoGPT-small
ENV MAX_RESPONSE_LENGTH=500
ENV TEMPERATURE=0.8
ENV LOW_MEMORY_MODE=false

# Auto-translation and timezone
ENV AUTO_TRANSLATE=true
ENV TARGET_LANGUAGE=en
ENV TIMEZONE=Africa/Lagos

# Expose port for health checks
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Create startup script
RUN cat > start.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting WhatsApp AI Bot with Full AI Models..."

# Start health check server in background
python3 -c "
import http.server
import socketserver
import threading

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    with socketserver.TCPServer(('', 8080), HealthHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()
print('Health check server started on port 8080')

# Keep the script running
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