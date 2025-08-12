// Load config first
global.db = { users: [], chats: [], groups: [], statistic: {}, sticker: {}, setting: {} }

const { Component } = require('@neoxr/wb')
const { Baileys, Function: Func, Config: env } = new Component
const PluginManager = require('./plugins/pluginManager')
const http = require('http')
const fs = require('fs')
const path = require('path')

class WhatsAppBotNeoxr {
    constructor() {
        this.connected = false
        this.sock = null
        this.client = null
        this.hasWelcomeBeenSent = false
        this.ownerNumber = null
        this.pluginManager = null
        this.prefix = process.env.PREFIX || '.'
        
        console.log(`🔧 Command prefix set to: "${this.prefix}"`)
        console.log('🔌 Starting WhatsApp Bot with @neoxr/wb...')
        
        this.init()
    }

    async init() {
        try {
            // Load WhatsApp credentials
            if (!this.loadCredentials()) {
                console.error('❌ Failed to load WhatsApp credentials')
                return
            }

            // Initialize plugin system
            this.pluginManager = new PluginManager(this)
            await this.pluginManager.loadPlugins()

            // Start health server
            this.startHealthServer()

            // Initialize @neoxr/wb client
            await this.initializeClient()

        } catch (error) {
            console.error('❌ Error initializing bot:', error)
            setTimeout(() => this.init(), 5000)
        }
    }

    loadCredentials() {
        try {
            const credsEnv = process.env.WHATSAPP_CREDS
            if (credsEnv) {
                console.log('✅ Found WhatsApp credentials in environment')
                const creds = JSON.parse(credsEnv)
                if (creds.me && creds.me.id) {
                    this.ownerNumber = creds.me.id.split(':')[0]
                    console.log('👤 Owner number extracted from credentials')
                }
                console.log('✅ WhatsApp credentials loaded from environment')
                return true
            } else {
                console.error('❌ WHATSAPP_CREDS environment variable not found')
                return false
            }
        } catch (error) {
            console.error('❌ Error loading credentials:', error)
            return false
        }
    }

    async initializeClient() {
        try {
            console.log('🚀 WhatsApp Bot starting...')

            // Create @neoxr/wb client
            this.client = new Baileys({
                type: '--neoxr-v1',
                session: 'wa-auth',
                online: true,
                bypass_disappearing: true,
                bot: id => {
                    // Detect message from bot by message ID
                    return id && ((id.startsWith('3EB0') && id.length === 40) || id.startsWith('BAE') || /[-]/.test(id))
                },
                version: [2, 3000, 1023223821]
            }, {
                browser: ['WhatsApp Bot', 'Chrome', '137.0.7151.107'],
                shouldIgnoreJid: jid => {
                    return /(newsletter|bot)/.test(jid)
                }
            })

            console.log(`📱 Using @neoxr/wb with Baileys version: ${require('@neoxr/wb/package.json').version}`)

            // Setup event handlers
            this.setupEventHandlers()

            console.log('✅ WhatsApp bot initialized successfully')

        } catch (error) {
            console.error('❌ Error initializing client:', error)
            setTimeout(() => this.initializeClient(), 5000)
        }
    }

    setupEventHandlers() {
        // Connection established
        this.client.once('connect', async (connectionInfo) => {
            console.log('🔄 Connecting to WhatsApp...')
        })

        // Bot is ready
        this.client.once('ready', async () => {
            this.connected = true
            this.sock = this.client.sock
            console.log('✅ WhatsApp Web connected successfully!')
            
            // Extract owner number from socket if not already set
            if (this.sock.user && this.sock.user.id && !this.ownerNumber) {
                this.ownerNumber = this.sock.user.id.split(':')[0]
                console.log('👤 Owner number extracted from socket connection')
            }

            // Send welcome message
            await this.sendWelcomeMessage()
        })

        // Handle incoming messages
        this.client.register('message', async (m) => {
            try {
                await this.handleMessages(m)
            } catch (error) {
                console.error('❌ Error handling message:', error)
            }
        })

        // Handle disconnection
        this.client.once('disconnect', (reason) => {
            this.connected = false
            console.log('🔄 Disconnected from WhatsApp:', reason)
            console.log('🔄 Attempting to reconnect...')
            setTimeout(() => this.initializeClient(), 5000)
        })

        // Handle errors
        this.client.once('error', (error) => {
            console.error('❌ WhatsApp client error:', error)
        })
    }

    async handleMessages(m) {
        try {
            if (!m || !m.message || m.key.fromMe) return

            const messageType = Object.keys(m.message)[0]
            if (['protocolMessage', 'senderKeyDistributionMessage'].includes(messageType)) {
                console.log('⚠️ Skipping protocol message')
                return
            }

            // Extract message data
            const messageData = this.extractMessageData(m)
            if (!messageData) return

            console.log(`📨 Message from ${messageData.from}: ${messageData.text}`)

            // Check if it's a command
            if (this.isCommand(messageData.text)) {
                await this.processCommand(messageData)
            }

        } catch (error) {
            console.error('❌ Error in message handler:', error)
        }
    }

    extractMessageData(m) {
        try {
            const messageType = Object.keys(m.message)[0]
            let text = ''

            switch (messageType) {
                case 'conversation':
                    text = m.message.conversation
                    break
                case 'extendedTextMessage':
                    text = m.message.extendedTextMessage.text
                    break
                case 'imageMessage':
                case 'videoMessage':
                case 'audioMessage':
                case 'documentMessage':
                    text = m.message[messageType].caption || ''
                    break
                default:
                    return null
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
            }
        } catch (error) {
            console.error('❌ Error extracting message data:', error)
            return null
        }
    }

    isCommand(text) {
        if (!text) return false
        
        if (this.prefix === 'null' || this.prefix === null) {
            // No prefix mode - check if message starts with known command
            const commands = this.pluginManager ? this.pluginManager.getAllCommands() : []
            return commands.some(cmd => text.toLowerCase().startsWith(cmd.toLowerCase()))
        }
        
        return text.startsWith(this.prefix)
    }

    async processCommand(messageData) {
        try {
            let command, args

            if (this.prefix === 'null' || this.prefix === null) {
                // No prefix mode
                const parts = messageData.text.split(' ')
                command = parts[0].toLowerCase()
                args = parts.slice(1)
            } else {
                // With prefix
                const parts = messageData.text.slice(this.prefix.length).split(' ')
                command = parts[0].toLowerCase()
                args = parts.slice(1)
            }

            if (!command) return

            // Execute command through plugin manager
            if (this.pluginManager) {
                await this.pluginManager.executeCommand(command, messageData, args)
            }

        } catch (error) {
            console.error('❌ Error processing command:', error)
        }
    }

    async sendMessage(to, message) {
        try {
            if (!this.connected || !this.sock) {
                console.log('⚠️ Not connected to WhatsApp - cannot send message')
                return false
            }

            await this.sock.sendMessage(to, { text: message })
            console.log(`📤 Message sent to ${to}`)
            return true

        } catch (error) {
            console.error('❌ Error sending message:', error)
            return false
        }
    }

    async reactToMessage(messageData, emoji) {
        try {
            if (!this.connected || !this.sock) {
                console.log('⚠️ Not connected to WhatsApp - cannot react')
                return false
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
            }

            await this.sock.sendMessage(messageData.from, reactionMessage)
            console.log(`⚡ Reacted with ${emoji} to message from ${messageData.from}`)
            return true

        } catch (error) {
            console.error('❌ Error reacting to message:', error)
            return false
        }
    }

    async removeReaction(messageData) {
        try {
            if (!this.connected || !this.sock) {
                console.log('⚠️ Not connected to WhatsApp - cannot remove reaction')
                return false
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
            }

            await this.sock.sendMessage(messageData.from, removeReactionMessage)
            console.log(`🗑️ Removed reaction from message from ${messageData.from}`)
            return true

        } catch (error) {
            console.error('❌ Error removing reaction:', error)
            return false
        }
    }

    async getGroupMetadata(groupJid) {
        try {
            if (!this.connected || !this.sock) {
                console.log('⚠️ Not connected to WhatsApp - cannot get group metadata')
                return null
            }

            const metadata = await this.sock.groupMetadata(groupJid)
            return metadata

        } catch (error) {
            console.error('❌ Error getting group metadata:', error)
            return null
        }
    }

    async sendWelcomeMessage() {
        try {
            if (this.hasWelcomeBeenSent || !this.ownerNumber || !this.connected) {
                return false
            }

            const welcomeText = `🎉 WhatsApp Bot Connected Successfully!

⏰ Connection Time: ${new Date().toLocaleString()}
📱 Bot Status: Online and Ready
🔧 Command Prefix: ${this.prefix === 'null' ? 'No prefix required' : this.prefix}
🔌 Plugins: ${this.pluginManager ? this.pluginManager.loadedCount : 0} loaded

📋 Available Commands:
${this.prefix === 'null' ? '' : this.prefix}menu - Show all commands
${this.prefix === 'null' ? '' : this.prefix}ping - Check bot status
${this.prefix === 'null' ? '' : this.prefix}help - Get help information

🚀 Bot is ready to receive commands!`

            const ownerJid = this.ownerNumber + '@s.whatsapp.net'
            const success = await this.sendMessage(ownerJid, welcomeText)
            
            if (success) {
                this.hasWelcomeBeenSent = true
                console.log('🎉 Welcome message sent to owner')
            }

            return success

        } catch (error) {
            console.error('❌ Error sending welcome message:', error)
            return false
        }
    }

    startHealthServer() {
        try {
            let port = process.env.PORT || 8080
            
            const server = http.createServer((req, res) => {
                if (req.url === '/health' || req.url === '/') {
                    res.writeHead(200, { 'Content-Type': 'application/json' })
                    res.end(JSON.stringify({
                        status: 'healthy',
                        connected: this.connected,
                        timestamp: new Date().toISOString(),
                        plugins: this.pluginManager ? this.pluginManager.loadedCount : 0
                    }))
                } else {
                    res.writeHead(404, { 'Content-Type': 'text/plain' })
                    res.end('Not Found')
                }
            })

            server.on('error', (err) => {
                if (err.code === 'EADDRINUSE') {
                    port = port + 1
                    console.log(`⚠️ Port ${port - 1} in use, trying port ${port}`)
                    server.listen(port)
                } else {
                    console.error('❌ Health server error:', err)
                }
            })

            server.listen(port, '0.0.0.0', () => {
                console.log(`🏥 Health check server running on port ${port}`)
            })

        } catch (error) {
            console.error('❌ Error starting health server:', error)
        }
    }
}

// Start the bot
new WhatsAppBotNeoxr()

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down WhatsApp Bot...')
    process.exit(0)
})

process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down WhatsApp Bot...')
    process.exit(0)
})