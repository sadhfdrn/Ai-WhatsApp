# 🚀 Koyeb Deployment Guide for WhatsApp AI Bot

## Overview

This guide helps you deploy the WhatsApp AI Bot to Koyeb with SearXNG search engine and streaming AI models for optimal performance in the cloud.

## 🔧 Prerequisites

1. **Koyeb Account**: Sign up at [koyeb.com](https://www.koyeb.com)
2. **GitHub Repository**: Fork or clone this repository
3. **WhatsApp Credentials**: Generated using the WHATSAPP_CREDENTIALS_GUIDE.md
4. **Environment Variables**: Required API keys and configurations

## 📋 Required Environment Variables

### Core Configuration
```bash
# WhatsApp Credentials (from your wa-auth folder)
WHATSAPP_SESSION_DATA=<base64-encoded-session-data>
WHATSAPP_PHONE_NUMBER=<your-whatsapp-number>

# AI Models Configuration
USE_STREAMING=true
STREAM_MODELS=true
AI_MODEL=microsoft/DialoGPT-small
MAX_RESPONSE_LENGTH=500
TEMPERATURE=0.8
LOW_MEMORY_MODE=true
MODEL_DOWNLOAD_ON_DEMAND=true

# Search Engine - SearXNG
SEARCH_ENABLED=true
SEARXNG_URL=https://searx.be
SEARXNG_FALLBACK_URL=https://search.bus-hit.me
MAX_SEARCH_RESULTS=10
AUTO_SEARCH_ON_QUESTIONS=true
SEARXNG_INSTANCE_ACTIVE=true

# OpenAI API (Optional - for enhanced responses)
OPENAI_API_KEY=<your-openai-api-key>

# Database (Optional - for learning features)
DATABASE_URL=<your-postgresql-database-url>

# Bot Configuration
BOT_NAME=AI Assistant 🤖
BOT_PREFIX=!
AUTO_TRANSLATE=true
TARGET_LANGUAGE=en
TIMEZONE=UTC

# Voice Features
VOICE_ENABLED=true
TTS_LANGUAGE=en
VOICE_SPEED=1.0

# Performance Settings
TRANSFORMERS_CACHE=/app/model_cache
HF_HOME=/app/model_cache
TOKENIZERS_PARALLELISM=false
OMP_NUM_THREADS=2
MKL_NUM_THREADS=2
```

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository
1. Fork this repository to your GitHub account
2. Ensure the `Dockerfile.koyeb` is present in the root directory

### Step 2: Create Koyeb Application
1. Login to your Koyeb dashboard
2. Click "Create App"
3. Choose "GitHub" as the source
4. Select your forked repository

### Step 3: Configure Build Settings
```yaml
Build Command: (leave empty - uses Dockerfile.koyeb)
Dockerfile Path: Dockerfile.koyeb
Port: 8080
Health Check Path: /health
```

### Step 4: Set Environment Variables
Add all the environment variables listed above in the Koyeb environment variables section.

### Step 5: Advanced Configuration
```yaml
Instance Type: Nano (1 CPU, 512MB RAM) - minimum
          or: Micro (1 CPU, 1GB RAM) - recommended
Regions: Choose closest to your users
Auto-scaling: Enabled (1-3 instances)
Health Check: Enabled
  - Path: /health
  - Port: 8080
  - Initial Delay: 120s
  - Timeout: 15s
  - Interval: 45s
```

## 🎯 SearXNG vs Whoogle Advantages

### Why SearXNG is Better:
1. **JSON API Support**: Native JSON responses for better parsing
2. **Multiple Search Engines**: Aggregates results from multiple sources
3. **Better Privacy**: More privacy-focused than single-engine solutions
4. **Faster Responses**: Optimized for programmatic access
5. **More Reliable**: Multiple fallback instances available
6. **Better Results**: Combines results from Google, Bing, DuckDuckGo, etc.

### SearXNG Configuration:
- **Primary Instance**: https://searx.be
- **Fallback Instances**: 
  - https://search.bus-hit.me
  - https://searx.tiekoetter.com
- **Format**: JSON for programmatic access
- **Categories**: General search with multi-engine support

## 🤖 AI Models Streaming

The bot uses streaming AI models optimized for cloud deployment:

### Model Configuration:
- **Primary Model**: microsoft/DialoGPT-small (300MB)
- **Download**: On-demand streaming during first use
- **Caching**: Intelligent model caching for faster responses
- **Memory**: Low-memory mode for efficient resource usage

### Supported Models:
1. **Conversational AI**: DialoGPT family
2. **Text Generation**: GPT-2 variants
3. **Sentiment Analysis**: RoBERTa-based models
4. **Translation**: Helsinki-NLP/opus-mt models
5. **Voice**: gTTS and SpeechRecognition

### Model Streaming Benefits:
- ✅ **Faster Startup**: No pre-downloading of large models
- ✅ **Resource Efficient**: Models loaded only when needed
- ✅ **Auto-scaling**: Perfect for Koyeb's auto-scaling
- ✅ **Cost Effective**: Pay only for resources used
- ✅ **Always Updated**: Latest model versions automatically

## 📊 Monitoring & Health Checks

### Health Endpoints:
- **Basic Health**: `GET /health`
- **Detailed Status**: `GET /status` (if implemented)

### Health Check Response:
```json
{
  "status": "healthy",
  "platform": "koyeb",
  "timestamp": "2025-08-10T21:30:00.000Z",
  "memory_usage": 45.2,
  "searxng_enabled": true,
  "streaming_enabled": true,
  "models_ready": true,
  "database_url_set": true,
  "deployment_target": "koyeb"
}
```

### Monitoring Features:
- **CPU Usage**: Tracked via Koyeb metrics
- **Memory Usage**: Optimized for cloud deployment
- **Response Times**: SearXNG search latency monitoring
- **Model Loading**: AI model download and caching status

## 🔧 Troubleshooting

### Common Issues:

#### 1. **Build Failures**
```bash
# Check Dockerfile.koyeb exists
# Verify all dependencies in pyproject.toml
# Ensure Node.js dependencies are in package.json
```

#### 2. **Health Check Failures**
```bash
# Verify port 8080 is exposed
# Check environment variables are set
# Ensure health check endpoint is accessible
```

#### 3. **WhatsApp Connection Issues**
```bash
# Verify WHATSAPP_SESSION_DATA is correctly encoded
# Check WhatsApp credentials are not expired
# Ensure phone number format is correct
```

#### 4. **SearXNG Search Failures**
```bash
# Test primary SearXNG instance: https://searx.be
# Verify fallback instances are accessible
# Check SEARXNG_INSTANCE_ACTIVE=true
```

#### 5. **AI Model Loading Issues**
```bash
# Verify STREAM_MODELS=true
# Check MODEL_DOWNLOAD_ON_DEMAND=true
# Ensure sufficient memory allocation
```

## 📈 Performance Optimization

### Recommended Settings:
- **Instance**: Micro (1 CPU, 1GB RAM)
- **Auto-scaling**: 1-3 instances
- **Health checks**: Every 45 seconds
- **Model caching**: Enabled
- **Low memory mode**: Enabled

### Expected Performance:
- **Startup Time**: 60-120 seconds (includes model download)
- **Response Time**: 1-3 seconds for AI responses
- **Search Time**: 2-5 seconds for SearXNG queries
- **Memory Usage**: 400-800MB depending on models loaded

## 💡 Advanced Features

### Database Integration:
- **PostgreSQL**: For conversation learning and analytics
- **Style Learning**: Adapts to user communication patterns
- **Analytics**: Tracks usage patterns and performance

### Voice Features:
- **Text-to-Speech**: gTTS integration
- **Voice Messages**: Automatic transcription
- **Multi-language**: Support for multiple languages

### Security Features:
- **Environment Variables**: Secure secret management
- **Rate Limiting**: Built-in protection against abuse
- **Privacy**: SearXNG provides enhanced privacy protection

## 🎉 Deployment Complete!

Once deployed, your bot will:
1. ✅ Connect to WhatsApp Web automatically
2. ✅ Download AI models on-demand
3. ✅ Use SearXNG for enhanced search capabilities
4. ✅ Scale automatically based on usage
5. ✅ Provide health monitoring for uptime tracking

### Next Steps:
1. Monitor the deployment logs in Koyeb dashboard
2. Test WhatsApp connectivity by sending a message
3. Verify search functionality with queries
4. Check AI model responses for quality
5. Set up monitoring alerts for production use

### Support:
- **Documentation**: Check README.md for detailed features
- **Koyeb Support**: https://www.koyeb.com/docs
- **Issues**: Create GitHub issues for bug reports

Happy deployment! 🚀