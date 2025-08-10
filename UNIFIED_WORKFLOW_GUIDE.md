# Unified WhatsApp AI Bot Workflow Guide

## Overview
All three previous workflows have been consolidated into a single optimized workflow: `whatsapp-ai-bot-unified.yml`

## Key Features

### Manual Trigger Only
- **No automatic scheduling** - Workflow only starts when manually triggered
- **Manual dispatch** via GitHub Actions UI
- **Self-triggering mechanism** using GH_TOKEN to restart every 5 hours

### Self-Sustaining Operation
- Runs for ~4.8 hours (290 minutes timeout)
- **Auto-triggers next run** using GH_TOKEN at the end
- Creates continuous operation loop without cron scheduling
- Brief 30-second pause between runs

### Enhanced Features
- **Personality learning** with GitHub repository persistence
- **Smart model caching** and memory optimization
- **Comprehensive disk cleanup** for maximum available space
- **Enhanced error handling** and crash recovery
- **Automatic profile statistics** and commit summaries

## Required Secret: GH_TOKEN

### Setup Instructions
1. Go to GitHub Settings > Developer Settings > Personal Access Tokens
2. Create a new **Fine-grained personal access token** or **Classic token**
3. Grant the following permissions:
   - `repo` (full repository access)
   - `actions` (to trigger workflows)
   - `metadata` (to read repository metadata)
4. Add the token to repository secrets as `GH_TOKEN`

### Why GH_TOKEN is Needed
- **Repository persistence**: Push personality learning data
- **Self-triggering**: Restart workflow automatically every 5 hours
- **Enhanced authentication**: Better than default GITHUB_TOKEN for cross-workflow operations

## Workflow Architecture

### Consolidated Components
- **Python 3.11** with optimized dependencies
- **Node.js 18** for WhatsApp Web integration
- **AI model caching** with Hugging Face transformers
- **Whoogle search** instance deployment
- **Voice processing** capabilities
- **Personality learning system** with repository persistence

### Memory and Performance Optimizations
- **Aggressive disk cleanup** - removes unnecessary packages (~15GB freed)
- **Smart dependency caching** - faster subsequent runs
- **Memory-optimized model loading** - prevents OOM errors
- **CPU-only PyTorch** - no GPU overhead

### Personality Learning Integration
- **Real-time pattern analysis** from user messages
- **Automatic repository commits** every 10 interactions
- **Profile statistics** and learning progress tracking
- **Cross-restart memory** through GitHub repository storage

## Usage Instructions

### Starting the Bot
1. Go to GitHub Actions tab in your repository
2. Select "WhatsApp AI Bot - Unified Deployment with Personality Learning"
3. Click "Run workflow" > "Run workflow" button
4. Bot will start and run continuously with 5-hour auto-restart cycles

### Monitoring
- Check GitHub Actions logs for real-time status
- View commit history for personality learning progress
- Monitor WhatsApp Web QR code generation in logs
- Check `/data/` directory for personality profiles

### Stopping the Bot
- **Cancel the running workflow** in GitHub Actions
- Bot will complete current cycle but won't auto-trigger next run
- All personality data remains saved in repository

## Benefits of Unified Workflow

### Simplified Management
- **Single workflow file** instead of three separate ones
- **Consistent configuration** across all features
- **Unified logging** and error handling
- **Streamlined maintenance**

### Enhanced Reliability
- **Self-healing** auto-restart mechanism
- **Improved error recovery** with comprehensive logging
- **Memory leak prevention** through regular cleanup
- **Automatic dependency management**

### Cost Efficiency
- **Optimal resource usage** with smart caching
- **Reduced GitHub Actions minutes** through efficient operations
- **Minimal storage overhead** with cleanup procedures

## Technical Specifications

### Runtime Environment
- **Ubuntu Latest** runner
- **290-minute timeout** (just under 5 hours)
- **Continuous operation** through self-triggering
- **Enhanced memory management** with cleanup procedures

### Dependencies Optimized
- **Core Python packages** for AI and WhatsApp integration
- **PyTorch CPU** version for model operations
- **Transformers library** with streaming support
- **WhatsApp Baileys** for Web integration

### Storage Strategy
- **Persistent personality data** in `/data/` directory
- **Version-controlled learning** through Git commits
- **Automatic backup** through repository storage
- **Cross-deployment continuity** maintained

**Status**: Ready for production use with GH_TOKEN setup
**Manual Start**: Use GitHub Actions workflow dispatch
**Continuous Operation**: Self-triggering every 5 hours automatically