# WhatsApp AI Bot

## Overview
This AI-powered WhatsApp bot provides conversational AI, voice processing, web search, meme generation, and auto-reply functionality through WhatsApp Web. It offers a personality-driven experience, integrating multiple AI services for rich conversations while ensuring privacy via self-hosted search. The project aims to provide a comprehensive, engaging, and personalized AI interaction experience with persistent personality learning.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
### Core Architecture
The system employs a modular architecture with a central orchestrator (`WhatsAppAIBot`) managing specialized components. A key feature is the comprehensive personality learning framework that persists user communication patterns directly to a GitHub repository, ensuring memory across workflow restarts.

### Configuration
A centralized `Config` class manages settings from environment variables, supporting feature toggles and environment-specific configurations.

### WhatsApp Integration
Utilizes a WhatsApp Web client implementation (Baileys) to process incoming messages through a structured handler system. It maintains user sessions and conversation context, integrating personality learning directly into message processing.

### Enhanced AI Processing Engine
Features a Smart Model Manager for environment-aware progressive model downloading and caching. It dynamically loads function-specific models (conversation, translation, sentiment, TTS, STT) optimized for GitHub Actions or cloud deployments. Includes specialized Hugging Face models, graceful fallbacks to rule-based responses, context awareness for coherent responses, and response caching.

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

### GitHub Repository Personality Persistence System
- **GitHubProfileManager**: Handles personality data storage and Git operations.
- **PersonalityLearner**: Analyzes user messages for communication patterns.
- **StyleMimicker**: Applies learned user style to AI responses.