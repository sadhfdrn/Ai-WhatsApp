# WhatsApp AI Bot Deployment Guide

## 🚀 Full AI Models + Unlimited Web Search Deployment

This deployment configuration includes:
- ✅ All 5 specified AI models (DialoGPT, FLAN-T5, translation, sentiment, embeddings)
- ✅ Streaming responses enabled
- ✅ Unlimited web search capabilities
- ✅ Self-hosted Whoogle search instance
- ✅ Full timezone and translation support
- ✅ Production-ready configuration

## 📋 Prerequisites

1. **Docker & Docker Compose** installed
2. **WhatsApp Web credentials** (from your current setup)
3. **Minimum 4GB RAM** (recommended 8GB for optimal AI performance)
4. **2+ CPU cores** for concurrent AI model processing

## 🔧 Deployment Steps

### 1. Prepare Your Environment

```bash
# Clone or copy your WhatsApp bot files
# Ensure you have wa-auth/ directory with credentials

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with your preferences:

```env
# AI Models (Pre-configured for your specified models)
USE_STREAMING=true
AI_MODEL=microsoft/DialoGPT-small
LOW_MEMORY_MODE=false

# Unlimited Web Search
SEARCH_ENABLED=true
WHOOGLE_URL=http://whoogle-search:5000
AUTO_SEARCH_ON_QUESTIONS=true
MAX_SEARCH_RESULTS=10

# Timezone & Translation
TIMEZONE=Africa/Lagos
AUTO_TRANSLATE=true
TARGET_LANGUAGE=en

# Optional: OpenAI API for enhanced responses
OPENAI_API_KEY=your_openai_key_here
```

### 3. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f whatsapp-ai-bot
```

### 4. Monitor Deployment

```bash
# Check AI model loading progress
docker-compose logs whatsapp-ai-bot | grep "Downloading\|Loading\|✅"

# Health check
curl http://localhost:8080/health

# Check Whoogle search
curl http://localhost:5000
```

## 🎯 AI Models Configuration

Your deployment includes these models (total ~1.5GB):

1. **microsoft/DialoGPT-small** (300MB) - Conversational AI
2. **google/flan-t5-small** (300MB) - Text generation & tasks
3. **Helsinki-NLP/opus-mt-en-mul** (300MB) - Multi-language translation
4. **cardiffnlp/twitter-roberta-base-sentiment-latest** (500MB) - Sentiment analysis
5. **sentence-transformers/all-MiniLM-L6-v2** (80MB) - Text embeddings

## 🔍 Web Search Features

The bot automatically searches when:
- You ask questions starting with "what", "who", "where", "when", "how", "why"
- You use commands like "search", "find", "look up"
- It detects it needs current information to answer properly

**Search Sources:**
- Primary: Self-hosted Whoogle (unlimited, private)
- Fallback: Public Whoogle instances
- Real-time results integration

## 🌊 Streaming Configuration

Streaming is enabled by default for:
- **Conversation responses** - Real-time token generation
- **Search results** - Progressive result loading
- **Translation** - Live language processing
- **Voice synthesis** - Streaming audio generation

## 📊 Production Optimizations

### Resource Allocation
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G        # Maximum memory usage
      cpus: '2.0'       # CPU cores allocated
    reservations:
      memory: 2G        # Guaranteed memory
      cpus: '1.0'       # Guaranteed CPU
```

### Model Caching
- Models are pre-downloaded during build
- Persistent volume for model cache
- Faster startup times after initial deployment

### Health Monitoring
```bash
# Continuous health monitoring
watch -n 30 'curl -s http://localhost:8080/health'

# Container resource usage
docker stats whatsapp-ai-bot
```

## 🔧 Customization Options

### Modify Search Behavior
```env
# Search on every question (current setting)
AUTO_SEARCH_ON_QUESTIONS=true

# Only search on explicit commands
AUTO_SEARCH_ON_QUESTIONS=false

# Increase search results
MAX_SEARCH_RESULTS=15
```

### AI Model Tuning
```env
# More creative responses
TEMPERATURE=0.9

# More conservative responses  
TEMPERATURE=0.5

# Longer responses
MAX_RESPONSE_LENGTH=1000

# Enable low-memory mode (uses smaller models)
LOW_MEMORY_MODE=true
```

### Performance Scaling
```env
# Increase parallel processing
OMP_NUM_THREADS=8
MKL_NUM_THREADS=8

# Enable GPU if available
CUDA_VISIBLE_DEVICES=0
```

## 🚨 Troubleshooting

### AI Models Not Loading
```bash
# Check available memory
docker exec whatsapp-ai-bot free -h

# Force model re-download
docker-compose down -v
docker-compose up --build
```

### Search Not Working
```bash
# Check Whoogle service
docker-compose logs whoogle-search

# Test search directly
curl "http://localhost:5000/search?q=test"
```

### Performance Issues
```bash
# Increase memory limits in docker-compose.yml
memory: 6G

# Enable low-memory mode
LOW_MEMORY_MODE=true
```

## 📈 Monitoring & Maintenance

### Daily Checks
```bash
# Check all services
docker-compose ps

# Check logs for errors
docker-compose logs --tail=50 whatsapp-ai-bot
```

### Weekly Maintenance
```bash
# Update images
docker-compose pull
docker-compose up -d

# Clean up old containers
docker system prune -f
```

### Backup Important Data
```bash
# Backup WhatsApp credentials
tar -czf wa-auth-backup.tar.gz wa-auth/

# Backup learned personality data
tar -czf data-backup.tar.gz data/
```

## 🎉 Success Indicators

Your deployment is successful when you see:

1. ✅ "All AI models pre-downloaded successfully!"
2. ✅ "Enhanced AI System initialized"
3. ✅ "WhatsApp Web connected successfully!"
4. ✅ Health check returns "OK" on port 8080
5. ✅ Bot responds to messages with streaming
6. ✅ Web search returns real results
7. ✅ Translation works for non-English messages

## 📞 Production Deployment

For production use:

1. **Use environment secrets** instead of .env file
2. **Set up SSL/TLS** for external access
3. **Configure log aggregation** (ELK stack, etc.)
4. **Set up monitoring** (Prometheus/Grafana)
5. **Regular backups** of wa-auth and data volumes

Your WhatsApp AI bot is now deployed with full AI capabilities, unlimited web search, and streaming responses!