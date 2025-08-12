class AntiDeletePlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'antidelete';
        this.description = 'Forward deleted messages to owner DM';
        this.commands = ['antidelete'];
        this.emoji = '🗑️';
        this.ownerJid = null;
        this.antiDeleteEnabled = {
            pm: false,      // Private messages
            chat: false     // Group chats
        };
        this.messageCache = new Map(); // Store messages temporarily
        this.maxCacheSize = 2000;
        
        // Listen for message deletions
        this.setupDeleteListener();
    }

    async execute(messageData, command, args) {
        try {
            // Get owner JID for DM functionality
            if (!this.ownerJid && this.bot.ownerNumber) {
                this.ownerJid = this.bot.ownerNumber + '@s.whatsapp.net';
            }

            if (command === 'antidelete') {
                return await this.handleAntiDelete(messageData, args);
            }

            return false;
        } catch (error) {
            console.error(`❌ Error in antidelete plugin (${command}):`, error);
            return false;
        }
    }

    async handleAntiDelete(messageData, args) {
        try {
            if (!args || args.length === 0) {
                // Show current status
                const status = `🗑️ *ANTI-DELETE STATUS*\n\n` +
                             `📱 Private Messages: ${this.antiDeleteEnabled.pm ? '✅ ON' : '❌ OFF'}\n` +
                             `👥 Group Chats: ${this.antiDeleteEnabled.chat ? '✅ ON' : '❌ OFF'}\n\n` +
                             `📝 Usage:\n` +
                             `.antidelete on pm - Enable for private messages\n` +
                             `.antidelete off pm - Disable for private messages\n` +
                             `.antidelete on chat - Enable for group chats\n` +
                             `.antidelete off chat - Disable for group chats`;

                if (this.ownerJid) {
                    await this.bot.sendMessage(this.ownerJid, status);
                }
                return true;
            }

            const action = args[0]?.toLowerCase();
            const type = args[1]?.toLowerCase();

            if (!['on', 'off'].includes(action) || !['pm', 'chat'].includes(type)) {
                if (this.ownerJid) {
                    await this.bot.sendMessage(this.ownerJid, '❌ Invalid command. Use: .antidelete on/off pm/chat');
                }
                return true;
            }

            // Update setting
            this.antiDeleteEnabled[type] = action === 'on';

            const typeLabel = type === 'pm' ? 'Private Messages' : 'Group Chats';
            const statusEmoji = action === 'on' ? '✅' : '❌';
            const statusText = action === 'on' ? 'ENABLED' : 'DISABLED';

            const response = `${statusEmoji} *ANTI-DELETE ${statusText}*\n\n` +
                           `📍 Target: ${typeLabel}\n` +
                           `🔄 Status: ${statusText}\n\n` +
                           `${action === 'on' ? 'Deleted messages will now be forwarded to your DM' : 'Deleted message forwarding disabled'}`;

            if (this.ownerJid) {
                await this.bot.sendMessage(this.ownerJid, response);
            }

            return true;
        } catch (error) {
            console.error('❌ Error handling antidelete command:', error);
            if (this.ownerJid) {
                await this.bot.sendMessage(this.ownerJid, '❌ Error processing antidelete command');
            }
            return false;
        }
    }

    setupDeleteListener() {
        // The bot will handle this through the main event system
        // This method will be called from main.js
        console.log('🗑️ Anti-delete listener setup complete');
    }

    // Called by main bot when a new message arrives
    onMessageReceived(message) {
        if (message.key && message.message) {
            this.cacheMessage(message);
        }
    }

    // Called by main bot when messages are updated/deleted
    onMessageUpdate(updates) {
        updates.forEach(update => {
            if (update.update?.message === null) {
                // Message was deleted
                this.handleMessageDeletion(update);
            }
        });
    }

    cacheMessage(message) {
        try {
            // Clean cache if it gets too large
            if (this.messageCache.size >= this.maxCacheSize) {
                const oldestKey = this.messageCache.keys().next().value;
                this.messageCache.delete(oldestKey);
            }

            // Store message with key as identifier
            const messageKey = `${message.key.remoteJid}_${message.key.id}`;
            this.messageCache.set(messageKey, {
                key: message.key,
                message: message.message,
                messageTimestamp: message.messageTimestamp,
                pushName: message.pushName,
                participant: message.key.participant,
                cached: Date.now()
            });

            console.log(`💾 Cached message: ${messageKey}`);
        } catch (error) {
            console.error('❌ Error caching message:', error);
        }
    }

    async handleMessageDeletion(update) {
        try {
            const messageKey = `${update.key.remoteJid}_${update.key.id}`;
            const cachedMessage = this.messageCache.get(messageKey);

            if (!cachedMessage) {
                console.log(`🗑️ Deleted message not found in cache: ${messageKey}`);
                
                // Send notification about missed deletion
                if (this.ownerJid) {
                    const chatType = update.key.remoteJid.includes('@g.us') ? 'Group' : 'Private';
                    const missedMsg = `🗑️ *MISSED DELETION*\n` +
                                    `📍 From: ${chatType} (${update.key.remoteJid})\n` +
                                    `⚠️ Message was deleted but not cached\n` +
                                    `📝 This usually means the message was deleted very quickly`;
                    
                    const shouldNotify = (update.key.remoteJid.includes('@g.us') && this.antiDeleteEnabled.chat) || 
                                       (!update.key.remoteJid.includes('@g.us') && this.antiDeleteEnabled.pm);
                    
                    if (shouldNotify) {
                        await this.bot.sendMessage(this.ownerJid, missedMsg);
                    }
                }
                return;
            }

            // Check if anti-delete is enabled for this chat type
            const isGroupChat = update.key.remoteJid.includes('@g.us');
            const isPrivateChat = !isGroupChat;

            const shouldForward = (isPrivateChat && this.antiDeleteEnabled.pm) || 
                                (isGroupChat && this.antiDeleteEnabled.chat);

            if (!shouldForward || !this.ownerJid) {
                console.log(`🗑️ Anti-delete not enabled for this chat type or no owner JID`);
                return;
            }

            console.log(`🗑️ Forwarding deleted message: ${messageKey}`);

            // Get message content
            const messageContent = await this.extractMessageContent(cachedMessage);
            
            // Prepare deletion notification
            const chatType = isGroupChat ? 'Group' : 'Private';
            const senderInfo = cachedMessage.participant || update.key.remoteJid;
            const deletionTime = new Date().toLocaleString();
            const originalTime = cachedMessage.messageTimestamp ? 
                new Date(Number(cachedMessage.messageTimestamp) * 1000).toLocaleString() : 'Unknown';

            const header = `🗑️ *DELETED MESSAGE DETECTED*\n` +
                         `⏰ Deleted: ${deletionTime}\n` +
                         `📅 Original: ${originalTime}\n` +
                         `📍 From: ${chatType} (${update.key.remoteJid})\n` +
                         `👤 Sender: ${senderInfo}\n` +
                         `💬 Name: ${cachedMessage.pushName || 'Unknown'}\n\n` +
                         `📝 Content:`;

            await this.bot.sendMessage(this.ownerJid, header);

            // Forward the actual content
            if (messageContent.media) {
                await this.forwardMedia(messageContent);
            } else if (messageContent.text) {
                await this.bot.sendMessage(this.ownerJid, `💬 "${messageContent.text}"`);
            } else {
                await this.bot.sendMessage(this.ownerJid, '📄 Message type not supported for recovery');
            }

            // Remove from cache after forwarding
            this.messageCache.delete(messageKey);

        } catch (error) {
            console.error('❌ Error handling message deletion:', error);
        }
    }

    async extractMessageContent(cachedMessage) {
        try {
            const msg = cachedMessage.message;
            let content = { text: null, media: null, type: 'unknown' };

            // Text messages
            if (msg.conversation) {
                content.text = msg.conversation;
                content.type = 'text';
            } else if (msg.extendedTextMessage?.text) {
                content.text = msg.extendedTextMessage.text;
                content.type = 'text';
            }
            // Image messages
            else if (msg.imageMessage) {
                content.media = {
                    type: 'image',
                    message: { imageMessage: msg.imageMessage },
                    key: cachedMessage.key,
                    caption: msg.imageMessage.caption || ''
                };
                content.type = 'image';
            }
            // Video messages
            else if (msg.videoMessage) {
                content.media = {
                    type: 'video',
                    message: { videoMessage: msg.videoMessage },
                    key: cachedMessage.key,
                    caption: msg.videoMessage.caption || ''
                };
                content.type = 'video';
            }
            // Audio messages
            else if (msg.audioMessage) {
                content.media = {
                    type: 'audio',
                    message: { audioMessage: msg.audioMessage },
                    key: cachedMessage.key,
                    mimetype: msg.audioMessage.mimetype
                };
                content.type = 'audio';
            }
            // Document messages
            else if (msg.documentMessage) {
                content.media = {
                    type: 'document',
                    message: { documentMessage: msg.documentMessage },
                    key: cachedMessage.key,
                    filename: msg.documentMessage.fileName || 'document'
                };
                content.type = 'document';
            }

            return content;
        } catch (error) {
            console.error('❌ Error extracting message content:', error);
            return { text: null, media: null, type: 'error' };
        }
    }

    async forwardMedia(mediaContent) {
        try {
            const { downloadMediaMessage } = require('baileys');
            
            // Create message structure for download
            const messageForDownload = {
                key: mediaContent.key,
                message: mediaContent.message
            };

            const buffer = await downloadMediaMessage(
                messageForDownload,
                'buffer',
                {},
                {
                    logger: console,
                    reuploadRequest: this.bot.sock.updateMediaMessage
                }
            );

            if (buffer) {
                // Forward the media
                switch (mediaContent.type) {
                    case 'image':
                        await this.bot.sock.sendMessage(this.ownerJid, {
                            image: buffer,
                            caption: `🖼️ Deleted Image${mediaContent.caption ? `\nOriginal Caption: ${mediaContent.caption}` : ''}`
                        });
                        break;
                    case 'video':
                        await this.bot.sock.sendMessage(this.ownerJid, {
                            video: buffer,
                            caption: `🎥 Deleted Video${mediaContent.caption ? `\nOriginal Caption: ${mediaContent.caption}` : ''}`
                        });
                        break;
                    case 'audio':
                        await this.bot.sock.sendMessage(this.ownerJid, {
                            audio: buffer,
                            mimetype: mediaContent.mimetype || 'audio/ogg; codecs=opus'
                        });
                        await this.bot.sendMessage(this.ownerJid, '🎵 Deleted Audio/Voice Message');
                        break;
                    case 'document':
                        await this.bot.sock.sendMessage(this.ownerJid, {
                            document: buffer,
                            fileName: mediaContent.filename,
                            mimetype: 'application/octet-stream'
                        });
                        await this.bot.sendMessage(this.ownerJid, `📄 Deleted Document: ${mediaContent.filename}`);
                        break;
                }
            } else {
                await this.bot.sendMessage(this.ownerJid, `❌ Could not recover deleted ${mediaContent.type}`);
            }
        } catch (error) {
            console.error('❌ Error forwarding media:', error);
            await this.bot.sendMessage(this.ownerJid, `❌ Error recovering deleted ${mediaContent.type}`);
        }
    }
}

module.exports = AntiDeletePlugin;