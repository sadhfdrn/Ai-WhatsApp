const { makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = require('baileys-mod');
const { Boom } = require('@hapi/boom');
const P = require('pino');
const fs = require('fs');
const path = require('path');

class WhatsAppBridge {
    constructor() {
        this.sock = null;
        this.connected = false;
        this.pythonProcess = null;
        this.messageQueue = [];
        this.processingQueue = false;
        this.sentMessageIds = new Set(); // Track messages sent by bot to avoid loops
    }

    async initialize() {
        try {
            console.log('🔌 Initializing WhatsApp connection...');
            
            // Create auth state directory
            const authDir = './wa-auth';
            if (!fs.existsSync(authDir)) {
                fs.mkdirSync(authDir);
            }

            // Load credentials from environment variable (JSON format)
            const waCredsEnv = process.env.WHATSAPP_CREDS;
            if (waCredsEnv) {
                console.log('✅ Found WhatsApp credentials in environment');
                try {
                    const credsData = JSON.parse(waCredsEnv);
                    const credsPath = path.join(authDir, 'creds.json');
                    fs.writeFileSync(credsPath, JSON.stringify(credsData, null, 2));
                    console.log('✅ WhatsApp credentials loaded from environment');
                    
                    // Also create session-data.json for baileys-mod compatibility
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

            // Create WhatsApp socket with baileys-mod configuration
            this.sock = makeWASocket({
                version,
                auth: state,
                logger: P({ level: 'silent' }),
                printQRInTerminal: false,  // Disable QR since we're using creds
                defaultQueryTimeoutMs: 90000,
                connectTimeoutMs: 60000,
                generateHighQualityLinkPreview: true,
                getMessage: async (key) => {
                    return { conversation: 'Hello from Bot' };
                },
                syncFullHistory: false,
                markOnlineOnConnect: true,
                browser: ['WhatsApp AI Bot', 'Chrome', '10.0'],
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

            console.log('✅ WhatsApp bridge initialized');

        } catch (error) {
            console.error('❌ Failed to initialize WhatsApp bridge:', error);
            process.exit(1);
        }
    }

    handleConnectionUpdate(update) {
        const { connection, lastDisconnect, qr, isNewLogin } = update;
        
        if (qr) {
            console.log('📱 QR Code generated - but credentials should be provided via WHATSAPP_CREDS');
            console.log('⚠️  If you see this, please provide WhatsApp session credentials in environment variable');
            // Generate QR code only if no credentials are available
            if (!process.env.WHATSAPP_CREDS) {
                const QR = require('qrcode-terminal');
                QR.generate(qr, { small: true });
                console.log('⬆️ Scan the QR code above with your WhatsApp mobile app');
                console.log('💡 Or provide session credentials via WHATSAPP_CREDS environment variable');
            }
        }
        
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            
            console.log('🔌 Connection closed due to:', lastDisconnect?.error, ', reconnecting:', shouldReconnect);
            console.log(`📊 Status code: ${statusCode}, Reason: ${this.getDisconnectReason(statusCode)}`);
            
            if (shouldReconnect) {
                this.connected = false;
                setTimeout(() => this.initialize(), 5000);
            } else {
                console.log('🚫 Logged out - will not reconnect automatically');
                this.connected = false;
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp Web connected successfully!');
            this.connected = true;
            this.notifyPython('connected');
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
                // Skip messages sent by the bot itself to avoid infinite loops
                if (message.key.fromMe && this.sentMessageIds.has(message.key.id)) {
                    console.log('🤖 Skipping bot message to avoid loop');
                    continue;
                }
                
                const messageData = this.parseMessage(message);
                if (messageData) {
                    const senderInfo = message.key.fromMe ? 'you (self-chat)' : messageData.from;
                    console.log(`📨 New message from ${senderInfo}: ${messageData.body || messageData.type}`);
                    await this.sendToPython(messageData);
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
                timestamp: message.messageTimestamp,
                type: 'text',
                body: null,
                media: null
            };

            // Handle different message types
            if (message.message?.conversation) {
                messageData.body = message.message.conversation;
            } else if (message.message?.extendedTextMessage?.text) {
                messageData.body = message.message.extendedTextMessage.text;
            } else if (message.message?.audioMessage) {
                messageData.type = 'voice';
                messageData.media = message.message.audioMessage;
            } else if (message.message?.imageMessage) {
                messageData.type = 'image';
                messageData.media = message.message.imageMessage;
                messageData.body = message.message.imageMessage.caption || '';
            }

            // Filter out empty messages from status/newsletters
            if (messageData.from.includes('@broadcast') || messageData.from.includes('@newsletter')) {
                if (!messageData.body || !messageData.body.trim()) {
                    console.log(`🚫 Skipping empty status/newsletter from ${messageData.from}`);
                    return null;
                }
            }

            // Filter out completely empty text messages
            if (messageData.type === 'text' && (!messageData.body || !messageData.body.trim())) {
                console.log(`🚫 Skipping empty text message from ${messageData.from}`);
                return null;
            }

            return messageData;

        } catch (error) {
            console.error('❌ Error parsing message:', error);
            return null;
        }
    }

    async sendToPython(messageData) {
        try {
            // Send message to Python bot via HTTP or file system
            const messageFile = path.join(__dirname, 'incoming_messages.json');
            
            let messages = [];
            if (fs.existsSync(messageFile)) {
                try {
                    const data = fs.readFileSync(messageFile, 'utf8');
                    messages = JSON.parse(data || '[]');
                } catch (error) {
                    console.error('❌ JSON parse error, reinitializing messages file:', error.message);
                    messages = [];
                    // Backup corrupted file
                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                    fs.writeFileSync(`${messageFile}.corrupt.${timestamp}`, fs.readFileSync(messageFile));
                }
            }
            
            messages.push({
                ...messageData,
                processed: false,
                received_at: new Date().toISOString()
            });
            
            fs.writeFileSync(messageFile, JSON.stringify(messages, null, 2));
            console.log('📤 Message queued for Python processing');

        } catch (error) {
            console.error('❌ Error sending to Python:', error);
        }
    }

    async sendMessage(to, message, options = {}) {
        try {
            if (!this.connected) {
                console.log('⚠️ Not connected to WhatsApp');
                return false;
            }

            // Prepare message object
            const messageObj = { text: message };
            
            // Add AI flag if specified
            if (options.ai === true) {
                messageObj.ai = true;
            }

            const result = await this.sock.sendMessage(to, messageObj);
            
            // Track messages sent by the bot to prevent loops
            if (result && result.key && result.key.id) {
                this.sentMessageIds.add(result.key.id);
                
                // Clean up old message IDs periodically (keep last 100)
                if (this.sentMessageIds.size > 100) {
                    const idsArray = Array.from(this.sentMessageIds);
                    this.sentMessageIds.clear();
                    idsArray.slice(-50).forEach(id => this.sentMessageIds.add(id));
                }
            }
            
            console.log(`📤 Message sent to ${to}${options.ai ? ' (with AI icon)' : ''}`);
            return true;

        } catch (error) {
            console.error('❌ Error sending message:', error);
            return false;
        }
    }

    notifyPython(event, data = {}) {
        try {
            const eventFile = path.join(__dirname, 'whatsapp_events.json');
            const eventData = {
                event,
                data,
                timestamp: new Date().toISOString()
            };
            
            fs.writeFileSync(eventFile, JSON.stringify(eventData, null, 2));
            
        } catch (error) {
            console.error('❌ Error notifying Python:', error);
        }
    }

    // Monitor for outgoing messages from Python
    async monitorOutgoingMessages() {
        const outgoingFile = path.join(__dirname, 'outgoing_messages.json');
        
        setInterval(async () => {
            if (fs.existsSync(outgoingFile)) {
                try {
                    const data = fs.readFileSync(outgoingFile, 'utf8');
                    const messages = JSON.parse(data || '[]');
                    
                    for (const msg of messages) {
                        if (!msg.sent) {
                            const options = msg.options || {};
                            if (msg.ai) {
                                options.ai = true;
                            }
                            await this.sendMessage(msg.to, msg.message, options);
                            msg.sent = true;
                        }
                    }
                    
                    // Clean up sent messages
                    const pendingMessages = messages.filter(msg => !msg.sent);
                    fs.writeFileSync(outgoingFile, JSON.stringify(pendingMessages, null, 2));
                    
                } catch (error) {
                    console.error('❌ Error processing outgoing messages:', error);
                }
            }
        }, 1000); // Check every second
    }
}

// Initialize and start the bridge
const bridge = new WhatsAppBridge();
bridge.initialize();
bridge.monitorOutgoingMessages();

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('🛑 Shutting down WhatsApp bridge...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('🛑 Terminating WhatsApp bridge...');
    process.exit(0);
});