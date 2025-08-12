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
Environment variables manage WhatsApp credentials (WHATSAPP_CREDS), server port (PORT), customizable command prefix (PREFIX), and optional owner number for welcome messages (OWNER_NUMBER).

### WhatsApp Integration
Uses Baileys library for WhatsApp Web connectivity with authentication state management and message handling.

### Command System
Enhanced command processor with smart reaction system and customizable prefix:
- **ping**: Returns bot status, uptime, and network speed with ⚡ reaction
- **tag [message]**: Tags all group members silently with custom message and 👥 reaction
- **tagall**: Tags all group members loudly without requiring a message and 🔔 reaction
- Customizable prefix via PREFIX env var (., /, !, etc.) or null for no prefix
- Smart reactions: Initial command emoji → Success (✅) or Failure (❌) → Auto-removal after 2 seconds
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
- **Enhanced Commands**: Added group tagging commands with smart reactions
  - .tag [message] tags all group members silently with custom message (👥 reaction)
  - .tagall tags all group members loudly without requiring message (🔔 reaction)
  - Both commands work only in groups with proper error handling
  - Loud tagging shows numbered list with each member on separate line for clarity
- **Smart Reaction System**: Enhanced user feedback with status-aware reactions
  - Initial command reactions show processing (⚡, 👥, 🔔)
  - Success/failure indicators with green check (✅) or red X (❌)
  - Auto-removal of reactions after 2 seconds to keep chats clean
  - Comprehensive error handling with proper reaction feedback
- **Customizable Command Prefix**: Flexible prefix configuration via environment variables
  - PREFIX=. (default dot prefix for .ping, .tag, .tagall)
  - PREFIX=/ (slash prefix for /ping, /tag, /tagall)
  - PREFIX=! (exclamation prefix for !ping, !tag, !tagall)
  - PREFIX=null (no prefix required - just ping, tag, tagall)
  - Dynamic prefix handling in command processing and error messages
- **Documentation Update**: Updated replit.md to reflect pure Node.js architecture and new features

### August 12, 2025 - Welcome Message Feature
- **Welcome Message System**: Added automatic welcome message functionality after successful connection
  - Sends welcome message to configured owner number when bot connects
  - Welcome message includes connection time, bot status, prefix information, and usage instructions
  - OWNER_NUMBER environment variable configuration for targeting welcome messages
  - Prevents duplicate welcome messages with hasWelcomeBeenSent flag
  - Graceful handling when no owner number is configured
  - Enhanced connection handler to be async for welcome message support