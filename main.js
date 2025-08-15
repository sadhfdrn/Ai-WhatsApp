// Clean WhatsApp Bot using pure Baileys
// Use hybrid approach - best of all Baileys variants
const { makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = require('./utils/baileys-hybrid');
const { Boom } = require('@hapi/boom');
const P = require('pino');
const fs = require('fs');
const path = require('path');
const http = require('http');
const PluginManager = require('./plugins/pluginManager');
const MessageUtils = require('./utils/messageUtils');

// Simple spam detection class
class SpamDetection {
    constructor(options = {}) {
        this.RESET_TIMER = options.RESET_TIMER || 3000; // 3 seconds
        this.userCooldowns = new Map();
    }

    detection(client, message, options = {}) {
        const { command, cooldown } = options;
        const userId = message.key.participant || message.key.remoteJid;
        const cooldownKey = `${userId}-${command}`;
        const now = Date.now();

        // Check cooldown
        const lastUsed = cooldown.get(cooldownKey);
        if (lastUsed && (now - lastUsed) < this.RESET_TIMER) {
            console.log(`🚫 Spam detected: ${userId} command: ${command}`);
            return true;
        }

        return false;
    }
}

class WhatsAppBot {
    constructor() {
        this.client = null; // baileys-x client
        this.sock = null; // Direct Baileys socket access
        this.connected = false;
        this.sentMessageIds = new Set();
        this.startTime = Date.now();
        this.healthServer = null;
        this.hasWelcomeBeenSent = false;
        
        // Load prefix from environment, default to ".", null means no prefix
        this.prefix = process.env.PREFIX === 'null' ? '' : (process.env.PREFIX || '.');
        // Owner number will be extracted from credentials
        this.ownerNumber = null;
        
        // Enhanced features with baileys-x
        this.commandCooldown = new Map(); // Anti-spam cooldown
        this.messageCache = new Map(); // Message caching
        this.botDetection = new Set(); // Bot message detection
        this.sessionActive = false;
        
        // Initialize spam detection
        this.spam = new SpamDetection({
            RESET_TIMER: 3000 // 3 seconds cooldown
        });
        
        // Initialize plugin system
        this.pluginManager = new PluginManager(this);
        this.plugins = new Map(); // For backward compatibility
        this.messageUtils = null; // Will be initialized after socket creation
        
        console.log(`🔧 Command prefix set to: "${this.prefix || 'none'}"`);
        console.log(`🔌 Starting WhatsApp Bot...`);
    }

    async initialize() {
        try {
            console.log('🔌 Starting WhatsApp Bot...');
            
            // Start health server for monitoring
            this.startHealthServer();
            
            // Load credentials from environment variable
            if (!await this.loadCredentials()) {
                console.error('❌ WHATSAPP_CREDS environment variable not found');
                console.log('ℹ️  Please provide WhatsApp session credentials in JSON format');
                return;
            }

            console.log('🚀 WhatsApp Bot starting...');

            // Create auth state directory
            const authDir = './wa-auth';
            if (!fs.existsSync(authDir)) {
                fs.mkdirSync(authDir);
            }

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
                version = [2, 3000, 1023223821];
            }

            // Close existing socket if it exists
            if (this.sock) {
                try {
                    console.log('🔌 Closing existing socket...');
                    this.sock.end();
                    this.sock = null;
                } catch (error) {
                    console.error('❌ Error closing socket:', error);
                }
            }

            // Create WhatsApp socket with KaizenMFH optimized settings
            this.sock = makeWASocket({
                version,
                auth: state,
                logger: P({ level: 'silent' }),
                printQRInTerminal: false,
                defaultQueryTimeoutMs: 60000,
                connectTimeoutMs: 60000,
                generateHighQualityLinkPreview: false, // Set to false as per KaizenMFH defaults
                getMessage: async (key) => {
                    // Try to get message from cache first
                    if (this.messageCache && this.messageCache.has(key.id)) {
                        return this.messageCache.get(key.id);
                    }
                    
                    // Return empty message for missing messages
                    return {
                        conversation: "Message not available"
                    };
                },
                syncFullHistory: false,
                markOnlineOnConnect: true,
                browser: ['KaizenBot', 'Chrome', '118.0.0.0'], // Updated browser info
                mobile: false,
                shouldIgnoreJid: jid => {
                    // Only ignore newsletters and status broadcasts, not regular chats
                    if (!jid) return false;
                    return /(@newsletter|status@broadcast)/.test(jid);
                },
                // Connection optimization for KaizenMFH
                keepAliveIntervalMs: 30000,
                retryRequestDelayMs: 250,
                maxMsgRetryCount: 3,
                fireInitQueries: true,
                emitOwnEvents: true // Enable to receive owner messages
            });

            // Handle credentials update
            this.sock.ev.on('creds.update', saveCreds);

            // Setup event handlers
            this.setupEventHandlers();

            // Load plugins after client initialization
            await this.pluginManager.loadPlugins();
            this.plugins = this.pluginManager.plugins; // For backward compatibility
            
            console.log('✅ WhatsApp bot initialized successfully');

        } catch (error) {
            console.error('❌ Failed to initialize WhatsApp bot:', error);
            process.exit(1);
        }
    }

    async loadCredentials() {
        try {
            const waCredsEnv = process.env.WHATSAPP_CREDS;
            if (waCredsEnv) {
                console.log('✅ Found WhatsApp credentials in environment');
                
                // Create auth state directory
                const authDir = './wa-auth';
                if (!fs.existsSync(authDir)) {
                    fs.mkdirSync(authDir, { recursive: true });
                }
                
                const credsData = JSON.parse(waCredsEnv);
                const credsPath = path.join(authDir, 'creds.json');
                fs.writeFileSync(credsPath, JSON.stringify(credsData, null, 2));
                console.log('✅ WhatsApp credentials loaded from environment');
                
                // Extract owner number from credentials
                if (credsData.me && credsData.me.id) {
                    this.ownerNumber = credsData.me.id.split(':')[0];
                    console.log('👤 Owner number extracted from credentials');
                }
                
                return true;
            } else {
                console.log('❌ WHATSAPP_CREDS environment variable not found');
                return false;
            }
        } catch (error) {
            console.error('❌ Error loading credentials:', error);
            return false;
        }
    }

    setupEventHandlers() {
        // Handle connection updates  
        this.sock.ev.on('connection.update', (update) => {
            this.handleConnectionUpdate(update);
        });

        // Handle incoming messages
        this.sock.ev.on('messages.upsert', async (m) => {
            console.log('🔔 Raw message event received:', m?.messages?.length || 0, 'messages');
            if (m?.messages?.length > 0) {
                console.log('🔔 First message details:', {
                    fromMe: m.messages[0].key.fromMe,
                    remoteJid: m.messages[0].key.remoteJid,
                    hasMessage: !!m.messages[0].message,
                    messageKeys: m.messages[0].message ? Object.keys(m.messages[0].message) : []
                });
            }
            
            await this.handleMessages(m);
            
            // Forward to anti-delete plugin if loaded
            const antiDeletePlugin = this.pluginManager?.plugins?.get('antidelete');
            if (antiDeletePlugin && m.messages) {
                m.messages.forEach(message => {
                    antiDeletePlugin.onMessageReceived(message);
                });
            }
        });

        // Handle message updates (including deletions)
        this.sock.ev.on('messages.update', (updates) => {
            console.log('📝 Message updates received:', updates.length);
            
            // Forward to anti-delete plugin if loaded
            const antiDeletePlugin = this.pluginManager?.plugins?.get('antidelete');
            if (antiDeletePlugin) {
                antiDeletePlugin.onMessageUpdate(updates);
            }
        });
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
            
            // Handle stream conflict specifically
            if (statusCode === 440 || lastDisconnect?.error?.message?.includes('conflict')) {
                console.log('⚠️ Stream conflict detected, clearing session and reconnecting...');
                this.connected = false;
                
                // Clear auth state to prevent conflicts
                try {
                    const authDir = './wa-auth';
                    if (fs.existsSync(authDir)) {
                        console.log('🧹 Clearing authentication state...');
                        fs.rmSync(authDir, { recursive: true, force: true });
                    }
                } catch (error) {
                    console.error('❌ Error clearing auth state:', error);
                }
                
                // Wait longer for stream conflicts
                setTimeout(() => this.initialize(), 10000);
            } else if (shouldReconnect) {
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
            
            // Initialize message utils with socket
            this.messageUtils = new MessageUtils(this.sock);
            
            // Extract owner number from connected socket
            if (this.sock.user && this.sock.user.id && !this.ownerNumber) {
                this.ownerNumber = this.sock.user.id.split(':')[0];
                console.log('👤 Owner number extracted from socket connection');
            }
            
            // Send welcome message after successful connection
            await this.sendWelcomeMessage();
        } else if (connection === 'connecting') {
            console.log('🔄 Connecting to WhatsApp...');
        }
    }

    async handleMessages(m) {
        try {
            const messages = m.messages || [];
            console.log(`📝 Message updates received: ${messages.length}`);
            
            for (const message of messages) {
                // Debug: Log incoming message details
                console.log(`🔍 Processing message from: ${message.key.remoteJid || 'unknown'}`);
                console.log(`🔍 Message ID: ${message.key.id}`);
                console.log(`🔍 From me: ${message.key.fromMe}`);
                console.log(`🔍 Has message content: ${!!message.message}`);
                
                // Skip messages sent by the bot itself (but only our own sent messages)
                if (message.key.fromMe) {
                    console.log(`🔍 Message from me detected - checking if it's our sent message`);
                    if (this.sentMessageIds.has(message.key.id)) {
                        console.log(`⏭️ Skipping own sent message: ${message.key.id}`);
                        continue;
                    } else {
                        console.log(`✅ Message from me but not in sentMessageIds - processing (owner command)`);
                    }
                }
                
                // Handle decryption errors gracefully
                if (message.messageStubType || !message.message) {
                    console.log(`⏭️ Skipping stub/empty message: ${message.messageStubType || 'no content'}`);
                    continue;
                }

                // Bot detection - but be more specific
                if (this.isBotMessage(message.key.id)) {
                    console.log(`🤖 Detected bot message: ${message.key.id}`);
                    continue;
                }

                // Check for view-once messages first (for auto VV)
                if (this.pluginManager) {
                    const viewOncePlugin = this.pluginManager.getPlugin('vv');
                    if (viewOncePlugin && viewOncePlugin.autoVVEnabled) {
                        await viewOncePlugin.handleAutoVV(message);
                    }
                }

                // Cache the message for later retrieval
                if (message.message && message.key.id) {
                    this.messageCache.set(message.key.id, message.message);
                    // Clean old cache entries (keep only last 1000 messages)
                    if (this.messageCache.size > 1000) {
                        const firstKey = this.messageCache.keys().next().value;
                        this.messageCache.delete(firstKey);
                    }
                }

                // Check for interactive responses first
                const interactiveResponse = this.messageUtils ? this.messageUtils.parseInteractiveResponse(message) : null;
                if (interactiveResponse) {
                    console.log('🎮 Interactive response detected:', interactiveResponse.type, interactiveResponse.id);
                    await this.handleInteractiveResponse(message, interactiveResponse);
                    continue; // Skip further processing for interactive responses
                }

                // Extract message data
                const messageData = this.parseMessage(message);
                console.log(`🔍 Parsed message data:`, messageData ? {
                    from: messageData.from,
                    body: messageData.body,
                    hasBody: !!messageData.body
                } : 'null');
                
                if (messageData && messageData.body) {
                    console.log(`📨 Message from ${messageData.from}: ${messageData.body}`);

                    // Check if it's a command
                    const isCmd = this.isCommand(messageData.body);
                    console.log(`🔍 Is command check: ${isCmd} (prefix: "${this.prefix}")`);
                    
                    if (isCmd) {
                        const command = this.extractCommand(messageData.body);
                        console.log(`🎯 Extracted command: "${command}"`);
                        
                        // Apply spam detection
                        const isSpam = this.spam.detection(this.sock, message, {
                            command,
                            cooldown: this.commandCooldown
                        });

                        if (!isSpam) {
                            console.log(`✅ Processing command: ${command}`);
                            // Add original message to messageData for plugin access
                            messageData.originalMessage = message;
                            await this.processCommand(messageData);
                        } else {
                            console.log(`🚫 Spam detected from ${messageData.from}`);
                        }
                    } else {
                        console.log(`ℹ️ Not a command: "${messageData.body}"`);
                    }
                }
            }
        } catch (error) {
            console.error('❌ Error handling messages:', error);
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
                    const contextInfo = message.message.extendedTextMessage.contextInfo;
                    messageData.quotedMessage = {
                        participant: contextInfo.participant,
                        id: contextInfo.stanzaId,
                        content: contextInfo.quotedMessage,
                        // Add the full message for proper processing
                        message: {
                            message: contextInfo.quotedMessage,
                            key: {
                                id: contextInfo.stanzaId,
                                remoteJid: message.key.remoteJid,
                                participant: contextInfo.participant
                            }
                        }
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

    // Simple bot detection
    isBotMessage(messageId) {
        if (!messageId) return false;
        
        return (
            (messageId.startsWith('3EB0') && messageId.length === 40) ||
            messageId.startsWith('BAE') ||
            this.botDetection.has(messageId)
        );
    }

    extractMessageData(m) {
        try {
            const messageType = Object.keys(m.message)[0];
            let text = '';

            switch (messageType) {
                case 'conversation':
                    text = m.message.conversation;
                    break;
                case 'extendedTextMessage':
                    text = m.message.extendedTextMessage.text;
                    break;
                case 'imageMessage':
                case 'videoMessage':
                case 'audioMessage':
                case 'documentMessage':
                    text = m.message[messageType].caption || '';
                    break;
                default:
                    return null;
            }

            return {
                id: m.key.id,
                from: m.key.remoteJid,
                sender: m.key.participant || m.key.remoteJid,
                text: text.trim(),
                isGroup: m.key.remoteJid.endsWith('@g.us'),
                timestamp: m.messageTimestamp,
                quoted: m.message.extendedTextMessage?.contextInfo?.quotedMessage || null,
                quotedSender: m.message.extendedTextMessage?.contextInfo?.participant || null,
                messageType,
                originalMessage: m
            };
        } catch (error) {
            console.error('❌ Error extracting message data:', error);
            return null;
        }
    }

    isCommand(text) {
        if (!text) return false;
        
        if (this.prefix === 'null' || this.prefix === null || this.prefix === '') {
            // No prefix mode - check if message starts with known command
            const commands = this.pluginManager ? this.pluginManager.getCommandList() : [];
            return commands.some(cmd => text.toLowerCase().startsWith(cmd.toLowerCase()));
        }
        
        return text.startsWith(this.prefix);
    }

    extractCommand(text) {
        if (this.prefix === 'null' || this.prefix === null || this.prefix === '') {
            // No prefix mode
            return text.split(' ')[0].toLowerCase();
        } else {
            // With prefix
            return text.slice(this.prefix.length).split(' ')[0].toLowerCase();
        }
    }

    async processCommand(messageData) {
        try {
            const message = messageData.body.trim();
            const lowerMessage = message.toLowerCase();
            
            // Check if message starts with the configured prefix (or process all messages if no prefix)
            if (this.prefix && !lowerMessage.startsWith(this.prefix)) {
                return; // Not a command for us
            }
            
            // Remove prefix from command for processing (if prefix exists) - preserve original case for arguments
            const cleanCommand = this.prefix ? message.slice(this.prefix.length) : message;
            
            // Split command and arguments - only convert command name to lowercase, preserve arguments case
            const commandParts = cleanCommand.split(' ');
            const commandName = commandParts[0].toLowerCase(); // Only convert command to lowercase
            const args = commandParts.slice(1); // Keep original case for arguments
            
            // Add reaction to show command received
            await this.reactToMessage(messageData, '📋');
            
            // Execute command through plugin manager
            if (this.pluginManager) {
                const success = await this.pluginManager.executeCommand(messageData, commandName, args);
                
                if (success) {
                    // Success reaction
                    await this.reactToMessage(messageData, '✅');
                    setTimeout(() => this.removeReaction(messageData), 3000);
                } else {
                    // Command not found
                    await this.reactToMessage(messageData, '❓');
                    setTimeout(() => this.removeReaction(messageData), 3000);
                }
            }
            
            // Update cooldown after successful command execution
            this.updateCooldown(messageData.from, commandName);
            
        } catch (error) {
            console.error('❌ Error processing command:', error);
            await this.reactToMessage(messageData, '❌');
        }
    }

    updateCooldown(sender, command) {
        const cooldownKey = `${sender}-${command}`;
        this.commandCooldown.set(cooldownKey, Date.now());
        
        // Clean old cooldowns (older than 1 minute)
        const oneMinuteAgo = Date.now() - 60000;
        for (const [key, timestamp] of this.commandCooldown.entries()) {
            if (timestamp < oneMinuteAgo) {
                this.commandCooldown.delete(key);
            }
        }
    }

    // Handle interactive responses (buttons, lists, etc.)
    async handleInteractiveResponse(message, responseData) {
        try {
            const from = message.key.remoteJid;
            console.log('🎮 Handling interactive response:', responseData);

            // Forward to interactive plugin first
            const interactivePlugin = this.pluginManager?.plugins?.get('interactive');
            if (interactivePlugin) {
                await interactivePlugin.handleInteractiveResponse(message, responseData);
                return;
            }

            // Generic response handling if no specific plugin handles it
            switch (responseData.type) {
                case 'button':
                    await this.sendMessage(from, `You clicked: ${responseData.text} (ID: ${responseData.id})`);
                    break;
                case 'list':
                    await this.sendMessage(from, `You selected: ${responseData.text} (ID: ${responseData.id})`);
                    break;
                case 'native_flow':
                    await this.sendMessage(from, `Interactive response received: ${responseData.id}`);
                    break;
                default:
                    console.log('🔍 Unhandled interactive response type:', responseData.type);
            }
        } catch (error) {
            console.error('❌ Error handling interactive response:', error);
        }
    }

    async sendMessage(to, message) {
        try {
            if (!this.connected || !this.sock) {
                console.log('⚠️ Not connected to WhatsApp - cannot send message');
                return false;
            }

            // Ensure we have a valid JID format
            let targetJid = to;
            if (to && typeof to === 'string') {
                if (!to.includes('@')) {
                    targetJid = to.includes('-') ? `${to}@g.us` : `${to}@s.whatsapp.net`;
                }
            } else {
                console.error('❌ Invalid JID provided:', to);
                return false;
            }

            // Handle different message types
            let messageContent;
            if (typeof message === 'string') {
                // Simple text message
                messageContent = { text: message };
            } else if (typeof message === 'object' && message !== null) {
                // Media message or complex message object
                messageContent = message;
            } else {
                console.error('❌ Invalid message format:', typeof message);
                return false;
            }

            await this.sock.sendMessage(targetJid, messageContent);
            console.log(`📤 Message sent to ${targetJid}`);
            return true;

        } catch (error) {
            console.error('❌ Error sending message:', error);
            
            return false;
        }
    }

    async reactToMessage(messageData, emoji) {
        try {
            if (!this.connected || !this.sock) {
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
            if (!this.connected || !this.sock) {
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

    async getGroupMetadata(groupJid) {
        try {
            if (!this.connected || !this.sock) {
                console.log('⚠️ Not connected to WhatsApp - cannot get group metadata');
                return null;
            }

            const metadata = await this.sock.groupMetadata(groupJid);
            return metadata;

        } catch (error) {
            console.error('❌ Error getting group metadata:', error);
            return null;
        }
    }

    async sendWelcomeMessage() {
        try {
            if (this.hasWelcomeBeenSent || !this.ownerNumber || !this.connected) {
                return false;
            }

            const welcomeText = `🎉 WhatsApp Bot Connected Successfully!

⏰ Connection Time: ${new Date().toLocaleString()}
📱 Bot Status: Online and Ready  
🔧 Command Prefix: ${this.prefix === 'null' || this.prefix === '' ? 'No prefix required' : this.prefix}
🔌 Plugins: ${this.pluginManager ? this.pluginManager.loadedCount : 0} loaded
📚 Library: Pure Baileys
🛡️ Features: Spam detection, interactive messages

📋 Available Commands:
${this.prefix === 'null' || this.prefix === '' ? '' : this.prefix}menu - Show all commands
${this.prefix === 'null' || this.prefix === '' ? '' : this.prefix}ping - Check bot status
${this.prefix === 'null' || this.prefix === '' ? '' : this.prefix}help - Get help information
${this.prefix === 'null' || this.prefix === '' ? '' : this.prefix}buttons - Interactive buttons demo
${this.prefix === 'null' || this.prefix === '' ? '' : this.prefix}list - Interactive list demo

🚀 Bot is ready to receive commands!`;

            const ownerJid = this.ownerNumber + '@s.whatsapp.net';
            const success = await this.sendMessage(ownerJid, welcomeText);
            
            if (success) {
                this.hasWelcomeBeenSent = true;
                console.log('🎉 Welcome message sent to owner');
            }

            return success;

        } catch (error) {
            console.error('❌ Error sending welcome message:', error);
            return false;
        }
    }

    startHealthServer() {
        try {
            let port = process.env.PORT || 8080;
            
            const server = http.createServer((req, res) => {
                if (req.url === '/health' || req.url === '/') {
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        status: 'healthy',
                        connected: this.connected,
                        timestamp: new Date().toISOString(),
                        plugins: this.pluginManager ? this.pluginManager.loadedCount : 0,
                        library: '@neoxr/wb with Baileys',
                        uptime: Date.now() - this.startTime
                    }));
                } else {
                    res.writeHead(404, { 'Content-Type': 'text/plain' });
                    res.end('Not Found');
                }
            });

            server.on('error', (err) => {
                if (err.code === 'EADDRINUSE') {
                    port = port + 1;
                    console.log(`⚠️ Port ${port - 1} in use, trying port ${port}`);
                    server.listen(port);
                } else {
                    console.error('❌ Health server error:', err);
                }
            });

            server.listen(port, '0.0.0.0', () => {
                console.log(`🏥 Health check server running on port ${port}`);
            });

        } catch (error) {
            console.error('❌ Error starting health server:', error);
        }
    }
}

// Start the bot
const bot = new WhatsAppBot();
bot.initialize();

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down WhatsApp Bot...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down WhatsApp Bot...');
    process.exit(0);
});