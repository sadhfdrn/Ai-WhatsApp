// Enhanced Interactive Message Utilities for WhatsApp Bot
// Based on WhatsApp Business API standards and Baileys compatibility

class InteractiveUtils {
    constructor(sock) {
        this.sock = sock;
    }

    // Generate message ID for tracking
    generateId(prefix = 'msg') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    // Validate and format JID
    validateJid(jid) {
        try {
            if (!jid || typeof jid !== 'string') {
                return null;
            }

            // If it already includes @, assume it's properly formatted
            if (jid.includes('@')) {
                return jid;
            }

            // Format based on whether it looks like a group or individual
            if (jid.includes('-')) {
                return `${jid}@g.us`;
            } else {
                return `${jid}@s.whatsapp.net`;
            }
        } catch (error) {
            console.error('❌ JID validation error:', error);
            return null;
        }
    }

    // Enhanced Button Messages using @neoxr/baileys format
    async sendInteractiveButtons(jid, options) {
        try {
            const {
                text,
                footer = 'WhatsApp Bot',
                buttons = [],
                headerType = 1,
                header = null
            } = options;

            // Validate and format JID
            const validJid = this.validateJid(jid);
            if (!validJid) {
                console.log('❌ Invalid JID, using text fallback');
                return await this.sock.sendMessage(jid, { 
                    text: `${text}\n\n${buttons.map((btn, i) => `${i + 1}. ${btn.text || btn.displayText}`).join('\n')}`
                });
            }

            // Use @neoxr/baileys button format from docs
            const buttonMessage = {
                text: text,
                footer: footer,
                buttons: buttons.map((btn, index) => ({
                    buttonId: btn.id || this.generateId('btn'),
                    buttonText: {
                        displayText: btn.text || btn.displayText || `Button ${index + 1}`
                    },
                    type: 1
                })),
                headerType: headerType,
                viewOnce: false
            };

            try {
                console.log('🔄 Sending @neoxr/baileys button message...');
                return await this.sock.sendMessage(validJid, buttonMessage, { quoted: null });
            } catch (buttonError) {
                console.log('⚠️ Buttons failed, using text menu fallback');
                const textMenu = `${text}\n\n📋 Options:\n${buttons.map((btn, i) => `${i + 1}. ${btn.text || btn.displayText}`).join('\n')}\n\nReply with the number of your choice.`;
                return await this.sock.sendMessage(validJid, { text: textMenu });
            }

        } catch (error) {
            console.error('❌ Error sending interactive buttons:', error);
            return false;
        }
    }

    // Enhanced List Messages using @neoxr/baileys native flow format
    async sendInteractiveList(jid, options) {
        try {
            const {
                text,
                footer = 'WhatsApp Bot',
                buttonText = 'View Options',
                sections = [],
                title = 'Select Option'
            } = options;

            // Validate JID first
            const validJid = this.validateJid(jid);
            if (!validJid) {
                console.log('❌ Invalid JID for list message');
                return false;
            }

            try {
                // Use @neoxr/baileys native flow button format from docs
                const flowMessage = {
                    text: text,
                    footer: footer,
                    buttons: [
                        {
                            buttonId: '.menu',
                            buttonText: {
                                displayText: 'MENU'
                            },
                            type: 1,
                        },
                        {
                            buttonId: 'flow_list',
                            buttonText: {
                                displayText: buttonText
                            },
                            type: 4,
                            nativeFlowInfo: {
                                name: 'single_select',
                                paramsJson: JSON.stringify({
                                    title: title,
                                    sections: sections.map(section => ({
                                        title: section.title,
                                        highlight_label: '📋',
                                        rows: section.rows.map(row => ({
                                            header: row.title,
                                            title: row.title,
                                            description: row.description || '',
                                            id: row.id || this.generateId('row'),
                                        }))
                                    }))
                                }),
                            },
                        },
                    ],
                    headerType: 1,
                    viewOnce: false
                };

                console.log('🔄 Sending @neoxr/baileys flow list...');
                return await this.sock.sendMessage(validJid, flowMessage, { quoted: null });

            } catch (flowError) {
                console.log('⚠️ Flow list failed, using text menu fallback');
                let textMenu = `📋 *${title}*\n\n${text}\n\n`;
                
                let optionNumber = 1;
                sections.forEach((section) => {
                    textMenu += `*${section.title}*\n`;
                    section.rows.forEach((row) => {
                        textMenu += `${optionNumber}. ${row.title}`;
                        if (row.description) textMenu += ` - ${row.description}`;
                        textMenu += '\n';
                        optionNumber++;
                    });
                    textMenu += '\n';
                });
                
                textMenu += '💡 Reply with the number of your choice.';
                
                return await this.sock.sendMessage(validJid, { text: textMenu });
            }

        } catch (error) {
            console.error('❌ Error sending interactive list:', error);
            return false;
        }
    }

    // Quick Reply Buttons with validation
    async sendQuickReplies(jid, options) {
        try {
            const {
                text,
                footer = 'WhatsApp Bot',
                replies = []
            } = options;

            // Validate JID
            const validJid = this.validateJid(jid);
            if (!validJid) {
                return false;
            }

            // Use standard button approach for better compatibility
            console.log('🔄 Sending quick replies as standard buttons');
            return await this.sendInteractiveButtons(validJid, {
                text,
                footer,
                buttons: replies.map(reply => ({
                    id: reply.id || this.generateId('qr'),
                    text: reply.text
                }))
            });

        } catch (error) {
            console.error('❌ Error sending quick replies:', error);
            return false;
        }
    }

    // Flow Messages (Call-to-action style)
    async sendFlowMessage(jid, options) {
        try {
            const {
                text,
                footer = 'WhatsApp Bot',
                flowId,
                flowCta = 'Click Here',
                flowToken,
                flowData = {}
            } = options;

            const flowMessage = {
                interactiveMessage: {
                    body: { text: text },
                    footer: { text: footer },
                    nativeFlowMessage: {
                        buttons: [{
                            name: "flow",
                            buttonParamsJson: JSON.stringify({
                                flow_id: flowId,
                                flow_cta: flowCta,
                                flow_token: flowToken,
                                flow_message_version: "3",
                                ...flowData
                            })
                        }],
                        messageParamsJson: JSON.stringify({
                            type: "flow",
                            timestamp: Date.now()
                        })
                    }
                }
            };

            try {
                console.log('🔄 Attempting to send flow message...');
                return await this.sock.sendMessage(jid, flowMessage);
            } catch (flowError) {
                console.log('⚠️ Flow message failed, using button fallback');
                return await this.sendInteractiveButtons(jid, {
                    text: `${text}\n\n💡 ${flowCta}`,
                    footer,
                    buttons: [{ id: 'flow_fallback', text: flowCta }]
                });
            }

        } catch (error) {
            console.error('❌ Error sending flow message:', error);
            return false;
        }
    }

    // Payment Button (Business feature)
    async sendPaymentButton(jid, options) {
        try {
            const {
                text,
                footer = 'WhatsApp Bot',
                currency = 'USD',
                amount,
                reference_id,
                type = 'physical-goods'
            } = options;

            const paymentMessage = {
                interactiveMessage: {
                    body: { text: text },
                    footer: { text: footer },
                    nativeFlowMessage: {
                        buttons: [{
                            name: "review_and_pay",
                            buttonParamsJson: JSON.stringify({
                                currency: currency,
                                total_amount: {
                                    value: amount.toString(),
                                    offset: 100
                                },
                                reference_id: reference_id || this.generateId('pay'),
                                type: type,
                                payment_method: "confirm"
                            })
                        }],
                        messageParamsJson: JSON.stringify({
                            type: "payment",
                            timestamp: Date.now()
                        })
                    }
                }
            };

            try {
                console.log('🔄 Attempting to send payment button...');
                return await this.sock.sendMessage(jid, paymentMessage);
            } catch (paymentError) {
                console.log('⚠️ Payment button failed, using info message');
                return await this.sock.sendMessage(jid, {
                    text: `${text}\n\n💳 Payment Amount: ${currency} ${amount}\nReference: ${reference_id}`
                });
            }

        } catch (error) {
            console.error('❌ Error sending payment button:', error);
            return false;
        }
    }

    // Copy Code Button using @neoxr/baileys native flow format
    async sendCopyCodeButton(jid, options) {
        try {
            const {
                text,
                code,
                footer = 'WhatsApp Bot'
            } = options;

            // Validate JID
            const validJid = this.validateJid(jid);
            if (!validJid) {
                return false;
            }

            try {
                // Use @neoxr/baileys native flow copy button format
                const copyMessage = {
                    text: text,
                    footer: footer,
                    buttons: [
                        {
                            buttonId: 'copy_code',
                            buttonText: {
                                displayText: 'Copy Code'
                            },
                            type: 4,
                            nativeFlowInfo: {
                                name: 'cta_copy',
                                paramsJson: JSON.stringify({
                                    display_text: 'Copy Code',
                                    id: 'copy_action',
                                    copy_code: code
                                })
                            }
                        }
                    ],
                    headerType: 1,
                    viewOnce: false
                };

                console.log('📋 Sending @neoxr/baileys copy code button...');
                return await this.sock.sendMessage(validJid, copyMessage, { quoted: null });

            } catch (copyError) {
                console.log('⚠️ Copy button failed, using formatted text');
                const codeMessage = `${text}\n\n\`\`\`${code}\`\`\`\n\n${footer}`;
                return await this.sock.sendMessage(validJid, { text: codeMessage });
            }

        } catch (error) {
            console.error('❌ Error sending copy code button:', error);
            return false;
        }
    }

    // Handle Interactive Response
    parseInteractiveResponse(message) {
        try {
            // Handle different response types
            if (message.message?.interactiveResponseMessage) {
                const response = message.message.interactiveResponseMessage;
                
                if (response.nativeFlowResponseMessage) {
                    return {
                        type: 'native_flow',
                        id: response.nativeFlowResponseMessage.paramsJson ? 
                            JSON.parse(response.nativeFlowResponseMessage.paramsJson).id : null,
                        data: response.nativeFlowResponseMessage
                    };
                }

                return {
                    type: 'interactive',
                    data: response
                };
            }

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
                return {
                    type: 'list',
                    id: message.message.listResponseMessage.singleSelectReply.selectedRowId,
                    text: message.message.listResponseMessage.title
                };
            }

            return null;
        } catch (error) {
            console.error('❌ Error parsing interactive response:', error);
            return null;
        }
    }

    // Parse interactive response from message
    parseInteractiveResponse(message) {
        try {
            if (!message || !message.message) {
                return null;
            }

            const msg = message.message;

            // Check for button response
            if (msg.buttonsResponseMessage) {
                return {
                    type: 'button',
                    id: msg.buttonsResponseMessage.selectedButtonId,
                    text: msg.buttonsResponseMessage.selectedDisplayText || 'Button Selected'
                };
            }

            // Check for list response
            if (msg.listResponseMessage) {
                const response = msg.listResponseMessage;
                return {
                    type: 'list',
                    id: response.singleSelectReply?.selectedRowId || response.title,
                    text: response.title || response.singleSelectReply?.selectedRowId || 'List Item Selected'
                };
            }

            // Check for template button response
            if (msg.templateButtonReplyMessage) {
                return {
                    type: 'template_button',
                    id: msg.templateButtonReplyMessage.selectedId,
                    text: msg.templateButtonReplyMessage.selectedDisplayText || 'Template Button'
                };
            }

            // Check for quick reply
            if (msg.extendedTextMessage?.contextInfo?.quotedMessage?.buttonsMessage) {
                return {
                    type: 'quick_reply',
                    id: 'quick_reply',
                    text: msg.extendedTextMessage.text || 'Quick Reply'
                };
            }

            return null;
        } catch (error) {
            console.error('❌ Error parsing interactive response:', error);
            return null;
        }
    }
}

module.exports = InteractiveUtils;