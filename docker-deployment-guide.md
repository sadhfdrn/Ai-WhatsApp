# 🚀 WhatsApp AI Bot - Docker Deployment Guide

## Comprehensive Deployment Monitoring & Logging

This deployment guide includes comprehensive logging, health monitoring, database connection tracking, and deployment verification to ensure everything works perfectly in Docker.

## 🔧 Prerequisites

### Required Environment Variables

```bash
# Database Configuration (Required for learning features)
DATABASE_URL=postgresql://username:password@host:port/database

# OpenAI API (Required for advanced AI responses)
OPENAI_API_KEY=your_openai_api_key_here

# WhatsApp Credentials (Required)
WHATSAPP_PHONE_NUMBER=+1234567890
WHATSAPP_SESSION_PATH=/app/wa-auth

# Optional but Recommended
GITHUB_TOKEN=your_github_token_for_personality_persistence
```

### Optional Configuration Variables (Pre-configured in Dockerfile)

```bash
# Deployment Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
USE_STREAMING=true               # Enable AI model streaming
STREAM_MODELS=true               # Stream models on-demand
MODEL_DOWNLOAD_ON_DEMAND=true    # Download models when needed
LOW_MEMORY_MODE=true             # Optimize for memory usage

# Search Configuration
WHOOGLE_INSTANCE_ACTIVE=true     # Enable privacy-preserving search
WHOOGLE_URL=https://search.whoogle.io

# Performance Tuning
TOKENIZERS_PARALLELISM=false     # Disable for Docker
OMP_NUM_THREADS=4                # CPU optimization
MKL_NUM_THREADS=4                # Math library optimization
```

## 🏗️ Build & Deploy

### 1. Build the Docker Image

```bash
# Build with deployment monitoring enabled
docker build -t whatsapp-ai-bot:latest .
```

### 2. Run with Environment Variables

#### Option A: Using Environment File

Create `.env.docker`:
```bash
DATABASE_URL=postgresql://user:pass@db:5432/whatsapp_bot
OPENAI_API_KEY=sk-your-key-here
WHATSAPP_PHONE_NUMBER=+1234567890
GITHUB_TOKEN=ghp_your_token_here
```

Run:
```bash
docker run -d \
  --name whatsapp-ai-bot \
  --env-file .env.docker \
  -p 8080:8080 \
  -v $(pwd)/wa-auth:/app/wa-auth \
  -v $(pwd)/logs:/app/logs \
  whatsapp-ai-bot:latest
```

#### Option B: Direct Environment Variables

```bash
docker run -d \
  --name whatsapp-ai-bot \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e OPENAI_API_KEY="sk-your-key-here" \
  -e WHATSAPP_PHONE_NUMBER="+1234567890" \
  -e GITHUB_TOKEN="ghp_your_token_here" \
  -p 8080:8080 \
  -v $(pwd)/wa-auth:/app/wa-auth \
  -v $(pwd)/logs:/app/logs \
  whatsapp-ai-bot:latest
```

### 3. With PostgreSQL Database

#### Using Docker Compose (Recommended)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: whatsapp_bot
      POSTGRES_USER: botuser
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U botuser -d whatsapp_bot"]
      interval: 10s
      timeout: 5s
      retries: 5

  whatsapp-bot:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: "postgresql://botuser:secure_password@postgres:5432/whatsapp_bot"
      OPENAI_API_KEY: "sk-your-key-here"
      WHATSAPP_PHONE_NUMBER: "+1234567890"
      GITHUB_TOKEN: "ghp_your_token_here"
    ports:
      - "8080:8080"
    volumes:
      - ./wa-auth:/app/wa-auth
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s

volumes:
  postgres_data:
```

Deploy:
```bash
docker-compose up -d
```

## 📊 Deployment Monitoring & Verification

### 1. Health Check Endpoints

The bot exposes comprehensive health monitoring on port 8080:

#### `/health` - Basic Health Status
```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-10T20:40:31.346228",
  "uptime": 123.45,
  "deployment_checks_passed": true
}
```

#### `/status` - Detailed System Status
```bash
curl http://localhost:8080/status
```

Response:
```json
{
  "status": "running",
  "timestamp": "2025-08-10T20:40:31.620253",
  "deployment_ready": true,
  "whatsapp_connected": true,
  "database_available": true,
  "ai_models_ready": true
}
```

### 2. Deployment Logs

The bot creates comprehensive deployment logs:

#### Startup Monitoring
```bash
# View deployment summary
docker logs whatsapp-ai-bot | grep "DEPLOYMENT"

# View database connection timing
docker logs whatsapp-ai-bot | grep "Database"

# View AI model initialization
docker logs whatsapp-ai-bot | grep "Model Manager"

# View WhatsApp connection status
docker logs whatsapp-ai-bot | grep "WhatsApp"
```

#### Deployment Report
```bash
# View detailed deployment report
docker exec whatsapp-ai-bot cat /app/logs/deployment_report.json
```

### 3. Real-time Monitoring

#### Container Health
```bash
# Check container health status
docker ps --filter "name=whatsapp-ai-bot"

# View health check history
docker inspect whatsapp-ai-bot | jq '.[0].State.Health'

# Monitor resource usage
docker stats whatsapp-ai-bot
```

#### Application Logs
```bash
# Follow live logs
docker logs -f whatsapp-ai-bot

# Filter by component
docker logs whatsapp-ai-bot 2>&1 | grep "DeploymentMonitor"
docker logs whatsapp-ai-bot 2>&1 | grep "database"
docker logs whatsapp-ai-bot 2>&1 | grep "AI"
```

### 4. Database Connection Verification

```bash
# Check database connectivity and timing
curl http://localhost:8080/status | jq '.database_available'

# View database stats from deployment report
docker exec whatsapp-ai-bot cat /app/logs/deployment_report.json | jq '.deployment_info.environment_variables.DATABASE_URL'
```

## 🔍 Troubleshooting

### Database Connection Issues

1. **Check DATABASE_URL is set:**
```bash
docker exec whatsapp-ai-bot printenv DATABASE_URL
```

2. **Verify database connectivity:**
```bash
# From inside container
docker exec whatsapp-ai-bot python3 -c "
from database.models import get_database_engine
engine = get_database_engine()
print('✅ Database connected' if engine else '❌ Database failed')
"
```

3. **Check timing issues:**
```bash
# View database connection timing
docker logs whatsapp-ai-bot | grep "Database.*took.*s"
```

### WhatsApp Connection Issues

1. **Check credentials:**
```bash
# Verify wa-auth directory
docker exec whatsapp-ai-bot ls -la /app/wa-auth/

# Check environment variables
docker exec whatsapp-ai-bot printenv | grep WHATSAPP
```

2. **Monitor connection status:**
```bash
# Check WhatsApp connection logs
docker logs whatsapp-ai-bot | grep "WhatsApp.*connect"
```

### AI Model Issues

1. **Check streaming configuration:**
```bash
curl http://localhost:8080/status | jq '.ai_models_ready'
```

2. **Monitor model loading:**
```bash
# View model initialization timing
docker logs whatsapp-ai-bot | grep "Model.*initialized.*took.*s"
```

## 📈 Performance Optimization

### Memory Usage
- AI models stream on-demand (reduces startup memory)
- Low memory mode enabled by default
- Model cache persisted in `/app/model_cache`

### Startup Time
- Health checks start after 90 seconds
- Models download only when needed
- Database connections are lazy-initialized

### Network Optimization
- Whoogle instance for privacy-preserving search
- Multiple fallback URLs configured
- Connection pooling for database

## 🔒 Security Best Practices

1. **Environment Variables:**
   - Store sensitive data in environment variables
   - Use Docker secrets for production
   - Never commit credentials to code

2. **Volume Mounting:**
   - Mount wa-auth directory for credential persistence
   - Mount logs directory for monitoring
   - Use named volumes for database persistence

3. **Network Security:**
   - Only expose port 8080 for health checks
   - Use internal networks in docker-compose
   - Configure firewall rules appropriately

## 📋 Deployment Checklist

- [ ] Database URL configured and accessible
- [ ] OpenAI API key set and valid
- [ ] WhatsApp credentials available
- [ ] Health endpoints responding (`:8080/health`, `:8080/status`)
- [ ] Deployment report generated (`/app/logs/deployment_report.json`)
- [ ] Database connection timing logged
- [ ] AI models streaming correctly
- [ ] WhatsApp Web connection established
- [ ] Logs directory mounted and writable

## 🚀 Production Deployment

For production deployments, consider:

1. **Load Balancing:** Use multiple container instances
2. **Database:** Use managed PostgreSQL service (AWS RDS, Google Cloud SQL)
3. **Monitoring:** Integrate with Prometheus/Grafana
4. **Logging:** Use centralized logging (ELK stack, Fluentd)
5. **Backup:** Regular database backups and wa-auth persistence
6. **Security:** Use secrets management, TLS encryption, network policies

## 🆘 Support

If deployment issues persist:

1. Check the deployment report: `/app/logs/deployment_report.json`
2. Review health endpoints: `:8080/health` and `:8080/status`
3. Examine container logs: `docker logs whatsapp-ai-bot`
4. Verify all environment variables are set correctly
5. Ensure database connectivity and timing are acceptable

The enhanced logging system provides comprehensive deployment monitoring to help identify and resolve any issues quickly.