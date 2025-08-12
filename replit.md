# WhatsApp Bot

## Overview
A simple, pure Node.js WhatsApp bot that connects via WhatsApp Web using Baileys. The bot responds to basic commands and maintains a clean, minimal codebase without AI processing or complex features. It includes health monitoring and connection management for reliable operation.

## User Preferences
- Preferred communication style: Simple, everyday language
- Security: wa-auth directory should be in gitignore to protect authentication data
- Architecture: Pure Node.js implementation without Python or AI dependencies
- Health Checks: Expose port for health monitoring
- Commands: Implement .ping command for basic bot functionality

## System Architecture
### Core Architecture
Simple Node.js WhatsApp bot with minimal dependencies. The main application (`main.js`) handles WhatsApp Web connection, message processing, and basic command responses.

### Configuration
Environment variables manage WhatsApp credentials (WHATSAPP_CREDS) and server port (PORT).

### WhatsApp Integration
Uses Baileys library for WhatsApp Web connectivity with authentication state management and message handling.

### Command System
Enhanced command processor with reaction support:
- **.ping**: Returns bot status, uptime, and network speed with ⚡ reaction
- **.tag [message]**: Tags all group members silently with custom message and 👥 reaction
- Command reactions provide instant feedback to users
- Network speed measurement for performance monitoring
- Group member tagging with mention functionality

### Health Monitoring
HTTP server on port 8080 provides health check endpoint for deployment monitoring.

## External Dependencies
### WhatsApp Integration
- **baileys**: Official WhatsApp Web client library from GitHub (WhiskeySockets/Baileys)
- **@hapi/boom**: Error handling for Baileys
- **pino**: Logging library
- **qrcode-terminal**: QR code generation for initial setup

### Core Node.js Libraries
- **http**: Built-in HTTP server for health checks
- **fs**: File system operations for credential management
- **path**: Path utilities

## Recent Changes

### August 12, 2025 - Complete Node.js Conversion
- **Removed Python and AI Components**: Completely converted from Python-based AI bot to pure Node.js implementation
  - Deleted all Python files: main.py, config.py, bot/, database/, utils/, templates/
  - Removed AI processing, personality learning, web search, meme generation
  - Eliminated Python dependencies: pyproject.toml, uv.lock, requirements files
  - Cleaned up model cache and AI-related files
- **Pure Node.js Architecture**: Created new main.js with minimal WhatsApp functionality
  - Enhanced command processor supporting .ping command with reactions
  - Health monitoring on port 8080 for deployment status
  - Connection management with automatic reconnection logic
  - Message parsing and response system with emoji reactions
  - Network speed measurement for performance monitoring
- **Dependency Cleanup**: Removed unnecessary Node.js packages
  - Uninstalled: cheerio, fluent-ffmpeg, jimp, sharp (AI/image processing)
  - Switched from baileys-mod to official Baileys GitHub repository
  - Kept essential packages: baileys (from GitHub), @hapi/boom, pino, qrcode-terminal, cheerio
- **Fixed Connection Issues**: Resolved stream error conflicts causing disconnections
  - Improved error handling and reconnection strategy
  - Added exponential backoff for reconnection attempts
  - Enhanced connection state management
- **Workflow Updates**: Updated workflows to use new main.js instead of Python bridge
  - Removed "WhatsApp AI Bot" and "WhatsApp Bridge" workflows
  - Added new "WhatsApp Bot" workflow running Node.js application
- **Enhanced Commands**: Added .tag command for group member tagging
  - .tag [message] tags all group members with custom message
  - Includes 👥 reaction and silent mention functionality
  - Works only in groups with proper error handling
- **Documentation Update**: Updated replit.md to reflect pure Node.js architecture