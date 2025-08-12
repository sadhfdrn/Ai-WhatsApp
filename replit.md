# WhatsApp Bot

## Overview
This project is a pure Node.js WhatsApp bot designed for simplicity and reliability. It connects via WhatsApp Web using Baileys, offering basic command responses, health monitoring, and robust connection management. The bot's vision is to provide a clean, minimal, and efficient communication tool without relying on AI processing or complex features, focusing on core WhatsApp functionalities and easy extensibility.

## User Preferences
- Preferred communication style: Simple, everyday language
- Security: wa-auth directory should be in gitignore to protect authentication data
- Architecture: Pure Node.js implementation without Python or AI dependencies
- Health Checks: Expose port for health monitoring
- Commands: Implement .ping command for basic bot functionality

## System Architecture
### Core Architecture
A simple Node.js WhatsApp bot leveraging the Baileys library for WhatsApp Web connectivity. The `main.js` application manages connections, message processing, and command execution. It features a modular plugin system for easy command extension.

### Configuration
Environment variables (`WHATSAPP_CREDS`, `PORT`, `PREFIX`, `OWNER_NUMBER`) are used for managing credentials, server port, command prefix, and optional owner number for welcome messages.

### WhatsApp Integration
Utilizes the Baileys library for WhatsApp Web integration, including authentication state management and message handling. Enhanced features are provided through the `@neoxr/wb` framework.

### Plugin System
An enhanced modular plugin architecture, inspired by `@neoxr/wb`, enables automatic loading and management of command plugins. Key features include:
- **Commands**: `ping` (bot status, uptime, network speed), `menu`/`help`/`commands` (formatted bot menu), `tag` (silently tags group members), `tagall` (loudly tags group members), and `gstatus` (detailed group member information).
- **Smart Reactions**: Initial command emojis, followed by success (✅) or failure (❌) indicators, which auto-remove after 2 seconds.
- **Enhanced Anti-Spam**: A 3-second cooldown per command per user.
- **Bot Detection**: Advanced filtering of bot messages using multiple detection patterns.
- **Message Caching**: Temporary message storage for improved performance.
- **Session Management**: Enhanced connection state tracking.
- **Customizable Prefix**: Configurable via the `PREFIX` environment variable.
- **Professional Menu**: Boxed layout with comprehensive command listings.
- **Interactive Messages**: Support for button messages, list messages, poll messages, carousel messages, quick reply messages, location sharing, and contact cards.

### Health Monitoring
An HTTP server on port 8080 provides a health check endpoint for monitoring deployment status.

### System Design Choices
The architecture prioritizes a pure Node.js environment, avoiding Python or AI dependencies for a lightweight and focused solution. It emphasizes modularity through its plugin system and robust connection management for high availability. UI/UX considerations are addressed through professional menu formatting, smart emoji reactions, and interactive message capabilities to enhance user experience.

## External Dependencies
- **@neoxr/wb**: An enhanced WhatsApp bot framework built on Baileys.
- **baileys**: The core WhatsApp Web client library (from GitHub - WhiskeySockets/Baileys).
- **@hapi/boom**: Used for error handling.
- **pino**: Employed for logging.
- **qrcode-terminal**: Generates QR codes for initial setup.
- **cheerio**: Used for HTML/XML parsing in advanced message processing.
- **http**: Node.js built-in module for health checks.
- **fs**: Node.js built-in module for file system operations (credential management).
- **path**: Node.js built-in module for path utilities.