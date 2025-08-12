// Hybrid WhatsApp Bot using baileys-mod features with GitHub Baileys as fallback
const fs = require('fs');
const path = require('path');
const http = require('http');
const PluginManager = require('./plugins/pluginManager');
const MessageUtils = require('./utils/messageUtils');

// Try to use baileys-mod first, fallback to github baileys
let BaileysLib;
let useModVersion = false;

try {
    // Try baileys-mod first
    BaileysLib = require('baileys-mod');
    useModVersion = true;
    console.log('📱 Using baileys-mod library');
} catch (error) {
    // Fallback to github baileys
    BaileysLib = require('baileys');
    useModVersion = false;
    console.log('📱 Using GitHub Baileys library');
}

const { makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = BaileysLib;
const { Boom } = require('@hapi/boom');
const P = require('pino');

// Enhanced spam detection inspired by @neoxr/wb
class SpamDetection {
    constructor(options = {}) {
        this.RESET_TIMER = options.RESET_TIMER || 3000;
        this.HOLD_TIMER = options.HOLD_TIMER || 180000;
        this.userCooldowns = new Map();
    }

    detection(client, message, options = {}) {
        const { prefix, command, cooldown, show = 'all' } = options;
        const userId = message.key.participant || message.key.remoteJid;
        const cooldownKey = `${userId}-${command}`;
        const now = Date.now();

        const lastUsed = cooldown.get(cooldownKey);
        if (lastUsed && (now - lastUsed) < this.RESET_TIMER) {
            if (show === 'all' || show === 'spam-only') {
                console.log(`🚫 Spam detected: ${userId} command: ${command}`);
            }
            return true;
        }

        return false;
    }
}

class HybridWhatsAppBot {
    constructor() {
        this.client = null;
        this.sock = null;
        this.connected = false;
        this.sentMessageIds = new Set();
        this.startTime = Date.now();
        this.hasWelcomeBeenSent = false;
        this.useModVersion = useModVersion;
        
        // Load prefix from environment
        this.prefix = process.env.PREFIX === 'null' ? '' : (process.env.PREFIX || '.');
        this.ownerNumber = null;
        
        // Enhanced features
        this.commandCooldown = new Map();
        this.messageCache = new Map();
        this.botDetection = new Set();
        
        this.spam = new SpamDetection({
            RESET_TIMER: 3000,
            HOLD_TIMER: 180000,
            PERMANENT_THRESHOLD: 3,
            NOTIFY_THRESHOLD: 4,
            BANNED_THRESHOLD: 5
        });
        
        this.pluginManager = new PluginManager(this);
        this.messageUtils = null;
        
        console.log(`🔧 Command prefix: "${this.prefix || 'none'}"`);
        console.log(`🔧 Library: ${useModVersion ? 'baileys-mod' : 'GitHub Baileys'}`);
    }

    async initialize() {
        try {
            console.log('🔌 Starting Hybrid WhatsApp Bot...');
            
            this.startHealthServer();
            
            if (!await this.loadCredentials()) {
                console.error('❌ WHATSAPP_CREDS environment variable not found');
                return;
            }

            console.log('🚀 WhatsApp Bot starting...');

            // Create auth state
            const authDir = './wa-auth';
            if (!fs.existsSync(authDir)) {
                fs.mkdirSync(authDir);
            }

            const { state, saveCreds } = await useMultiFileAuthState(authDir);
            
            // Get latest version
            let version;
            try {
                const baileyVersion = await fetchLatestBaileysVersion();
                version = baileyVersion.version;
                console.log(`📱 Using version: ${version.join('.')}`);
            } catch (error) {
                version = [2, 3000, 1023223821];
            }

            // Enhanced socket configuration for hybrid approach
            const socketConfig = {
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
                browser: ['WhatsApp Bot Hybrid', 'Chrome', '10.0'],
                mobile: false,
                shouldIgnoreJid: jid => /(newsletter|bot)/.test(jid)
            };

            // Use baileys-mod specific features if available
            if (this.useModVersion) {
                socketConfig.options = {
                    phoneNumber: undefined,
                    timeoutMs: 30000
                };
            }

            this.sock = makeWASocket(socketConfig);
            this.sock.ev.on('creds.update', saveCreds);

            this.setupEventHandlers();
            await this.pluginManager.loadPlugins();
            
            console.log('✅ Hybrid WhatsApp bot initialized successfully');

        } catch (error) {
            console.error('❌ Failed to initialize bot:', error);
            process.exit(1);
        }
    }

    async loadCredentials() {
        try {
            const waCredsEnv = process.env.WHATSAPP_CREDS;
            if (waCredsEnv) {
                console.log('✅ Found WhatsApp credentials in environment');
                
                const authDir = './wa-auth';
                if (!fs.existsSync(authDir)) {
                    fs.mkdirSync(authDir, { recursive: true });
                }
                
                const credsData = JSON.parse(waCredsEnv);
                const credsPath = path.join(authDir, 'creds.json');
                fs.writeFileSync(credsPath, JSON.stringify(credsData, null, 2));
                
                if (credsData.me && credsData.me.id) {
                    this.ownerNumber = credsData.me.id.split(':')[0];
                    console.log('👤 Owner number extracted from credentials');
                }
                
                return true;
            }
            return false;
        } catch (error) {
            console.error('❌ Error loading credentials:', error);
            return false;
        }
    }

    setupEventHandlers() {
        this.sock.ev.on('connection.update', (update) => {
            this.handleConnectionUpdate(update);
        });

        this.sock.ev.on('messages.upsert', async (m) => {
            await this.handleMessages(m);
        });
    }

    async handleConnectionUpdate(update) {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr && !process.env.WHATSAPP_CREDS) {
            const QR = require('qrcode-terminal');
            QR.generate(qr, { small: true });
            console.log('⬆️ Scan the QR code above');
        }
        
        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('🔌 Connection closed, reconnecting:', shouldReconnect);
            
            if (shouldReconnect) {
                this.connected = false;
                const delay = Math.min(5000 + Math.random() * 5000, 30000);
                setTimeout(() => this.initialize(), delay);
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp Web connected successfully!');
            this.connected = true;
            
            this.messageUtils = new MessageUtils(this.sock);
            
            if (this.sock.user && this.sock.user.id && !this.ownerNumber) {
                this.ownerNumber = this.sock.user.id.split(':')[0];
                console.log('👤 Owner number extracted from socket');
            }
            
            await this.sendWelcomeMessage();
        } else if (connection === 'connecting') {
            console.log('🔄 Connecting to WhatsApp...');
        }
    }

    async handleMessages(m) {
        try {
            const messages = m.messages || [];
            
            for (const message of messages) {
                if (message.key.fromMe && this.sentMessageIds.has(message.key.id)) {
                    continue;
                }
                
                if (message.messageStubType || !message.message) {
                    continue;
                }

                if (this.isBotMessage(message.key.id)) {
                    continue;
                }

                const messageData = this.parseMessage(message);
                if (messageData && messageData.body) {
                    console.log(`📨 Message from ${messageData.from}: ${messageData.body}`);

                    if (this.isCommand(messageData.body)) {
                        const command = this.extractCommand(messageData.body);
                        
                        const isSpam = this.spam.detection(this.sock, message, {
                            prefix: this.prefix,
                            command,
                            commands: this.pluginManager ? this.pluginManager.getCommandList() : [],
                            users: {},
                            cooldown: this.commandCooldown,
                            show: 'all'
                        });

                        if (!isSpam) {
                            await this.processCommand(messageData);
                        }
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

            if (message.message?.conversation) {
                messageData.body = message.message.conversation;
            } else if (message.message?.extendedTextMessage?.text) {
                messageData.body = message.message.extendedTextMessage.text;
                
                if (message.message.extendedTextMessage.contextInfo?.quotedMessage) {
                    messageData.quotedMessage = {
                        participant: message.message.extendedTextMessage.contextInfo.participant,
                        id: message.message.extendedTextMessage.contextInfo.stanzaId
                    };
                }
            }

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

    isBotMessage(messageId) {
        if (!messageId) return false;
        return (
            (messageId.startsWith('3EB0') && messageId.length === 40) ||
            messageId.startsWith('BAE') ||
            /[-]/.test(messageId) ||
            this.botDetection.has(messageId)
        );
    }

    isCommand(text) {
        if (!text) return false;
        
        if (this.prefix === 'null' || this.prefix === null || this.prefix === '') {
            const commands = this.pluginManager ? this.pluginManager.getCommandList() : [];
            return commands.some(cmd => text.toLowerCase().startsWith(cmd.toLowerCase()));
        }
        
        return text.startsWith(this.prefix);
    }

    extractCommand(text) {
        if (this.prefix === 'null' || this.prefix === null || this.prefix === '') {
            return text.split(' ')[0].toLowerCase();
        } else {
            return text.slice(this.prefix.length).split(' ')[0].toLowerCase();
        }
    }

    async processCommand(messageData) {
        try {
            const message = messageData.body.trim();
            const command = message.toLowerCase();
            
            if (this.prefix && !command.startsWith(this.prefix)) {
                return;
            }
            
            const cleanCommand = this.prefix ? command.slice(this.prefix.length) : command;
            const commandParts = cleanCommand.split(' ');
            const commandName = commandParts[0];
            const args = commandParts.slice(1);
            
            await this.reactToMessage(messageData, '📋');
            
            if (this.pluginManager) {
                const success = await this.pluginManager.executeCommand(messageData, commandName, args);
                
                if (success) {
                    await this.reactToMessage(messageData, '✅');
                    setTimeout(() => this.removeReaction(messageData), 3000);
                } else {
                    await this.reactToMessage(messageData, '❓');
                    setTimeout(() => this.removeReaction(messageData), 3000);
                }
            }
            
            this.updateCooldown(messageData.from, commandName);
            
        } catch (error) {
            console.error('❌ Error processing command:', error);
            await this.reactToMessage(messageData, '❌');
        }
    }

    updateCooldown(sender, command) {
        const cooldownKey = `${sender}-${command}`;
        this.commandCooldown.set(cooldownKey, Date.now());
        
        const oneMinuteAgo = Date.now() - 60000;
        for (const [key, timestamp] of this.commandCooldown.entries()) {
            if (timestamp < oneMinuteAgo) {
                this.commandCooldown.delete(key);
            }
        }
    }

    async sendMessage(to, message) {
        try {
            if (!this.connected || !this.sock) {
                return false;
            }

            // Enhanced JID handling for hybrid compatibility
            let targetJid = to;
            
            // Normalize JID format
            if (!to.includes('@')) {
                targetJid = to.includes('-') ? `${to}@g.us` : `${to}@s.whatsapp.net`;
            }

            // Use different message sending approaches based on library
            if (this.useModVersion) {
                // baileys-mod approach
                await this.sock.sendMessage(targetJid, { text: message });
            } else {
                // GitHub Baileys approach with enhanced error handling
                try {
                    await this.sock.sendMessage(targetJid, { text: message });
                } catch (jidError) {
                    // Try with different JID format
                    const altJid = targetJid.includes('@g.us') ? 
                        targetJid.replace('@g.us', '@s.whatsapp.net') : 
                        targetJid.replace('@s.whatsapp.net', '@g.us');
                    
                    await this.sock.sendMessage(altJid, { text: message });
                    targetJid = altJid;
                }
            }

            console.log(`📤 Message sent to ${targetJid}`);
            return true;

        } catch (error) {
            console.error('❌ Error sending message:', error);
            return false;
        }
    }

    async reactToMessage(messageData, emoji) {
        try {
            if (!this.connected || !this.sock) return false;

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
            console.log(`⚡ Reacted with ${emoji}`);
            return true;
        } catch (error) {
            console.error('❌ Error reacting:', error);
            return false;
        }
    }

    async removeReaction(messageData) {
        try {
            if (!this.connected || !this.sock) return false;

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
            return true;
        } catch (error) {
            return false;
        }
    }

    async sendWelcomeMessage() {
        try {
            if (this.hasWelcomeBeenSent || !this.ownerNumber || !this.connected) {
                return false;
            }

            const welcomeText = `🎉 Hybrid WhatsApp Bot Connected!

⏰ Connection Time: ${new Date().toLocaleString()}
📱 Bot Status: Online and Ready  
🔧 Command Prefix: ${this.prefix === 'null' || this.prefix === '' ? 'No prefix required' : this.prefix}
🔌 Plugins: ${this.pluginManager ? this.pluginManager.loadedCount : 0} loaded
📚 Library: ${this.useModVersion ? 'baileys-mod' : 'GitHub Baileys'} (Hybrid)
🛡️ Features: Enhanced spam detection, hybrid compatibility

📋 Available Commands:
${this.prefix === 'null' || this.prefix === '' ? '' : this.prefix}menu - Show all commands
${this.prefix === 'null' || this.prefix === '' ? '' : this.prefix}ping - Check bot status
${this.prefix === 'null' || this.prefix === '' ? '' : this.prefix}buttons - Interactive buttons
${this.prefix === 'null' || this.prefix === '' ? '' : this.prefix}list - Interactive lists

🚀 Hybrid bot ready for commands!`;

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
                        library: this.useModVersion ? 'baileys-mod (hybrid)' : 'GitHub Baileys (hybrid)',
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
                    server.listen(port);
                }
            });

            server.listen(port, '0.0.0.0', () => {
                console.log(`🏥 Health server running on port ${port}`);
            });

        } catch (error) {
            console.error('❌ Error starting health server:', error);
        }
    }
}

// Start the hybrid bot
const bot = new HybridWhatsAppBot();
bot.initialize();

process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down Hybrid Bot...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down Hybrid Bot...');
    process.exit(0);
});