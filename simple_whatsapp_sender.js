const { makeWASocket, DisconnectReason, useMultiFileAuthState } = require('baileys-mod');
const fs = require('fs');
const path = require('path');

class SimpleWhatsAppSender {
    constructor() {
        this.sock = null;
        this.connected = false;
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    async initialize() {
        try {
            console.log('🔌 Starting simple WhatsApp sender...');
            
            const authDir = './wa-auth';
            const { state, saveCreds } = await useMultiFileAuthState(authDir);
            
            this.sock = makeWASocket({
                auth: state,
                logger: require('pino')({ level: 'silent' }),
                printQRInTerminal: false,
                defaultQueryTimeoutMs: 30000,
                connectTimeoutMs: 20000,
                syncFullHistory: false,
                browser: ['WhatsApp Bot Sender', 'Chrome', '10.0'],
                mobile: false,
            });

            this.sock.ev.on('creds.update', saveCreds);
            
            this.sock.ev.on('connection.update', (update) => {
                const { connection, lastDisconnect } = update;
                
                if (connection === 'close') {
                    const statusCode = lastDisconnect?.error?.output?.statusCode;
                    console.log(`🔌 Connection closed: ${statusCode}`);
                    
                    if (statusCode === 440) {
                        console.log('⚠️ Connection conflict - waiting before retry');
                        this.connected = false;
                        this.retryAfterDelay();
                    } else if (statusCode !== DisconnectReason.loggedOut && this.retryCount < this.maxRetries) {
                        this.retryCount++;
                        console.log(`🔄 Retry attempt ${this.retryCount}/${this.maxRetries}`);
                        this.retryAfterDelay();
                    } else {
                        console.log('🚫 Max retries reached or logged out');
                        this.connected = false;
                    }
                } else if (connection === 'open') {
                    console.log('✅ Simple sender connected!');
                    this.connected = true;
                    this.retryCount = 0;
                    this.processOutgoingMessages();
                }
            });

        } catch (error) {
            console.error('❌ Failed to initialize sender:', error);
        }
    }

    retryAfterDelay() {
        const delay = Math.max(5000 * this.retryCount, 10000); // Progressive delay, minimum 10s
        console.log(`⏳ Waiting ${delay/1000}s before retry...`);
        setTimeout(() => this.initialize(), delay);
    }

    async processOutgoingMessages() {
        const outgoingFile = './outgoing_messages.json';
        
        setInterval(async () => {
            if (!this.connected) return;
            
            try {
                if (fs.existsSync(outgoingFile)) {
                    const data = fs.readFileSync(outgoingFile, 'utf8');
                    const messages = JSON.parse(data || '[]');
                    
                    for (const msg of messages) {
                        if (!msg.sent && this.connected) {
                            console.log(`📤 Sending message to ${msg.to}: ${msg.message.substring(0, 50)}...`);
                            
                            try {
                                await this.sock.sendMessage(msg.to, { text: msg.message });
                                msg.sent = true;
                                console.log(`✅ Message sent to ${msg.to}`);
                            } catch (sendError) {
                                console.error(`❌ Failed to send to ${msg.to}:`, sendError.message);
                                if (sendError.message.includes('conflict')) {
                                    console.log('⚠️ Conflict detected - disconnecting sender');
                                    this.connected = false;
                                    break;
                                }
                            }
                        }
                    }
                    
                    // Update file with sent status
                    const pendingMessages = messages.filter(msg => !msg.sent);
                    fs.writeFileSync(outgoingFile, JSON.stringify(pendingMessages, null, 2));
                }
            } catch (error) {
                console.error('❌ Error processing messages:', error);
            }
        }, 2000); // Check every 2 seconds
    }
}

// Start the simple sender
const sender = new SimpleWhatsAppSender();
sender.initialize();

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('🛑 Shutting down simple sender...');
    process.exit(0);
});