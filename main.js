const { makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = require('baileys');
const { Boom } = require('@hapi/boom');
const P = require('pino');
const fs = require('fs');
const path = require('path');
const http = require('http');

class WhatsAppBot {
    constructor() {
        this.sock = null;
        this.connected = false;
        this.sentMessageIds = new Set();
        this.startTime = Date.now();
        this.healthServer = null;
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

    handleConnectionUpdate(update) {
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
                timestamp: message.messageTimestamp,
                body: null
            };

            // Handle different message types
            if (message.message?.conversation) {
                messageData.body = message.message.conversation;
            } else if (message.message?.extendedTextMessage?.text) {
                messageData.body = message.message.extendedTextMessage.text;
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
            
            if (command === '.ping') {
                // Add initial processing reaction
                await this.reactToMessage(messageData, '⚡');
                
                try {
                    // Measure network speed by timing a simple request
                    const networkSpeed = await this.measureNetworkSpeed();
                    const uptime = Math.floor((Date.now() - this.startTime) / 1000);
                    
                    const response = `🏓 Pong!\n⏱️ Uptime: ${this.formatUptime(uptime)}\n🌐 Network: ${networkSpeed}ms\n✅ Status: Online`;
                    await this.sendMessage(messageData.from, response);
                    
                    // Show success reaction briefly then remove
                    await this.reactToMessage(messageData, '✅');
                    setTimeout(() => this.removeReaction(messageData), 2000);
                } catch (error) {
                    console.error('❌ Error in ping command:', error);
                    await this.reactToMessage(messageData, '❌');
                    setTimeout(() => this.removeReaction(messageData), 2000);
                }
            }
            else if (command.startsWith('.tag ')) {
                // Extract the message after .tag
                const tagMessage = message.substring(5).trim();
                
                if (tagMessage) {
                    // Add initial processing reaction
                    await this.reactToMessage(messageData, '👥');
                    
                    try {
                        // Tag everyone in the group
                        const success = await this.tagAllMembers(messageData.from, tagMessage);
                        
                        if (success) {
                            await this.reactToMessage(messageData, '✅');
                        } else {
                            await this.reactToMessage(messageData, '❌');
                        }
                        setTimeout(() => this.removeReaction(messageData), 2000);
                    } catch (error) {
                        console.error('❌ Error in tag command:', error);
                        await this.reactToMessage(messageData, '❌');
                        setTimeout(() => this.removeReaction(messageData), 2000);
                    }
                } else {
                    await this.reactToMessage(messageData, '❌');
                    await this.sendMessage(messageData.from, '❌ Please provide a message after .tag\nExample: .tag Hello everyone!');
                    setTimeout(() => this.removeReaction(messageData), 2000);
                }
            }
            else if (command === '.tagall') {
                // Add initial processing reaction
                await this.reactToMessage(messageData, '🔔');
                
                try {
                    // Tag everyone in the group without a custom message
                    const success = await this.tagAllMembersLoud(messageData.from);
                    
                    if (success) {
                        await this.reactToMessage(messageData, '✅');
                    } else {
                        await this.reactToMessage(messageData, '❌');
                    }
                    setTimeout(() => this.removeReaction(messageData), 2000);
                } catch (error) {
                    console.error('❌ Error in tagall command:', error);
                    await this.reactToMessage(messageData, '❌');
                    setTimeout(() => this.removeReaction(messageData), 2000);
                }
            }
            
        } catch (error) {
            console.error('❌ Error processing command:', error);
        }
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m ${secs}s`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
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
                    text: '', // Empty text removes the reaction
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

    async measureNetworkSpeed() {
        try {
            const startTime = Date.now();
            
            // Use a more reliable endpoint for latency measurement
            await new Promise((resolve, reject) => {
                const https = require('https');
                const req = https.get('https://www.google.com/generate_204', (res) => {
                    res.on('data', () => {});
                    res.on('end', resolve);
                });
                req.on('error', () => {
                    // Fallback to localhost health check
                    const http = require('http');
                    const fallbackReq = http.get('http://localhost:8080/health', (res) => {
                        res.on('data', () => {});
                        res.on('end', resolve);
                    });
                    fallbackReq.on('error', reject);
                    fallbackReq.setTimeout(2000, () => {
                        fallbackReq.destroy();
                        reject(new Error('Timeout'));
                    });
                });
                req.setTimeout(3000, () => {
                    req.destroy();
                    // Don't reject immediately, let the fallback handle it
                });
            });
            
            const endTime = Date.now();
            const latency = endTime - startTime;
            return `${latency}ms`;
            
        } catch (error) {
            console.error('❌ Error measuring network speed:', error);
            return 'N/A';
        }
    }

    async tagAllMembers(groupId, message) {
        try {
            // Check if it's a group (group IDs end with @g.us)
            if (!groupId.includes('@g.us')) {
                await this.sendMessage(groupId, '❌ This command only works in groups!');
                return false;
            }

            // Get group metadata to fetch all participants
            const groupMetadata = await this.sock.groupMetadata(groupId);
            const participants = groupMetadata.participants;

            if (!participants || participants.length === 0) {
                await this.sendMessage(groupId, '❌ Could not fetch group members');
                return false;
            }

            // Create mentions array (exclude the bot itself)
            const mentions = participants
                .map(participant => participant.id)
                .filter(id => !id.includes(this.sock.user?.id || ''));

            // Create the message with all mentions
            const tagMessage = {
                text: `📢 ${message}`,
                mentions: mentions
            };

            // Send the message with all mentions
            await this.sock.sendMessage(groupId, tagMessage);
            console.log(`👥 Tagged ${mentions.length} members in group ${groupId}`);
            return true;

        } catch (error) {
            console.error('❌ Error tagging group members:', error);
            await this.sendMessage(groupId, '❌ Failed to tag group members. Make sure I have admin permissions.');
            return false;
        }
    }

    async tagAllMembersLoud(groupId) {
        try {
            // Check if it's a group (group IDs end with @g.us)
            if (!groupId.includes('@g.us')) {
                await this.sendMessage(groupId, '❌ This command only works in groups!');
                return false;
            }

            // Get group metadata to fetch all participants
            const groupMetadata = await this.sock.groupMetadata(groupId);
            const participants = groupMetadata.participants;

            if (!participants || participants.length === 0) {
                await this.sendMessage(groupId, '❌ Could not fetch group members');
                return false;
            }

            // Create mentions array (exclude the bot itself)
            const mentions = participants
                .map(participant => participant.id)
                .filter(id => !id.includes(this.sock.user?.id || ''));

            // Create a loud notification message that tags everyone
            let tagText = '🔔 *ATTENTION EVERYONE!* 🔔\n\n';
            
            // Add each mention on a separate numbered line
            for (let i = 0; i < mentions.length; i++) {
                const phoneNumber = mentions[i].split('@')[0];
                tagText += `${i + 1}. @${phoneNumber}\n`;
            }

            const tagMessage = {
                text: tagText,
                mentions: mentions
            };

            // Send the loud notification message
            await this.sock.sendMessage(groupId, tagMessage);
            console.log(`🔔 Loudly tagged ${mentions.length} members in group ${groupId}`);
            return true;

        } catch (error) {
            console.error('❌ Error tagging group members loudly:', error);
            await this.sendMessage(groupId, '❌ Failed to tag group members. Make sure I have admin permissions.');
            return false;
        }
    }

    startHealthServer() {
        try {
            const port = parseInt(process.env.PORT || '8080');
            
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