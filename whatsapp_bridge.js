const { makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
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
    }

    async initialize() {
        try {
            console.log('🔌 Initializing WhatsApp connection...');
            
            // Create auth state directory
            const authDir = './wa-auth';
            if (!fs.existsSync(authDir)) {
                fs.mkdirSync(authDir);
            }

            // Load auth state
            const { state, saveCreds } = await useMultiFileAuthState(authDir);

            // Create WhatsApp socket
            this.sock = makeWASocket({
                auth: state,
                logger: P({ level: 'silent' }),
                printQRInTerminal: true,
                defaultQueryTimeoutMs: 60000,
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
        const { connection, lastDisconnect } = update;
        
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('🔌 Connection closed due to:', lastDisconnect?.error, ', reconnecting:', shouldReconnect);
            
            if (shouldReconnect) {
                setTimeout(() => this.initialize(), 5000);
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp Web connected successfully!');
            this.connected = true;
            this.notifyPython('connected');
        }
    }

    async handleMessages(m) {
        try {
            const messages = m.messages || [];
            
            for (const message of messages) {
                if (message.key.fromMe) continue; // Skip messages sent by bot
                
                const messageData = this.parseMessage(message);
                if (messageData) {
                    console.log(`📨 New message from ${messageData.from}: ${messageData.body || messageData.type}`);
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
                const data = fs.readFileSync(messageFile, 'utf8');
                messages = JSON.parse(data || '[]');
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

            const result = await this.sock.sendMessage(to, { text: message });
            console.log(`📤 Message sent to ${to}`);
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
                            await this.sendMessage(msg.to, msg.message, msg.options || {});
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