# WhatsApp Bot

## Overview
This project is a pure Node.js WhatsApp bot built with the GitHub version of Baileys. It provides a clean, reliable WhatsApp Web connection with comprehensive plugin support, interactive messaging capabilities, and robust spam protection. The bot focuses on core WhatsApp functionalities with easy extensibility through a modular plugin architecture.

## User Preferences
- Preferred communication style: Simple, everyday language
- Security: wa-auth directory should be in gitignore to protect authentication data
- Architecture: Pure Node.js implementation with GitHub Baileys (no @neoxr/wb or baileys-mod dependencies)
- Health Checks: Expose port for health monitoring
- Single Workflow: Only one WhatsApp Bot workflow running to avoid session conflicts
- Message Processing: vv and save commands should process actual message content (images, videos, voice, text) not just message IDs
- Stealth Mode: vv, autovv, and save commands operate completely silently - no confirmation messages or reactions in current chat, all feedback goes to owner DM only

## System Architecture
### Core Architecture
A simple Node.js WhatsApp bot leveraging the Baileys library for WhatsApp Web connectivity. The `main.js` application manages connections, message processing, and command execution. It features a modular plugin system for easy command extension.

### Configuration
Environment variables (`WHATSAPP_CREDS`, `PORT`, `PREFIX`, `OWNER_NUMBER`) are used for managing credentials, server port, command prefix, and optional owner number for welcome messages.

### WhatsApp Integration
Utilizes the official GitHub Baileys library for WhatsApp Web integration, including authentication state management and message handling. Clean implementation without external framework dependencies.

### Plugin System
An enhanced modular plugin architecture, inspired by `@neoxr/wb`, enables automatic loading and management of command plugins. Key features include:
- **Commands**: `ping` (bot status, uptime, network speed), `menu`/`help`/`commands` (formatted bot menu), `tag` (silently tags group members), `tagall` (loudly tags group members), `gstatus` (detailed group member information), `vv` (remove view-once restriction and download actual media), `autovv` (toggle auto view-once processing), and `save` (save actual message content including media to DM).
- **Enhanced Message Processing**: Full implementation of message content extraction and media downloading for vv and save commands. Now processes actual images, videos, voice messages, and text content instead of just message IDs.
- **Message Caching**: Temporary message storage (1000 messages) for reliable quoted message retrieval and processing.
- **Smart Reactions**: Initial command emojis, followed by success (✅) or failure (❌) indicators, which auto-remove after 2 seconds.
- **Enhanced Anti-Spam**: A 3-second cooldown per command per user.
- **Bot Detection**: Advanced filtering of bot messages using multiple detection patterns.
- **Session Management**: Enhanced connection state tracking.
- **Customizable Prefix**: Configurable via the `PREFIX` environment variable.
- **Professional Menu**: Boxed layout with comprehensive command listings.
- **Interactive Messages**: Support for button messages, list messages, poll messages, carousel messages, quick reply messages, location sharing, and contact cards.

### Health Monitoring
An HTTP server on port 8080 provides a health check endpoint for monitoring deployment status.

### System Design Choices
The architecture prioritizes a pure Node.js environment, avoiding Python or AI dependencies for a lightweight and focused solution. It emphasizes modularity through its plugin system and robust connection management for high availability. UI/UX considerations are addressed through professional menu formatting, smart emoji reactions, and interactive message capabilities to enhance user experience.

## External Dependencies
- **baileys**: The core WhatsApp Web client library (from GitHub - WhiskeySockets/Baileys).
- **@hapi/boom**: Used for error handling.
- **pino**: Employed for logging.
- **qrcode-terminal**: Generates QR codes for initial setup.
- **cheerio**: Used for HTML/XML parsing in message processing.
- **http**: Node.js built-in module for health checks.
- **fs**: Node.js built-in module for file system operations (credential management).
- **path**: Node.js built-in module for path utilities.