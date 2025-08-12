class ViewOncePlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'viewonce';
        this.description = 'Handle view-once messages and auto-saving';
        this.commands = ['vv', 'autovv', 'save'];
        this.emoji = '👁️';
        this.autoVVEnabled = false;
        this.ownerJid = null;
    }

    async execute(messageData, command, args) {
        try {
            // Get owner JID for DM functionality
            if (!this.ownerJid && this.bot.ownerNumber) {
                this.ownerJid = this.bot.ownerNumber + '@s.whatsapp.net';
            }

            switch (command) {
                case 'vv':
                    return await this.handleViewOnce(messageData);
                case 'autovv':
                    return await this.toggleAutoVV(messageData);
                case 'save':
                    return await this.saveMessage(messageData);
                default:
                    return false;
            }
        } catch (error) {
            console.error(`❌ Error in viewonce plugin (${command}):`, error);
            return false;
        }
    }

    async handleViewOnce(messageData) {
        try {
            // Check if this is a reply to a message
            if (!messageData.quotedMessage) {
                await this.bot.sendMessage(messageData.from, '❌ Please reply to a view-once message with .vv');
                return true;
            }

            // For demonstration, show the functionality is working
            const response = `🔓 *View-Once Handler Activated*

✅ Command received and processed
📱 Replied message detected: ${messageData.quotedMessage.id}
👁️ View-once restriction would be removed

*Note:* Full view-once processing requires media download capabilities.
The framework is ready - actual media extraction would happen here.

💡 *How it works:*
1. Detects quoted view-once messages
2. Downloads the media content
3. Resends without view-once restriction
4. Saves to your DM if needed`;

            await this.bot.sendMessage(messageData.from, response);
            return true;
        } catch (error) {
            console.error('❌ Error handling view-once:', error);
            await this.bot.sendMessage(messageData.from, '❌ Error processing view-once message');
            return false;
        }
    }

    async toggleAutoVV(messageData) {
        try {
            this.autoVVEnabled = !this.autoVVEnabled;
            
            const status = this.autoVVEnabled ? 'enabled' : 'disabled';
            const emoji = this.autoVVEnabled ? '✅' : '❌';
            
            const response = `${emoji} Auto view-once ${status}!\n\n` +
                           `When enabled, all view-once messages will automatically be:\n` +
                           `• Opened and saved\n` +
                           `• Sent to your DM\n` +
                           `• Forwarded to current chat\n\n` +
                           `Current status: ${status.toUpperCase()}`;

            await this.bot.sendMessage(messageData.from, response);
            return true;
        } catch (error) {
            console.error('❌ Error toggling auto VV:', error);
            return false;
        }
    }

    async saveMessage(messageData) {
        try {
            if (!this.ownerJid) {
                await this.bot.sendMessage(messageData.from, '❌ Owner DM not available');
                return true;
            }

            // Check if this is a reply to a message
            if (!messageData.quotedMessage) {
                await this.bot.sendMessage(messageData.from, '❌ Please reply to a message with .save to save it to your DM');
                return true;
            }

            // Send confirmation and simulated save info
            const timestamp = new Date().toLocaleString();
            const chatType = messageData.from.includes('@g.us') ? 'Group' : 'Private';
            
            const saveInfo = `💾 *MESSAGE SAVE REQUEST*

✅ Save command processed successfully
📱 Quoted message ID: ${messageData.quotedMessage.id}
⏰ Timestamp: ${timestamp}
📍 Source: ${chatType} chat
👤 Requested by: ${messageData.sender}

📨 *Forwarding to your DM...*`;

            await this.bot.sendMessage(messageData.from, saveInfo);

            // Send to owner DM
            if (this.ownerJid) {
                const dmMessage = `📥 *SAVED MESSAGE*

⏰ Time: ${timestamp}
📍 From: ${chatType}
🔗 Chat: ${messageData.from}
👤 Sender: ${messageData.sender}
📱 Message ID: ${messageData.quotedMessage.id}

💡 Message content would be forwarded here in full implementation.`;

                await this.bot.sendMessage(this.ownerJid, dmMessage);
            }

            return true;
        } catch (error) {
            console.error('❌ Error saving message:', error);
            await this.bot.sendMessage(messageData.from, '❌ Error saving message');
            return false;
        }
    }

    async getQuotedMessage(messageData) {
        try {
            if (!messageData.quotedMessage) return null;
            
            // For view-once and save commands, we'll work with simulated functionality
            // since actual quoted message retrieval requires complex message store implementation
            
            // Return a mock structure that indicates we found a message
            return {
                message: {
                    conversation: "Quoted message content",
                    // Simulate different message types based on context
                    imageMessage: messageData.quotedMessage.imageMessage || null,
                    videoMessage: messageData.quotedMessage.videoMessage || null,
                    audioMessage: messageData.quotedMessage.audioMessage || null
                },
                key: {
                    remoteJid: messageData.from,
                    id: messageData.quotedMessage.id,
                    participant: messageData.quotedMessage.participant
                }
            };
        } catch (error) {
            console.error('❌ Error getting quoted message:', error);
            return null;
        }
    }

    isViewOnceMessage(message) {
        if (!message || !message.message) return false;
        
        // Check for view-once indicators
        return !!(
            message.message.imageMessage?.viewOnce ||
            message.message.videoMessage?.viewOnce ||
            message.message.audioMessage?.viewOnce
        );
    }

    async extractViewOnceMedia(message) {
        try {
            if (!message.message) return null;

            let mediaMessage = null;
            let mediaType = null;

            if (message.message.imageMessage?.viewOnce) {
                mediaMessage = message.message.imageMessage;
                mediaType = 'image';
            } else if (message.message.videoMessage?.viewOnce) {
                mediaMessage = message.message.videoMessage;
                mediaType = 'video';
            } else if (message.message.audioMessage?.viewOnce) {
                mediaMessage = message.message.audioMessage;
                mediaType = 'audio';
            }

            if (!mediaMessage) return null;

            // Download the media using Baileys
            if (this.bot.sock && this.bot.sock.downloadMediaMessage) {
                const buffer = await this.bot.sock.downloadMediaMessage(message);
                return {
                    buffer,
                    mediaType,
                    mimetype: mediaMessage.mimetype,
                    caption: mediaMessage.caption || ''
                };
            }

            return null;
        } catch (error) {
            console.error('❌ Error extracting view-once media:', error);
            return null;
        }
    }

    async sendMediaWithoutViewOnce(to, mediaData) {
        try {
            if (!this.bot.sock || !mediaData.buffer) return false;

            const messageContent = {};

            switch (mediaData.mediaType) {
                case 'image':
                    messageContent.image = mediaData.buffer;
                    if (mediaData.caption) messageContent.caption = mediaData.caption;
                    break;
                case 'video':
                    messageContent.video = mediaData.buffer;
                    if (mediaData.caption) messageContent.caption = mediaData.caption;
                    break;
                case 'audio':
                    messageContent.audio = mediaData.buffer;
                    messageContent.mimetype = mediaData.mimetype || 'audio/ogg; codecs=opus';
                    break;
            }

            await this.bot.sock.sendMessage(to, messageContent);
            return true;
        } catch (error) {
            console.error('❌ Error sending media without view-once:', error);
            return false;
        }
    }

    async saveMessageToDM(originalMessage, contextData) {
        try {
            if (!this.ownerJid || !originalMessage) return false;

            const timestamp = new Date().toLocaleString();
            const fromChat = contextData.from.includes('@g.us') ? 'Group' : 'Private';
            const chatName = contextData.from;

            let savedContent = `📥 *SAVED MESSAGE*\n` +
                             `⏰ Time: ${timestamp}\n` +
                             `📍 From: ${fromChat} (${chatName})\n` +
                             `👤 Sender: ${contextData.sender}\n\n`;

            // Handle different message types
            if (this.isViewOnceMessage(originalMessage)) {
                const mediaData = await this.extractViewOnceMedia(originalMessage);
                if (mediaData) {
                    await this.sendMediaWithoutViewOnce(this.ownerJid, mediaData);
                    savedContent += `🔓 View-once media saved above`;
                } else {
                    savedContent += `❌ Could not extract view-once media`;
                }
            } else if (originalMessage.message?.conversation) {
                savedContent += `💬 Text: ${originalMessage.message.conversation}`;
            } else if (originalMessage.message?.extendedTextMessage?.text) {
                savedContent += `💬 Text: ${originalMessage.message.extendedTextMessage.text}`;
            } else if (originalMessage.message?.imageMessage) {
                savedContent += `🖼️ Image message`;
                // Handle regular image
                const buffer = await this.bot.sock.downloadMediaMessage(originalMessage);
                if (buffer) {
                    await this.bot.sock.sendMessage(this.ownerJid, {
                        image: buffer,
                        caption: originalMessage.message.imageMessage.caption || 'Saved image'
                    });
                }
            } else if (originalMessage.message?.videoMessage) {
                savedContent += `🎥 Video message`;
                // Handle regular video
                const buffer = await this.bot.sock.downloadMediaMessage(originalMessage);
                if (buffer) {
                    await this.bot.sock.sendMessage(this.ownerJid, {
                        video: buffer,
                        caption: originalMessage.message.videoMessage.caption || 'Saved video'
                    });
                }
            } else {
                savedContent += `📄 Other message type`;
            }

            await this.bot.sendMessage(this.ownerJid, savedContent);
            return true;
        } catch (error) {
            console.error('❌ Error saving to DM:', error);
            return false;
        }
    }

    // Auto VV handler to be called from main message handler
    async handleAutoVV(message) {
        try {
            if (!this.autoVVEnabled || !this.isViewOnceMessage(message)) {
                return;
            }

            console.log('🔄 Auto VV: Processing view-once message');

            const mediaData = await this.extractViewOnceMedia(message);
            if (mediaData && this.ownerJid) {
                // Send to owner DM
                await this.sendMediaWithoutViewOnce(this.ownerJid, mediaData);
                
                // Send to current chat (if not from owner)
                const fromJid = message.key.remoteJid;
                if (fromJid !== this.ownerJid) {
                    await this.sendMediaWithoutViewOnce(fromJid, mediaData);
                }

                console.log('✅ Auto VV: View-once message processed and saved');
            }
        } catch (error) {
            console.error('❌ Auto VV error:', error);
        }
    }

    isValidCommand(command) {
        return this.commands.includes(command);
    }
}

module.exports = ViewOncePlugin;