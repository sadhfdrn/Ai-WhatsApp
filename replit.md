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

### Plugin System
Enhanced modular plugin architecture with @neoxr/wb-inspired features and smart reaction system:
- **Plugin Manager**: Automatic loading and management of command plugins
- **ping**: Returns bot status, uptime, and network speed with ⚡ reaction
- **menu/help/commands**: Shows formatted bot menu with all available commands with 📋 reaction
- **tag [message]**: Tags all group members silently with custom message and 👥 reaction
- **tagall**: Tags all group members loudly without requiring a message and 🔔 reaction
- **gstatus**: Shows detailed group member information (admin status, role, join date) with 👤 reaction
- **Enhanced Anti-Spam**: 3-second cooldown per command per user (inspired by @neoxr/wb)
- **Bot Detection**: Advanced bot message filtering using multiple detection patterns
- **Message Caching**: Temporary message storage for improved performance
- **Session Management**: Enhanced connection state tracking and management
- Customizable prefix via PREFIX env var (., /, !, etc.) or null for no prefix
- Smart reactions: Initial command emoji → Success (✅) or Failure (❌) → Auto-removal after 2 seconds
- Extensible plugin system for easy addition of new commands
- Professional menu formatting with boxed layout and comprehensive command listing

### Health Monitoring
HTTP server on port 8080 provides health check endpoint for deployment monitoring.

## External Dependencies
### WhatsApp Integration
- **@neoxr/wb**: Enhanced WhatsApp bot framework built on top of Baileys (v5.10.14)
- **baileys**: Official WhatsApp Web client library from GitHub (WhiskeySockets/Baileys)
- **@hapi/boom**: Error handling for Baileys and @neoxr/wb
- **pino**: Logging library for enhanced debugging
- **qrcode-terminal**: QR code generation for initial setup
- **cheerio**: HTML/XML parsing for advanced message processing

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
  - Automatic owner number extraction from WhatsApp credentials for targeting welcome messages
  - Prevents duplicate welcome messages with hasWelcomeBeenSent flag
  - Graceful handling when no owner number is configured
  - Enhanced connection handler to be async for welcome message support

### August 12, 2025 - Group Status Command
- **gstatus Command**: Added comprehensive group member information command
  - Shows detailed information about yourself or replied-to user in groups
  - Displays admin status (Member, Admin, Super Admin/Creator)
  - Shows phone number, name, user ID, and role information
  - Includes group metadata (name, member count, creation date)
  - Works with reply feature - reply to someone's message and use .gstatus to see their info
  - Enhanced message parsing to handle quoted messages (replies)
  - Added sender identification and quoted message context
  - Group-only command with proper validation and error handling

### August 12, 2025 - Plugin System Architecture
- **Plugin System Implementation**: Complete conversion to modular plugin architecture
  - Created PluginManager class for automatic plugin loading and command routing
  - Separated commands into individual plugin files (menu.js, ping.js, grouputils.js)
  - Enhanced command processing with automatic plugin discovery and execution
  - Maintained backward compatibility with existing command structure
  - Added professional menu system with formatted command listing
- **Improved Health Server**: Enhanced port conflict handling with automatic port selection
  - Dynamic port selection when default port 8080 is in use
  - Better error handling for server startup
- **Professional Menu Design**: Created formatted menu command with boxed layout
  - Comprehensive command listing with categories and descriptions
  - Bot information display including loaded plugin count
  - Usage tips and examples for better user experience
  - Multiple command aliases (menu, help, commands) for accessibility

### August 12, 2025 - @neoxr/wb Integration & Enhancement
- **Full @neoxr/wb Integration**: Successfully integrated @neoxr/wb library with Baileys for enhanced WhatsApp bot functionality
  - **Library Architecture**: Uses @neoxr/wb Component system with Baileys, Function utilities, Config management, and Spam detection
  - **Enhanced Client**: Initialized @neoxr/wb Baileys client with type '--neoxr-v1' and advanced configuration options
  - **Bot Detection**: Advanced bot message filtering using @neoxr/wb patterns (3EB0*, BAE*, dash patterns)
  - **Session Management**: Enhanced session handling with ./wa-auth directory and bypass_disappearing features
  - **Event System**: Comprehensive event handling (connect, ready, message, disconnect, error) with @neoxr/wb client
- **Advanced Spam Protection**: Integrated @neoxr/wb Spam detection system
  - **Configurable Thresholds**: RESET_TIMER (3s), HOLD_TIMER (3min), PERMANENT_THRESHOLD (3), NOTIFY_THRESHOLD (4), BANNED_THRESHOLD (5)
  - **Real-time Detection**: Per-user, per-command cooldown system with advanced spam detection algorithms
  - **Automatic Management**: Spam detection integrated into message processing with cooldown tracking
  - **Show Options**: Configurable spam logging ('all', 'command-only', 'message-only', 'spam-only', 'none')
- **Enhanced Message Processing**: @neoxr/wb-powered message handling and command execution
  - **Message Registration**: client.register('message') for enhanced message processing
  - **Advanced Parsing**: Enhanced message data extraction with support for all WhatsApp message types
  - **Command Detection**: Smart command detection with prefix support and no-prefix mode compatibility
  - **Interactive Support**: Built-in support for @neoxr/wb interactive message features
- **Library Benefits**: Key advantages gained from @neoxr/wb integration
  - **Memory Efficient**: No Selenium/browser overhead compared to other WhatsApp libraries
  - **Plugin Architecture**: Modular command system with automatic plugin discovery
  - **Multi-Device Support**: Native WhatsApp multi-device compatibility
  - **TypeScript Ready**: Full TypeScript support for enhanced development
  - **Active Development**: Frequently updated library (latest version integrated)
- **Maintained Compatibility**: All existing functionality preserved while gaining @neoxr/wb benefits
  - **Plugin System**: Existing plugins work seamlessly with enhanced @neoxr/wb features
  - **Command Structure**: All commands maintain compatibility while gaining spam protection
  - **Interactive Features**: Enhanced with @neoxr/wb capabilities for better user experience

### August 12, 2025 - Interactive Messages Implementation
- **Advanced WhatsApp Features**: Added comprehensive interactive message capabilities
  - **Button Messages**: Interactive buttons with custom actions and responses
  - **List Messages**: Scrollable menu lists with multiple sections and options
  - **Poll Messages**: Voting polls with single or multi-select options
  - **Carousel Messages**: Card-style layouts with multiple swipeable items
  - **Quick Reply Messages**: Fast response buttons for common actions
  - **Location Sharing**: Send GPS coordinates and address information
  - **Contact Cards**: Share contact information with vCard format
- **Interactive Plugin System**: New plugin architecture for advanced messaging
  - **MessageUtils Class**: Utility library for creating interactive messages
  - **Response Handling**: Automatic detection and processing of user interactions
  - **Demo Commands**: Built-in demonstrations for all interactive features
  - **Seamless Integration**: Works with existing plugin system and commands
- **Enhanced User Experience**: Rich messaging capabilities beyond basic text
  - **Visual Feedback**: Buttons and lists provide intuitive interaction
  - **Organized Information**: Structured data presentation with sections and categories
  - **User Engagement**: Interactive elements encourage active participation
  - **Professional Interface**: Business-grade messaging features
- **Available Interactive Commands**:
  - `.buttons` - Interactive button demonstration
  - `.list` - Scrollable menu list showcase
  - `.poll` - Create voting polls with options
  - `.carousel` - Card-style layout presentation
  - `.quick` - Quick reply button examples
  - `.location` - GPS location sharing demo
  - `.contact` - Contact card sharing example