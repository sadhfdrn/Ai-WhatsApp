# WhatsApp AI Bot

## Overview
This AI-powered WhatsApp bot provides conversational AI, voice processing, web search, meme generation, and auto-reply functionality through WhatsApp Web. It offers a personality-driven experience, integrating multiple AI services for rich conversations while ensuring privacy via self-hosted search. The project aims to provide a comprehensive, engaging, and personalized AI interaction experience with persistent personality learning.

## User Preferences
- Preferred communication style: Simple, everyday language
- Security: wa-auth directory should be in gitignore to protect authentication data
- AI Models: Stream models directly from Hugging Face - NO external API keys required (OpenAI, etc.)
- AI Architecture: Self-hosted AI models using Transformers library with streaming download
- Health Checks: Expose port for health monitoring in Docker deployments
- Search: Keep Whoogle instance active for privacy-preserving web searches

## System Architecture
### Core Architecture
The system employs a modular architecture with a central orchestrator (`WhatsAppAIBot`) managing specialized components. A key feature is the comprehensive personality learning framework that persists user communication patterns directly to a GitHub repository, ensuring memory across workflow restarts.

### Configuration
A centralized `Config` class manages settings from environment variables, supporting feature toggles and environment-specific configurations.

### WhatsApp Integration
Utilizes a WhatsApp Web client implementation (Baileys) to process incoming messages through a structured handler system. It maintains user sessions and conversation context, integrating personality learning directly into message processing.

### Enhanced AI Processing Engine
Features a Smart Model Manager with advanced streaming capabilities for environment-aware model loading. It dynamically loads function-specific models (conversation, translation, sentiment, TTS, STT) with three strategies:
- **Progressive Loading**: For GitHub Actions with disk caching
- **Full Caching**: For frequently used small models
- **Streaming with On-Demand Loading**: For cloud deployments with minimal memory footprint and lazy loading wrappers
Includes specialized Hugging Face models, pipeline-based loading for efficiency, graceful fallbacks, context awareness, and optimized memory usage.

### Enhanced Voice Processing
An advanced voice cloning engine provides AI-powered TTS/STT with personality-based voice profiles, prioritizing specialized Hugging Face models and falling back to traditional engines. It supports multi-format audio, language configuration, and progressive voice pattern analysis.

### Web Search Integration
Employs Whoogle for privacy-preserving web searches, with multiple search engine fallbacks and content extraction using Trafilatura for clean web page content.

### Auto-Reply System
Learns user messaging patterns to generate realistic and proactive auto-replies with configurable delays to simulate human-like response timing.

### Personality Engine
Offers dynamic and configurable personality traits, including humor integration, proactive conversation starters, and adjustable confidence levels in responses.

### Meme Generation
A template-based system uses Pillow (PIL) for image manipulation, automatically positioning and styling text on meme templates with customizable fonts, colors, and layouts.

### Utility Architecture
Includes centralized utility functions for text sanitization and formatting, enhanced colored logging for debugging, and comprehensive error handling.

## External Dependencies

### Enhanced AI and Machine Learning Stack
- **Smart Model Manager**: Custom environment-aware model management.
- **Hugging Face Transformers**: Advanced model loading, streaming, and caching.
- **Microsoft DialoGPT**: Default conversational AI model.
- **Specialized AI Models**: For translation, sentiment analysis, summarization, and advanced voice (TTS/STT).
- **Accelerate Library**: Memory optimization and model loading acceleration.
- **Sentence Transformers**: Text understanding and embedding generation.

### WhatsApp Integration
- **Baileys**: WhatsApp Web client library for Node.js/Python integration.

### Web Search and Content
- **Whoogle Search**: Privacy-focused Google search proxy.
- **Trafilatura**: Content extraction from web pages.
- **Requests**: HTTP client for web search and content fetching.

### Image Processing
- **Pillow (PIL)**: Python Imaging Library for image manipulation.

### Core Python Libraries
- **asyncio**: Asynchronous programming.
- **dotenv**: Environment variable management.
- **logging**: Application logging.
- **tempfile**: Temporary file management.
- **json**: Data serialization.
- **datetime**: Time and date handling.

### Dual Personality Learning System
- **Database-Based Learning**: Primary system using PostgreSQL with sophisticated models (UserProfile, Conversation, CommonPhrase, EmojiUsage, ChatStyleLearning, ResponseSuggestion) for real-time pattern analysis and response suggestion
- **GitHub Repository Persistence**: Backup system for personality data storage
- **ChatStyleAnalyzer**: Analyzes communication patterns, formality levels, response preferences
- **PersonalityLearner**: Learns from user messages and updates personality profiles
- **StyleMimicker**: Applies learned user style to AI responses
- **DatabaseManager**: Orchestrates all database operations and learning integration

## Recent Changes (August 2025)
- Added comprehensive .gitignore including wa-auth/ directory for security
- Enhanced Dockerfile with streaming AI models instead of pre-downloading
- Added health check endpoints (/health, /status) on port 8080
- Implemented on-demand model streaming with lazy loading wrappers
- Improved Whoogle search integration with fallback URLs
- Enhanced model manager with pipeline-based loading for better efficiency

### Comprehensive Deployment Logging (Latest Update - August 2025)
- **DeploymentLogger**: Complete system monitoring with startup timing, resource tracking, and network connectivity tests
- **Database Connection Monitoring**: Lazy initialization with timing logs, graceful fallbacks, connection tests, and performance statistics
- **Health Check Endpoints**: Real-time status monitoring on port 8080 with `/health` and `/status` endpoints
- **Enhanced Main.py**: Integrated deployment readiness assessment, comprehensive startup logging, health server management
- **Docker Deployment Guide**: Complete deployment guide with monitoring, troubleshooting, and verification steps
- **Deployment Reports**: Automated JSON reports saved to `logs/deployment_report.json` with full system analysis
- **Database Resilience**: Database operations continue gracefully when DATABASE_URL unavailable during startup
- **Performance Timing**: All database operations and model loading include precise timing measurements
- **Environment Detection**: Automatic detection of deployment environment (Docker, Replit, Railway, Heroku)
- **Resource Monitoring**: Memory, disk, CPU usage tracking with system resource optimization settings

### GitHub Integration Removal (Latest Update)
- **Removed GitHub Chat Style Saving**: App now exclusively uses database for personality learning
- **Updated Whoogle URLs**: Fixed connection issues with working Whoogle instances (search.whoogle.io)
- **Cleaned Documentation**: Removed all OpenAI API key requirements from deployment guides
- **Database-Only Learning**: Personality patterns, conversation memory, and style mimicking now database-driven
- **Simplified Architecture**: Removed GitHub profile manager dependencies from chat processing