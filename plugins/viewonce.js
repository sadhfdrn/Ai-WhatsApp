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

            // Get the quoted message details
            const quotedMessageId = messageData.quotedMessage.id;
            const quotedParticipant = messageData.quotedMessage.participant;

            // Try to fetch the original message
            const originalMessage = await this.getQuotedMessage(messageData);
            
            if (!originalMessage) {
                await this.bot.sendMessage(messageData.from, '❌ Could not retrieve the quoted message');
                return true;
            }

            // Check if it's a view-once message
            if (this.isViewOnceMessage(originalMessage)) {
                const mediaData = await this.extractViewOnceMedia(originalMessage);
                
                if (mediaData) {
                    // Send the media without view-once restriction
                    await this.sendMediaWithoutViewOnce(messageData.from, mediaData);
                    await this.bot.sendMessage(messageData.from, '✅ View-once message converted and sent!');
                } else {
                    await this.bot.sendMessage(messageData.from, '❌ Could not extract media from view-once message');
                }
            } else {
                await this.bot.sendMessage(messageData.from, '❌ The quoted message is not a view-once message');
            }

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

            // Get the quoted message
            const originalMessage = await this.getQuotedMessage(messageData);
            
            if (!originalMessage) {
                await this.bot.sendMessage(messageData.from, '❌ Could not retrieve the quoted message');
                return true;
            }

            // Save different types of messages
            const saved = await this.saveMessageToDM(originalMessage, messageData);
            
            if (saved) {
                await this.bot.sendMessage(messageData.from, '✅ Message saved to your DM!');
            } else {
                await this.bot.sendMessage(messageData.from, '❌ Could not save the message');
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
            // In a real implementation, you would fetch the actual quoted message
            // For now, we'll simulate based on the context info
            const contextInfo = messageData.quotedMessage;
            
            // Try to get message from cache or fetch from WhatsApp
            const messageKey = {
                remoteJid: messageData.from,
                fromMe: false,
                id: contextInfo.id,
                participant: contextInfo.participant
            };

            // Attempt to get the message using Baileys getMessage
            if (this.bot.sock && this.bot.sock.getMessage) {
                return await this.bot.sock.getMessage(messageKey);
            }

            return null;
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