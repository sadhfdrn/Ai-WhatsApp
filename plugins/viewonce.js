// Import required Baileys functions
const { downloadMediaMessage, getContentType } = require('baileys');

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

            console.log('🔍 Processing view-once message...');
            console.log('📋 Quoted message structure:', JSON.stringify(messageData.quotedMessage, null, 2));
            
            // Get the quoted message content
            const quotedMsg = messageData.quotedMessage;
            
            // Try to get the full message from the original message if available
            let targetMessage = quotedMsg.message || quotedMsg.content;
            
            // If we have access to the original message from messageData, use that
            if (messageData.originalMessage && messageData.originalMessage.message && 
                messageData.originalMessage.message.extendedTextMessage && 
                messageData.originalMessage.message.extendedTextMessage.contextInfo &&
                messageData.originalMessage.message.extendedTextMessage.contextInfo.quotedMessage) {
                
                targetMessage = messageData.originalMessage.message.extendedTextMessage.contextInfo.quotedMessage;
                console.log('📱 Using contextInfo quoted message');
            }
            
            console.log('📋 Target message for processing:', JSON.stringify(targetMessage, null, 2));
            
            // Check if it's a view-once message
            if (this.isViewOnceMessage(targetMessage)) {
                console.log('👁️ View-once message detected, extracting media...');
                
                // Create proper message structure for extraction
                const messageForExtraction = {
                    message: targetMessage,
                    key: quotedMsg.key || {
                        id: quotedMsg.id,
                        remoteJid: messageData.from,
                        participant: quotedMsg.participant
                    }
                };
                
                // Extract and send the media without view-once restriction
                const mediaData = await this.extractViewOnceMedia(messageForExtraction);
                if (mediaData) {
                    console.log('✅ Media extracted, sending to chat and DM...');
                    
                    // Send the media back to the chat
                    await this.sendMediaWithoutViewOnce(messageData.from, mediaData);
                    
                    // Also save to owner DM if configured
                    if (this.ownerJid && messageData.from !== this.ownerJid) {
                        await this.sendMediaWithoutViewOnce(this.ownerJid, mediaData);
                        
                        const dmNotification = `🔓 *View-Once Revealed*
⏰ Time: ${new Date().toLocaleString()}
📍 From: ${messageData.from.includes('@g.us') ? 'Group' : 'Private'} chat
👤 Requested by: ${messageData.sender}
💾 Media saved above`;
                        
                        await this.bot.sendMessage(this.ownerJid, dmNotification);
                    }
                    
                    const confirmMsg = await this.bot.sendMessage(messageData.from, '✅ View-once media revealed and saved!');
                    
                    // Auto-delete confirmation message after 3 seconds for stealth
                    setTimeout(async () => {
                        try {
                            if (confirmMsg && confirmMsg.key) {
                                await this.bot.sock.sendMessage(messageData.from, {
                                    delete: confirmMsg.key
                                });
                            }
                        } catch (error) {
                            // Ignore deletion errors
                        }
                    }, 3000);
                } else {
                    console.log('❌ Failed to extract media');
                    await this.bot.sendMessage(messageData.from, '❌ Could not extract media from view-once message');
                }
            } else {
                // Not a view-once message, show what type it is
                const messageType = this.getMessageType(targetMessage);
                console.log(`❌ Not a view-once message, type: ${messageType}`);
                await this.bot.sendMessage(messageData.from, `❌ This is not a view-once message. Message type: ${messageType}`);
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

            const confirmMsg = await this.bot.sendMessage(messageData.from, response);
            
            // Auto-delete confirmation message after 5 seconds for stealth
            setTimeout(async () => {
                try {
                    if (confirmMsg && confirmMsg.key) {
                        await this.bot.sock.sendMessage(messageData.from, {
                            delete: confirmMsg.key
                        });
                    }
                } catch (error) {
                    // Ignore deletion errors
                }
            }, 5000);
            
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

            console.log('💾 Saving message to owner DM...');
            console.log('📋 Quoted message structure for save:', JSON.stringify(messageData.quotedMessage, null, 2));
            
            const timestamp = new Date().toLocaleString();
            const chatType = messageData.from.includes('@g.us') ? 'Group' : 'Private';
            
            // Get the target message content
            let targetMessage = messageData.quotedMessage.message || messageData.quotedMessage.content;
            
            // If we have access to the original message from messageData, use that
            if (messageData.originalMessage && messageData.originalMessage.message && 
                messageData.originalMessage.message.extendedTextMessage && 
                messageData.originalMessage.message.extendedTextMessage.contextInfo &&
                messageData.originalMessage.message.extendedTextMessage.contextInfo.quotedMessage) {
                
                targetMessage = messageData.originalMessage.message.extendedTextMessage.contextInfo.quotedMessage;
                console.log('📱 Using contextInfo quoted message for save');
            }
            
            console.log('📋 Target message for save:', JSON.stringify(targetMessage, null, 2));
            
            // Create proper message structure for saving
            const messageForSaving = {
                message: targetMessage,
                key: messageData.quotedMessage.key || {
                    id: messageData.quotedMessage.id,
                    remoteJid: messageData.from,
                    participant: messageData.quotedMessage.participant
                }
            };
            
            // Process the actual message content
            const success = await this.saveMessageToDM(messageForSaving, {
                from: messageData.from,
                sender: messageData.sender,
                timestamp: timestamp,
                chatType: chatType
            });
            
            if (success) {
                const confirmMsg = await this.bot.sendMessage(messageData.from, '✅ Message saved to your DM successfully!');
                
                // Auto-delete confirmation message after 3 seconds for stealth
                setTimeout(async () => {
                    try {
                        if (confirmMsg && confirmMsg.key) {
                            await this.bot.sock.sendMessage(messageData.from, {
                                delete: confirmMsg.key
                            });
                        }
                    } catch (error) {
                        // Ignore deletion errors
                    }
                }, 3000);
            } else {
                await this.bot.sendMessage(messageData.from, '❌ Failed to save message to DM');
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
        if (!message) return false;
        
        // Handle different message structure formats
        const msg = message.message || message;
        
        // Check for view-once indicators
        return !!(
            msg.imageMessage?.viewOnce ||
            msg.videoMessage?.viewOnce ||
            msg.audioMessage?.viewOnce
        );
    }
    
    getMessageType(message) {
        if (!message) return 'unknown';
        
        const msg = message.message || message;
        
        if (msg.conversation) return 'text';
        if (msg.extendedTextMessage) return 'text';
        if (msg.imageMessage) return msg.imageMessage.viewOnce ? 'view-once image' : 'image';
        if (msg.videoMessage) return msg.videoMessage.viewOnce ? 'view-once video' : 'video';
        if (msg.audioMessage) return msg.audioMessage.viewOnce ? 'view-once audio' : 'audio';
        if (msg.documentMessage) return 'document';
        if (msg.contactMessage) return 'contact';
        if (msg.locationMessage) return 'location';
        if (msg.stickerMessage) return 'sticker';
        
        return 'other';
    }

    async extractViewOnceMedia(message) {
        try {
            // Handle different message structure formats
            const msg = message.message || message;
            if (!msg) return null;

            let mediaMessage = null;
            let mediaType = null;

            if (msg.imageMessage?.viewOnce) {
                mediaMessage = msg.imageMessage;
                mediaType = 'imageMessage';
            } else if (msg.videoMessage?.viewOnce) {
                mediaMessage = msg.videoMessage;
                mediaType = 'videoMessage';
            } else if (msg.audioMessage?.viewOnce) {
                mediaMessage = msg.audioMessage;
                mediaType = 'audioMessage';
            }

            if (!mediaMessage) return null;

            // Create proper message structure for downloading (following Baileys documentation)
            const messageForDownload = {
                key: message.key || {
                    id: `temp_${Date.now()}`,
                    remoteJid: 'temp@temp.com',
                    fromMe: false
                },
                message: {
                    [mediaType]: {
                        ...mediaMessage,
                        viewOnce: false // Remove view-once restriction for download
                    }
                }
            };

            // Download the media using Baileys
            if (this.bot.sock) {
                console.log(`📥 Downloading ${mediaType} media...`);
                console.log('📋 Message structure for download:', JSON.stringify(messageForDownload, null, 2));
                
                const buffer = await downloadMediaMessage(
                    messageForDownload,
                    'buffer',
                    {},
                    {
                        logger: console,
                        reuploadRequest: this.bot.sock.updateMediaMessage
                    }
                );
                
                console.log(`✅ Downloaded ${buffer.length} bytes of ${mediaType} data`);
                
                return {
                    buffer,
                    mediaType: mediaType.replace('Message', ''), // Remove 'Message' suffix
                    mimetype: mediaMessage.mimetype,
                    caption: mediaMessage.caption || ''
                };
            }

            return null;
        } catch (error) {
            console.error('❌ Error extracting view-once media:', error);
            console.error('❌ Full error:', error.stack);
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

            const timestamp = contextData.timestamp || new Date().toLocaleString();
            const fromChat = contextData.chatType || (contextData.from.includes('@g.us') ? 'Group' : 'Private');
            const chatName = contextData.from;

            let savedContent = `📥 *SAVED MESSAGE*\n` +
                             `⏰ Time: ${timestamp}\n` +
                             `📍 From: ${fromChat} (${chatName})\n` +
                             `👤 Sender: ${contextData.sender}\n\n`;

            // Handle different message structure formats
            const msg = originalMessage.message || originalMessage;
            
            console.log('💾 Processing message type for save...');

            // Handle different message types
            if (this.isViewOnceMessage(originalMessage)) {
                console.log('🔓 Saving view-once message...');
                const mediaData = await this.extractViewOnceMedia(originalMessage);
                if (mediaData) {
                    await this.sendMediaWithoutViewOnce(this.ownerJid, mediaData);
                    savedContent += `🔓 View-once media saved above`;
                } else {
                    savedContent += `❌ Could not extract view-once media`;
                }
            } else if (msg.conversation) {
                console.log('💬 Saving text message...');
                savedContent += `💬 Text: ${msg.conversation}`;
            } else if (msg.extendedTextMessage?.text) {
                console.log('💬 Saving extended text message...');
                savedContent += `💬 Text: ${msg.extendedTextMessage.text}`;
            } else if (msg.imageMessage) {
                console.log('🖼️ Saving image message...');
                try {
                    // Create proper message structure for download
                    const messageForDownload = {
                        key: originalMessage.key || {
                            id: `temp_${Date.now()}`,
                            remoteJid: 'temp@temp.com',
                            fromMe: false
                        },
                        message: { imageMessage: msg.imageMessage }
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
                        await this.bot.sock.sendMessage(this.ownerJid, {
                            image: buffer,
                            caption: msg.imageMessage.caption || 'Saved image'
                        });
                        savedContent += `🖼️ Image saved above`;
                    } else {
                        savedContent += `🖼️ Image message (download failed)`;
                    }
                } catch (error) {
                    console.error('Error downloading image:', error);
                    savedContent += `🖼️ Image message (with caption: ${msg.imageMessage.caption || 'none'})`;
                }
            } else if (msg.videoMessage) {
                console.log('🎥 Saving video message...');
                try {
                    const messageForDownload = {
                        key: originalMessage.key || {
                            id: `temp_${Date.now()}`,
                            remoteJid: 'temp@temp.com',
                            fromMe: false
                        },
                        message: { videoMessage: msg.videoMessage }
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
                        await this.bot.sock.sendMessage(this.ownerJid, {
                            video: buffer,
                            caption: msg.videoMessage.caption || 'Saved video'
                        });
                        savedContent += `🎥 Video saved above`;
                    } else {
                        savedContent += `🎥 Video message (download failed)`;
                    }
                } catch (error) {
                    console.error('Error downloading video:', error);
                    savedContent += `🎥 Video message (with caption: ${msg.videoMessage.caption || 'none'})`;
                }
            } else if (msg.audioMessage) {
                console.log('🎵 Saving audio message...');
                try {
                    const messageForDownload = {
                        key: originalMessage.key || {
                            id: `temp_${Date.now()}`,
                            remoteJid: 'temp@temp.com',
                            fromMe: false
                        },
                        message: { audioMessage: msg.audioMessage }
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
                        await this.bot.sock.sendMessage(this.ownerJid, {
                            audio: buffer,
                            mimetype: msg.audioMessage.mimetype || 'audio/ogg; codecs=opus'
                        });
                        savedContent += `🎵 Audio saved above`;
                    } else {
                        savedContent += `🎵 Audio message (download failed)`;
                    }
                } catch (error) {
                    console.error('Error downloading audio:', error);
                    savedContent += `🎵 Voice/Audio message`;
                }
            } else {
                const messageType = this.getMessageType(msg);
                savedContent += `📄 ${messageType} message`;
                console.log(`📄 Unsupported message type for full save: ${messageType}`);
            }

            // Send the summary message
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