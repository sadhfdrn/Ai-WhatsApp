const { makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = require('baileys');
const { Boom } = require('@hapi/boom');
const P = require('pino');
const fs = require('fs');
const path = require('path');
const http = require('http');
const PluginManager = require('./plugins/pluginManager');
const MessageUtils = require('./utils/messageUtils');

class WhatsAppBot {
    constructor() {
        this.sock = null;
        this.connected = false;
        this.sentMessageIds = new Set();
        this.startTime = Date.now();
        this.healthServer = null;
        this.hasWelcomeBeenSent = false;
        // Load prefix from environment, default to ".", null means no prefix
        this.prefix = process.env.PREFIX === 'null' ? '' : (process.env.PREFIX || '.');
        // Owner number will be extracted from credentials
        this.ownerNumber = null;
        
        // Enhanced features inspired by @neoxr/wb
        this.commandCooldown = new Map(); // Anti-spam cooldown
        this.messageCache = new Map(); // Message caching
        this.botDetection = new Set(); // Bot message detection
        this.sessionActive = false;
        
        // Initialize plugin system
        this.pluginManager = new PluginManager(this);
        this.plugins = new Map(); // For backward compatibility
        this.messageUtils = null; // Will be initialized after socket creation
        
        console.log(`🔧 Command prefix set to: "${this.prefix || 'none'}"`);
        if (this.ownerNumber) {
            console.log(`👤 Owner number set for welcome messages`);
        }
    }

    async initialize() {
        try {
            console.log('🔌 Starting WhatsApp Bot...');
            
            // Start health server for monitoring
            this.startHealthServer();
            
            // Create auth state directory
            const authDir = './wa-auth';
            if (!fs.existsSync(authDir)) {
                fs.mkdirSync(authDir);
            }

            // Load credentials from environment variable
            await this.loadCredentials(authDir);

            // Load auth state
            const { state, saveCreds } = await useMultiFileAuthState(authDir);
            
            // Get latest Baileys version
            let version;
            try {
                const baileyVersion = await fetchLatestBaileysVersion();
                version = baileyVersion.version;
                console.log(`📱 Using Baileys version: ${version.join('.')}`);
            } catch (error) {
                console.log('⚠️ Could not fetch latest version, using default');
            }

            // Create WhatsApp socket
            this.sock = makeWASocket({
                version,
                auth: state,
                logger: P({ level: 'silent' }),
                printQRInTerminal: false,
                defaultQueryTimeoutMs: 90000,
                connectTimeoutMs: 60000,
                generateHighQualityLinkPreview: true,
                getMessage: async (key) => {
                    return { conversation: 'Bot Message' };
                },
                syncFullHistory: false,
                markOnlineOnConnect: true,
                browser: ['WhatsApp Bot', 'Chrome', '10.0'],
                mobile: false,
            });

            // Handle credentials update
            this.sock.ev.on('creds.update', saveCreds);

            // Handle connection updates
            this.sock.ev.on('connection.update', (update) => {
                this.handleConnectionUpdate(update);
            });

            // Handle incoming messages
            this.sock.ev.on('messages.upsert', async (m) => {
                await this.handleMessages(m);
            });

            // Load plugins after socket initialization
            await this.pluginManager.loadPlugins();
            this.plugins = this.pluginManager.plugins; // For backward compatibility
            
            console.log('✅ WhatsApp bot initialized successfully');

        } catch (error) {
            console.error('❌ Failed to initialize WhatsApp bot:', error);
            process.exit(1);
        }
    }

    async loadCredentials(authDir) {
        const waCredsEnv = process.env.WHATSAPP_CREDS;
        if (waCredsEnv) {
            console.log('✅ Found WhatsApp credentials in environment');
            try {
                const credsData = JSON.parse(waCredsEnv);
                const credsPath = path.join(authDir, 'creds.json');
                fs.writeFileSync(credsPath, JSON.stringify(credsData, null, 2));
                console.log('✅ WhatsApp credentials loaded from environment');
                
                // Extract owner number from credentials
                if (credsData.me && credsData.me.id) {
                    this.ownerNumber = credsData.me.id;
                    console.log('👤 Owner number extracted from credentials');
                } else if (credsData.registrationId) {
                    // Alternative: look for phone number in other credential fields
                    const phoneFields = ['phoneNumber', 'jid', 'wid'];
                    for (const field of phoneFields) {
                        if (credsData[field]) {
                            this.ownerNumber = credsData[field];
                            console.log(`👤 Owner number found in ${field} field`);
                            break;
                        }
                    }
                }
                
                // Also create session-data.json for compatibility
                const sessionPath = path.join(authDir, 'session-data.json');
                fs.writeFileSync(sessionPath, JSON.stringify(credsData, null, 2));
                
            } catch (error) {
                console.log('❌ Failed to parse WHATSAPP_CREDS:', error.message);
                console.log('Expected format: JSON object with WhatsApp session data');
            }
        } else {
            console.log('❌ WHATSAPP_CREDS environment variable not found');
            console.log('ℹ️  Please provide WhatsApp session credentials in JSON format');
        }
    }

    async handleConnectionUpdate(update) {
        const { connection, lastDisconnect, qr, isNewLogin } = update;
        
        if (qr) {
            console.log('📱 QR Code generated');
            if (!process.env.WHATSAPP_CREDS) {
                const QR = require('qrcode-terminal');
                QR.generate(qr, { small: true });
                console.log('⬆️ Scan the QR code above with your WhatsApp mobile app');
            }
        }
        
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            
            console.log('🔌 Connection closed:', lastDisconnect?.error, 'reconnecting:', shouldReconnect);
            console.log(`📊 Status code: ${statusCode}, Reason: ${this.getDisconnectReason(statusCode)}`);
            
            if (shouldReconnect) {
                this.connected = false;
                // Add exponential backoff for reconnection
                const delay = Math.min(5000 + Math.random() * 5000, 30000);
                setTimeout(() => this.initialize(), delay);
            } else {
                console.log('🚫 Logged out - will not reconnect automatically');
                this.connected = false;
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp Web connected successfully!');
            this.connected = true;
            
            // Extract owner number from connected socket
            if (this.sock && this.sock.user && this.sock.user.id) {
                this.ownerNumber = this.sock.user.id;
                console.log('👤 Owner number extracted from socket connection');
            }
            
            // Send welcome message after successful connection
            if (!this.hasWelcomeBeenSent) {
                await this.sendWelcomeMessage();
                this.hasWelcomeBeenSent = true;
            }
        } else if (connection === 'connecting') {
            console.log('🔄 Connecting to WhatsApp...');
        }
    }
    
    getDisconnectReason(statusCode) {
        switch (statusCode) {
            case DisconnectReason.badSession:
                return 'Bad Session File';
            case DisconnectReason.connectionClosed:
                return 'Connection Closed';
            case DisconnectReason.connectionLost:
                return 'Connection Lost';
            case DisconnectReason.connectionReplaced:
                return 'Connection Replaced';
            case DisconnectReason.loggedOut:
                return 'Device Logged Out';
            case DisconnectReason.restartRequired:
                return 'Restart Required';
            case DisconnectReason.timedOut:
                return 'Connection Timed Out';
            default:
                return `Unknown (${statusCode})`;
        }
    }

    async handleMessages(m) {
        try {
            const messages = m.messages || [];
            
            for (const message of messages) {
                // Skip messages sent by the bot itself
                if (message.key.fromMe && this.sentMessageIds.has(message.key.id)) {
                    continue;
                }
                
                // Handle decryption errors gracefully
                if (message.messageStubType || !message.message) {
                    console.log('⚠️ Skipping stub/encrypted message');
                    continue;
                }
                
                // Check for interactive message responses first
                const interactiveResponse = this.parseInteractiveResponse(message);
                if (interactiveResponse) {
                    console.log(`🎮 Interactive response: ${interactiveResponse.type} - ${interactiveResponse.id}`);
                    await this.handleInteractiveResponse(message, interactiveResponse);
                    continue;
                }

                const messageData = this.parseMessage(message);
                if (messageData && messageData.body) {
                    console.log(`📨 Message from ${messageData.from}: ${messageData.body}`);
                    await this.processCommand(messageData);
                }
            }
        } catch (error) {
            console.error('❌ Error handling messages:', error);
            // Don't crash the bot, just log and continue
        }
    }

    parseMessage(message) {
        try {
            const messageData = {
                id: message.key.id,
                from: message.key.remoteJid,
                sender: message.key.participant || message.key.remoteJid,
                timestamp: message.messageTimestamp,
                body: null,
                quotedMessage: null
            };

            // Handle different message types
            if (message.message?.conversation) {
                messageData.body = message.message.conversation;
            } else if (message.message?.extendedTextMessage?.text) {
                messageData.body = message.message.extendedTextMessage.text;
                
                // Check for quoted message (reply)
                if (message.message.extendedTextMessage.contextInfo?.quotedMessage) {
                    messageData.quotedMessage = {
                        participant: message.message.extendedTextMessage.contextInfo.participant,
                        id: message.message.extendedTextMessage.contextInfo.stanzaId
                    };
                }
            }

            // Filter out empty messages and broadcasts
            if (messageData.from.includes('@broadcast') || messageData.from.includes('@newsletter')) {
                return null;
            }

            if (!messageData.body || !messageData.body.trim()) {
                return null;
            }

            return messageData;

        } catch (error) {
            console.error('❌ Error parsing message:', error);
            return null;
        }
    }

    async processCommand(messageData) {
        try {
            const message = messageData.body.trim();
            const command = message.toLowerCase();
            
            // Check if message starts with the configured prefix (or process all messages if no prefix)
            if (this.prefix && !command.startsWith(this.prefix)) {
                return; // Not a command for us
            }
            
            // Remove prefix from command for processing (if prefix exists)
            const cleanCommand = this.prefix ? command.slice(this.prefix.length) : command;
            
            // Split command and arguments
            const commandParts = cleanCommand.split(' ');
            const commandName = commandParts[0];
            const args = commandParts.slice(1);
            
            // Enhanced spam protection inspired by @neoxr/wb
            if (this.isSpamDetected(messageData.from, commandName)) {
                console.log(`🚫 Spam detected from ${messageData.from} for command: ${commandName}`);
                return
            }
            
            // Handle special case for tag command with arguments
            if (commandName === 'tag' && args.length > 0) {
                // Use plugin system for tag command
                await this.pluginManager.executeCommand(messageData, 'tag', args);
            } else {
                // Try to execute command through plugin system
                const success = await this.pluginManager.executeCommand(messageData, commandName, args);
                
                if (!success) {
                    // Command not found in plugins
                    console.log(`❓ Unknown command: ${commandName}`);
                }
            }
            
            // Update cooldown after successful command execution
            this.updateCooldown(messageData.from, commandName)
            
        } catch (error) {
            console.error('❌ Error processing command:', error);
        }
    }

    isSpamDetected(sender, command) {
        const now = Date.now()
        const cooldownKey = `${sender}-${command}`
        const lastUsed = this.commandCooldown.get(cooldownKey)
        
        // 3 second cooldown per command per user (inspired by @neoxr/wb)
        if (lastUsed && (now - lastUsed) < 3000) {
            return true
        }
        
        return false
    }

    updateCooldown(sender, command) {
        const cooldownKey = `${sender}-${command}`
        this.commandCooldown.set(cooldownKey, Date.now())
        
        // Clean old cooldowns (older than 1 minute)
        const oneMinuteAgo = Date.now() - 60000
        for (const [key, timestamp] of this.commandCooldown.entries()) {
            if (timestamp < oneMinuteAgo) {
                this.commandCooldown.delete(key)
            }
        }
    }

    isBotMessage(messageId) {
        // Enhanced bot detection inspired by @neoxr/wb
        if (!messageId) return false
        
        return (
            (messageId.startsWith('3EB0') && messageId.length === 40) ||
            messageId.startsWith('BAE') ||
            /[-]/.test(messageId) ||
            this.botDetection.has(messageId)
        )
    }

    parseInteractiveResponse(message) {
        try {
            // Handle button responses
            if (message.message?.buttonsResponseMessage) {
                return {
                    type: 'button',
                    id: message.message.buttonsResponseMessage.selectedButtonId,
                    text: message.message.buttonsResponseMessage.selectedDisplayText
                };
            }

            // Handle list responses
            if (message.message?.listResponseMessage) {
                const response = message.message.listResponseMessage.singleSelectReply;
                return {
                    type: 'list',
                    id: response.selectedRowId,
                    text: response.selectedDisplayText
                };
            }

            // Handle poll responses
            if (message.message?.pollUpdateMessage) {
                return {
                    type: 'poll',
                    pollCreationMessageKey: message.message.pollUpdateMessage.pollCreationMessageKey,
                    vote: message.message.pollUpdateMessage.vote
                };
            }

            return null;
        } catch (error) {
            console.error('❌ Error parsing interactive response:', error);
            return null;
        }
    }

    async handleInteractiveResponse(message, responseData) {
        try {
            // Check if interactive plugin is loaded and can handle this response
            const interactivePlugin = this.pluginManager.plugins.get('interactive');
            if (interactivePlugin && interactivePlugin.handleInteractiveResponse) {
                await interactivePlugin.handleInteractiveResponse(message, responseData);
            } else {
                // Default handling
                const from = message.key.remoteJid;
                await this.sendMessage(from, `You selected: ${responseData.text} (${responseData.type})`);
            }
        } catch (error) {
            console.error('❌ Error handling interactive response:', error);
        }
    }



    async sendMessage(to, message) {
        try {
            if (!this.connected) {
                console.log('⚠️ Not connected to WhatsApp');
                return false;
            }

            const result = await this.sock.sendMessage(to, { text: message });
            
            // Track sent messages to prevent loops
            if (result && result.key && result.key.id) {
                this.sentMessageIds.add(result.key.id);
                
                // Clean up old message IDs (keep last 100)
                if (this.sentMessageIds.size > 100) {
                    const idsArray = Array.from(this.sentMessageIds);
                    this.sentMessageIds.clear();
                    idsArray.slice(-50).forEach(id => this.sentMessageIds.add(id));
                }
            }
            
            console.log(`📤 Message sent to ${to}`);
            return true;

        } catch (error) {
            console.error('❌ Error sending message:', error);
            return false;
        }
    }

    async sendWelcomeMessage() {
        try {
            if (!this.connected) {
                console.log('⚠️ Not connected to WhatsApp - cannot send welcome message');
                return false;
            }

            const welcomeText = `🤖 WhatsApp Bot is now online and ready!

✅ Connected successfully at ${new Date().toLocaleString()}
🚀 All systems operational
📱 Ready to respond to messages

Bot Information:
• Prefix: "${this.prefix || 'none'}"
• Uptime: Online
• Status: Active

Type a message to interact with me!`;

            // Send welcome message to owner (self)
            if (this.ownerNumber) {
                const formattedNumber = this.ownerNumber.includes('@') ? this.ownerNumber : `${this.ownerNumber}@s.whatsapp.net`;
                await this.sendMessage(formattedNumber, welcomeText);
                console.log('🎉 Welcome message sent to owner');
            } else {
                console.log('🎉 Bot connected successfully! (Owner number not yet available for welcome message)');
            }

            return true;
        } catch (error) {
            console.error('❌ Error sending welcome message:', error);
            return false;
        }
    }

    async reactToMessage(messageData, emoji) {
        try {
            if (!this.connected) {
                console.log('⚠️ Not connected to WhatsApp - cannot react');
                return false;
            }

            const reactionMessage = {
                react: {
                    text: emoji,
                    key: {
                        remoteJid: messageData.from,
                        fromMe: false,
                        id: messageData.id
                    }
                }
            };

            await this.sock.sendMessage(messageData.from, reactionMessage);
            console.log(`⚡ Reacted with ${emoji} to message from ${messageData.from}`);
            return true;

        } catch (error) {
            console.error('❌ Error reacting to message:', error);
            return false;
        }
    }

    async removeReaction(messageData) {
        try {
            if (!this.connected) {
                console.log('⚠️ Not connected to WhatsApp - cannot remove reaction');
                return false;
            }

            const removeReactionMessage = {
                react: {
                    text: '',
                    key: {
                        remoteJid: messageData.from,
                        fromMe: false,
                        id: messageData.id
                    }
                }
            };

            await this.sock.sendMessage(messageData.from, removeReactionMessage);
            console.log(`🗑️ Removed reaction from message from ${messageData.from}`);
            return true;

        } catch (error) {
            console.error('❌ Error removing reaction:', error);
            return false;
        }
    }

    startHealthServer() {
        try {
            let port = parseInt(process.env.PORT || '8080');
            
            this.healthServer = http.createServer((req, res) => {
                if (req.url === '/health') {
                    const uptime = Math.floor((Date.now() - this.startTime) / 1000);
                    const healthStatus = {
                        status: 'healthy',
                        connected: this.connected,
                        uptime: uptime,
                        timestamp: new Date().toISOString()
                    };
                    
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(healthStatus, null, 2));
                } else {
                    res.writeHead(404, { 'Content-Type': 'text/plain' });
                    res.end('Not Found');
                }
            });

            this.healthServer.listen(port, '0.0.0.0', () => {
                console.log(`🏥 Health check server running on port ${port}`);
            });

            this.healthServer.on('error', (err) => {
                if (err.code === 'EADDRINUSE') {
                    port += 1;
                    console.log(`⚠️ Port ${port - 1} in use, trying port ${port}`);
                    this.healthServer.listen(port, '0.0.0.0', () => {
                        console.log(`🏥 Health check server running on port ${port}`);
                    });
                } else {
                    console.error('❌ Health server error:', err);
                }
            });

        } catch (error) {
            console.error('❌ Failed to start health server:', error);
        }
    }

    // Graceful shutdown
    async shutdown() {
        console.log('🛑 Shutting down WhatsApp bot...');
        
        if (this.healthServer) {
            this.healthServer.close();
        }
        
        if (this.sock) {
            this.sock.end();
        }
        
        console.log('✅ Bot shutdown complete');
    }
}

// Initialize and start the bot
const bot = new WhatsAppBot();
bot.initialize();

// Handle graceful shutdown
process.on('SIGINT', async () => {
    console.log('⌨️ Keyboard interrupt received');
    await bot.shutdown();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('🛑 Terminating...');
    await bot.shutdown();
    process.exit(0);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('💥 Uncaught Exception:', error);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
});

console.log('🚀 WhatsApp Bot starting...');