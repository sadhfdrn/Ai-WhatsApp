const InteractiveUtils = require('./interactiveUtils');

class MessageUtils {
    constructor(sock) {
        this.sock = sock;
        this.interactiveUtils = new InteractiveUtils(sock);
    }

    // Enhanced button message with interactive support
    async sendButtonMessage(jid, text, buttons, options = {}) {
        try {
            console.log('🎯 Sending enhanced button message...');
            
            // Try interactive buttons first
            const result = await this.interactiveUtils.sendInteractiveButtons(jid, {
                text: text,
                footer: options.footer || 'WhatsApp Bot',
                buttons: buttons,
                headerType: options.headerType || 'text',
                header: options.header
            });

            if (result) {
                console.log('✅ Interactive buttons sent successfully');
                return result;
            }

            // Fallback to standard buttons
            console.log('🔄 Using standard button fallback...');
            const buttonMessage = {
                text: text,
                footer: options.footer || 'WhatsApp Bot',
                buttons: buttons.map((btn, index) => ({
                    buttonId: btn.id || `btn_${index}`,
                    buttonText: { displayText: btn.text },
                    type: 1
                })),
                headerType: 1
            };

            if (options.image) {
                buttonMessage.image = { url: options.image };
                buttonMessage.caption = text;
                buttonMessage.headerType = 4;
                delete buttonMessage.text;
            }

            return await this.sock.sendMessage(jid, buttonMessage);
        } catch (error) {
            console.error('❌ Error sending button message:', error);
            return false;
        }
    }

    // Enhanced list message with interactive support
    async sendListMessage(jid, title, description, sections, buttonText = "Select Option") {
        try {
            console.log('🎯 Sending enhanced list message...');
            
            // Try interactive list first
            const result = await this.interactiveUtils.sendInteractiveList(jid, {
                text: description,
                footer: "WhatsApp Bot",
                title: title,
                buttonText: buttonText,
                sections: sections
            });

            if (result) {
                console.log('✅ Interactive list sent successfully');
                return result;
            }

            // Fallback to standard list
            console.log('🔄 Using standard list fallback...');
            const listMessage = {
                text: description,
                footer: "WhatsApp Bot",
                title: title,
                buttonText: buttonText,
                sections: sections.map(section => ({
                    title: section.title,
                    rows: section.rows.map(row => ({
                        title: row.title,
                        description: row.description || '',
                        rowId: row.id
                    }))
                }))
            };

            try {
                return await this.sock.sendMessage(jid, listMessage);
            } catch (listError) {
                console.log('📱 List format not supported, using text menu');
                console.error('List error:', listError.message);
                return await this.sock.sendMessage(jid, { 
                    text: `📋 *${title}*\n\n${description}\n\n${sections.map(section => `*${section.title}*\n${section.rows.map(row => `• ${row.title}: ${row.description || ''}`).join('\n')}`).join('\n\n')}\n\n💡 Reply with the option name to select` 
                });
            }
        } catch (error) {
            console.error('❌ Error sending list message:', error);
            return false;
        }
    }

    // Send poll message
    async sendPoll(jid, question, options, multiSelect = false) {
        try {
            const pollMessage = {
                poll: {
                    name: question,
                    options: options,
                    selectableCount: multiSelect ? options.length : 1
                }
            };

            return await this.sock.sendMessage(jid, pollMessage);
        } catch (error) {
            console.error('❌ Error sending poll:', error);
            return false;
        }
    }

    // Enhanced quick reply message with interactive support
    async sendQuickReplyMessage(jid, text, quickReplies, options = {}) {
        try {
            console.log('🎯 Sending enhanced quick reply message...');
            
            // Try interactive quick replies first
            const result = await this.interactiveUtils.sendQuickReplies(jid, {
                text: text,
                footer: options.footer || 'WhatsApp Bot',
                replies: quickReplies
            });

            if (result) {
                console.log('✅ Interactive quick replies sent successfully');
                return result;
            }

            // Fallback to button format
            console.log('🔄 Using button fallback for quick replies...');
            const interactiveMessage = {
                text: text,
                footer: options.footer || 'WhatsApp Bot',
                buttons: quickReplies.map((reply, index) => ({
                    buttonId: reply.id || `quick_${index}`,
                    buttonText: { displayText: reply.text },
                    type: 1
                })),
                headerType: 1
            };

            return await this.sock.sendMessage(jid, interactiveMessage);
        } catch (error) {
            console.error('❌ Error sending quick reply message:', error);
            return false;
        }
    }

    // Send copy code button
    async sendCopyCodeMessage(jid, text, code, options = {}) {
        try {
            console.log('🎯 Sending copy code message...');
            
            const result = await this.interactiveUtils.sendCopyCodeButton(jid, {
                text: text,
                code: code,
                footer: options.footer || 'WhatsApp Bot'
            });

            return result;
        } catch (error) {
            console.error('❌ Error sending copy code message:', error);
            return false;
        }
    }

    // Send flow message
    async sendFlowMessage(jid, text, flowOptions = {}, options = {}) {
        try {
            console.log('🎯 Sending flow message...');
            
            const result = await this.interactiveUtils.sendFlowMessage(jid, {
                text: text,
                footer: options.footer || 'WhatsApp Bot',
                ...flowOptions
            });

            return result;
        } catch (error) {
            console.error('❌ Error sending flow message:', error);
            return false;
        }
    }

    // Parse interactive responses
    parseInteractiveResponse(message) {
        return this.interactiveUtils.parseInteractiveResponse(message);
    }

    // Send carousel-style message (using multiple list sections)
    async sendCarouselMessage(jid, title, cards) {
        try {
            const sections = cards.map((card, index) => ({
                title: card.title,
                rows: [{
                    title: card.subtitle || `Option ${index + 1}`,
                    description: card.description,
                    rowId: card.id || `card_${index}`
                }]
            }));

            return await this.sendListMessage(jid, title, "Browse through options below:", sections, "View Options");
        } catch (error) {
            console.error('❌ Error sending carousel message:', error);
            return false;
        }
    }

    // Send location message
    async sendLocation(jid, latitude, longitude, address = "") {
        try {
            const locationMessage = {
                location: {
                    degreesLatitude: latitude,
                    degreesLongitude: longitude,
                    name: address,
                    address: address
                }
            };

            return await this.sock.sendMessage(jid, locationMessage);
        } catch (error) {
            console.error('❌ Error sending location:', error);
            return false;
        }
    }

    // Send contact message
    async sendContact(jid, contacts) {
        try {
            const contactMessage = {
                contacts: {
                    displayName: contacts[0].name,
                    contacts: contacts.map(contact => ({
                        vcard: `BEGIN:VCARD\nVERSION:3.0\nFN:${contact.name}\nTEL;type=CELL;type=VOICE;waid=${contact.number}:${contact.number}\nEND:VCARD`
                    }))
                }
            };

            return await this.sock.sendMessage(jid, contactMessage);
        } catch (error) {
            console.error('❌ Error sending contact:', error);
            return false;
        }
    }

    // Send message with reactions
    async sendMessageWithReaction(jid, text, emoji) {
        try {
            const message = await this.sock.sendMessage(jid, { text: text });
            
            if (message && emoji) {
                setTimeout(async () => {
                    await this.sock.sendMessage(jid, {
                        react: {
                            text: emoji,
                            key: message.key
                        }
                    });
                }, 500);
            }

            return message;
        } catch (error) {
            console.error('❌ Error sending message with reaction:', error);
            return false;
        }
    }

    // Send typing indicator
    async sendTyping(jid, duration = 3000) {
        try {
            await this.sock.sendPresenceUpdate('composing', jid);
            setTimeout(async () => {
                await this.sock.sendPresenceUpdate('paused', jid);
            }, duration);
        } catch (error) {
            console.error('❌ Error sending typing indicator:', error);
        }
    }

    // Send media with caption and buttons
    async sendMediaWithButtons(jid, mediaUrl, mediaType, caption, buttons, options = {}) {
        try {
            const mediaMessage = {
                caption: caption,
                footer: options.footer || 'WhatsApp Bot',
                buttons: buttons.map((btn, index) => ({
                    buttonId: btn.id || `media_btn_${index}`,
                    buttonText: { displayText: btn.text },
                    type: 1
                })),
                headerType: 4
            };

            if (mediaType === 'image') {
                mediaMessage.image = { url: mediaUrl };
            } else if (mediaType === 'video') {
                mediaMessage.video = { url: mediaUrl };
            } else if (mediaType === 'document') {
                mediaMessage.document = { url: mediaUrl };
                mediaMessage.fileName = options.fileName || 'document';
            }

            return await this.sock.sendMessage(jid, mediaMessage);
        } catch (error) {
            console.error('❌ Error sending media with buttons:', error);
            return false;
        }
    }

    // Handle interactive message responses
    static parseInteractiveResponse(message) {
        try {
            // Handle button responses
            if (message.message?.buttonsResponseMessage) {
                return {
                    type: 'button',
                    id: message.message.buttonsResponseMessage.selectedButtonId,
                    text: message.message.buttonsResponseMessage.selectedDisplayText
                };
            }

            // Handle list responses
            if (message.message?.listResponseMessage) {
                const response = message.message.listResponseMessage.singleSelectReply;
                return {
                    type: 'list',
                    id: response.selectedRowId,
                    text: response.selectedDisplayText
                };
            }

            // Handle poll responses
            if (message.message?.pollUpdateMessage) {
                return {
                    type: 'poll',
                    pollCreationMessageKey: message.message.pollUpdateMessage.pollCreationMessageKey,
                    vote: message.message.pollUpdateMessage.vote
                };
            }

            return null;
        } catch (error) {
            console.error('❌ Error parsing interactive response:', error);
            return null;
        }
    }
}

module.exports = MessageUtils;