# WhatsApp Bot with TikTok Downloader 🤖

A pure Node.js WhatsApp bot with comprehensive plugin support, featuring TikTok video/image downloading, view-once message processing, anti-delete functionality, interactive messaging, and WhatsApp status posting capabilities.

## 🚀 Key Features

### 🎵 TikTok Integration
- **Video Downloads**: Download TikTok videos with metadata (title, author, stats)
- **Image Carousels**: Download TikTok slideshow posts as WhatsApp albums
- **Smart Detection**: Automatically detects video vs image content
- **Quality Options**: HD, SD, and watermarked video variants
- **File Management**: Automatic cleanup and size optimization

### 👻 View-Once Processing
- **Message Recovery**: Remove view-once restrictions from images/videos
- **Silent Processing**: Stealth mode with owner-only notifications
- **Auto Processing**: Toggle automatic view-once handling
- **Content Saving**: Save view-once content to owner DM

### 🛡️ Anti-Delete Protection
- **Message Backup**: Forward deleted messages to owner
- **Group/Private Control**: Separate toggles for different chat types
- **Message Caching**: Store recent messages for reliable recovery
- **Silent Operation**: No visible reactions or confirmations

### 📋 WhatsApp Status Features
- **Status Posting**: Post text, images, videos, and voice to WhatsApp Status
- **Video Trimming**: Auto-split videos longer than 1 minute
- **Owner Security**: Status posting restricted to bot owner
- **Contact Integration**: Automatic contact list detection

### 🎮 Interactive Messaging
- **Button Messages**: Create interactive button interfaces
- **List Messages**: Send organized list selections
- **Poll Creation**: Create WhatsApp polls with multiple options
- **Quick Replies**: Fast response templates
- **Location Sharing**: Send location coordinates
- **Contact Cards**: Share contact information

### 👥 Group Management
- **Smart Tagging**: Silent and loud member tagging options
- **Group Status**: Detailed member information and statistics
- **Admin Tools**: Group management utilities
- **Member Analysis**: Activity tracking and insights

## 🛠️ Technical Architecture

### Core Technologies
- **Backend**: Pure Node.js with async/await
- **WhatsApp Integration**: Baileys (WhiskeySockets/Baileys) for WhatsApp Web connectivity
- **Media Processing**: FFmpeg for video processing and trimming
- **TikTok API**: @tobyg74/tiktok-api-dl for reliable video/image downloads
- **Plugin System**: Modular architecture with auto-loading plugins

### Performance Features
- **Message Caching**: Temporary storage for deleted message recovery
- **Auto Cleanup**: Automatic file deletion after media sending
- **Spam Protection**: Cooldown system for command usage
- **Connection Management**: Auto-reconnection and session persistence
- **Health Monitoring**: HTTP server for deployment health checks

## 🚀 Quick Deployment

### Option 1: GitHub Actions (Recommended)
The bot automatically deploys on GitHub Actions with optimized resource usage:

1. **Fork this repository**
2. **Set up secrets** (optional for enhanced features):
   ```
   OPENAI_API_KEY=your_openai_key_here
   WHATSAPP_CREDS=your_whatsapp_credentials_json
   ```
3. **Enable GitHub Actions** in your repository settings
4. **Trigger deployment**:
   - Push to main branch, or
   - Go to Actions → "WhatsApp AI Bot - Enhanced Deployment" → "Run workflow"

### Option 2: Replit Deployment
Deploy directly on Replit for development and testing:

1. **Import repository** to Replit
2. **Install dependencies**:
   ```bash
   npm install
   ```
3. **Set environment variables** in Replit secrets:
   - `WHATSAPP_CREDS`: Your WhatsApp credentials JSON
   - `PREFIX`: Command prefix (default: ".")
   - `OWNER_NUMBER`: Your WhatsApp number for owner features
4. **Run the bot**:
   ```bash
   node main.js
   ```

## 📱 WhatsApp Setup

### First-Time Connection
1. **Start the bot** using either deployment method
2. **Scan QR code** displayed in the console with WhatsApp Web
3. **Send a test message** to confirm connection
4. **Enable features** using bot commands

### QR Code Authentication
The bot generates a QR code for WhatsApp Web authentication. Simply:
1. Open WhatsApp on your phone
2. Go to Settings → Linked Devices → Link a Device
3. Scan the QR code displayed in the bot console
4. Connection established automatically

## 🎯 Bot Commands

### Essential Commands
```
.menu                   # Show all available commands
.help                   # Get help information
.ping                   # Check bot status and uptime
```

### TikTok Features
```
.tiktok <url>          # Download TikTok video or image carousel
.tt <url>              # Short alias for TikTok download
```

### View-Once Processing
```
.vv                    # Remove view-once restriction (reply to message)
.vv2                   # Remove view-once, send to current chat
.autovv                # Toggle automatic view-once processing
.save                  # Save message content to owner DM (reply to message)
```

### WhatsApp Status
```
.post <text>           # Post text to WhatsApp Status
.post                  # Post quoted message to Status (reply to message)
```

### Anti-Delete Protection
```
.antidelete            # Toggle anti-delete for current chat type
```

### Group Management
```
.tag                   # Silently tag all group members
.tagall                # Loudly tag all group members with notification
.gstatus               # Show detailed group member information
```

### Interactive Messages
```
.buttons               # Demo interactive button message
.list                  # Demo interactive list message
.poll                  # Demo poll creation
.carousel              # Demo carousel message
.quick                 # Demo quick reply message
.location              # Demo location sharing
.contact               # Demo contact card sharing
```

## ⚙️ Configuration

### Environment Variables
```bash
# Core Configuration
PREFIX="."                              # Command prefix (default: .)
PORT=8080                              # Health check server port
OWNER_NUMBER=your_whatsapp_number      # Owner number for admin features

# WhatsApp Authentication
WHATSAPP_CREDS=your_credentials_json   # WhatsApp session credentials

# Optional Settings
AUTO_SAVE_CREDS=true                   # Automatically save session
MAX_RECONNECT_ATTEMPTS=5               # Connection retry limit
RECONNECT_DELAY=5000                   # Delay between reconnection attempts
```

### Plugin Configuration
The bot includes 9 core plugins with 23 commands:
- **antidelete**: Deleted message forwarding
- **tiktok**: Video/image downloading  
- **viewonce**: View-once message processing
- **post**: WhatsApp status posting
- **interactive**: Button/list/poll messages
- **grouputils**: Group management tools
- **menu**: Help and command listing
- **ping**: Status and uptime checking
- **debug**: Development and troubleshooting

### TikTok Image Carousel Feature
The enhanced TikTok plugin now supports both video and image content:

1. **Automatic Detection**: Analyzes TikTok API response to determine content type
2. **Video Downloads**: Downloads single video files with metadata
3. **Image Carousels**: Downloads multiple images from slideshow posts
4. **WhatsApp Albums**: Sends images sequentially with captions to create album effect
5. **File Management**: Automatic cleanup after successful sending

### Example Usage
```bash
# Download TikTok video
.tt https://vt.tiktok.com/ZSSvq22PY/

# Download TikTok image carousel (slideshow)
.tt https://vt.tiktok.com/ZSHsGtx6pomNQ-piNWy/
```

## 🔧 Advanced Features

### Message Caching System
- **Deleted Messages**: Stores 2000 recent messages for anti-delete recovery
- **Quoted Messages**: Stores 1000 messages for view-once processing
- **Auto Cleanup**: Removes old cache entries automatically

### Smart Reactions
- **Initial Emoji**: Shows command-specific emoji when processing
- **Success/Failure**: ✅ for success, ❌ for errors
- **Auto Remove**: Reactions disappear after 2 seconds

### Anti-Spam Protection
- **User Cooldowns**: 3-second cooldown per command per user
- **Bot Detection**: Filters messages from other bots
- **Rate Limiting**: Prevents command spam and abuse

## 🛡️ Privacy & Security

### Data Protection
- **Local Processing**: All media processing done locally
- **Session Security**: WhatsApp credentials stored securely in environment
- **Conversation Encryption**: WhatsApp end-to-end encryption maintained
- **Temporary Storage**: Files automatically deleted after processing

### Owner-Only Features
- **Status Posting**: Restricted to bot owner only
- **Anti-Delete**: Deleted messages forwarded to owner DM
- **View-Once Recovery**: Content sent to owner DM for privacy

## 🚨 Troubleshooting

### Common Issues

#### WhatsApp Connection
```bash
# Issue: QR code not appearing
# Solution: Check console output and restart
node main.js

# Issue: Connection lost frequently  
# Solution: Check network stability and credentials
```

#### TikTok Downloads
```bash
# Issue: Download failing
# Solution: Verify URL format and network connection

# Issue: Large files not sending
# Solution: WhatsApp has 64MB limit for videos
```

#### Media Processing
```bash
# Issue: Video trimming not working
# Solution: Ensure FFmpeg is installed
sudo apt-get install ffmpeg

# Issue: Images not sending as album
# Solution: Check file sizes and formats
```

### Debug Information
Check console logs for detailed error information:
- Connection status and QR code display
- Plugin loading and command processing
- File download progress and errors
- Media processing and sending status

## 🤝 Contributing

### Development Setup
1. **Clone repository**:
   ```bash
   git clone https://github.com/yourusername/whatsapp-tiktok-bot.git
   cd whatsapp-tiktok-bot
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your WhatsApp credentials
   ```

4. **Run the bot**:
   ```bash
   node main.js
   ```

### Adding New Plugins
The bot uses a modular plugin system. Create new plugins in the `plugins/` directory following the existing pattern:

```javascript
class MyPlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'myplugin';
        this.description = 'My custom plugin';
        this.commands = ['mycommand'];
        this.emoji = '🔧';
    }

    async execute(messageData, command, args) {
        // Plugin logic here
    }

    isValidCommand(command) {
        return this.commands.includes(command);
    }
}

module.exports = MyPlugin;
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Baileys**: WhiskeySockets/Baileys for WhatsApp Web integration
- **@tobyg74/tiktok-api-dl**: Pure Node.js TikTok API for reliable downloads
- **FFmpeg**: Video processing and trimming capabilities
- **Contributors**: All developers who contributed to this project

---

**Ready to deploy your WhatsApp bot with TikTok support?** 
Set up your credentials and start downloading TikTok videos and image carousels directly to WhatsApp!

*Note: This bot is for educational and personal use. Please respect WhatsApp's Terms of Service and TikTok's usage policies when deploying.*