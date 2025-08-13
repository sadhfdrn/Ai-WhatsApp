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

    // Enhanced Button Messages using interactiveMessage format
    async sendInteractiveButtons(jid, options) {
        try {
            const {
                text,
                footer = 'WhatsApp Bot',
                buttons = [],
                headerType = 'text',
                header = null
            } = options;

            // Format buttons for WhatsApp Business API
            const formattedButtons = buttons.map((btn, index) => ({
                name: "quick_reply",
                buttonParamsJson: JSON.stringify({
                    display_text: btn.text || btn.displayText || `Button ${index + 1}`,
                    id: btn.id || this.generateId('btn')
                })
            }));

            const interactiveMessage = {
                interactiveMessage: {
                    body: { text: text },
                    footer: { text: footer },
                    nativeFlowMessage: {
                        buttons: formattedButtons,
                        messageParamsJson: JSON.stringify({
                            from: "bot",
                            timestamp: Date.now()
                        })
                    }
                }
            };

            // Fallback to standard buttons if interactive fails
            const fallbackMessage = {
                text: text,
                footer: footer,
                buttons: buttons.map((btn, index) => ({
                    buttonId: btn.id || this.generateId('btn'),
                    buttonText: { displayText: btn.text || btn.displayText || `Button ${index + 1}` },
                    type: 1
                })),
                headerType: 1
            };

            try {
                console.log('🔄 Attempting to send interactive button message...');
                return await this.sock.sendMessage(jid, interactiveMessage);
            } catch (interactiveError) {
                console.log('⚠️ Interactive message failed, using fallback buttons');
                return await this.sock.sendMessage(jid, fallbackMessage);
            }

        } catch (error) {
            console.error('❌ Error sending interactive buttons:', error);
            // Final fallback to plain text
            return await this.sock.sendMessage(jid, { 
                text: `${options.text}\n\n${options.buttons.map((btn, i) => `${i + 1}. ${btn.text || btn.displayText}`).join('\n')}`
            });
        }
    }

    // Enhanced List Messages using native flow
    async sendInteractiveList(jid, options) {
        try {
            const {
                text,
                footer = 'WhatsApp Bot',
                buttonText = 'View Options',
                sections = [],
                title = 'Select Option'
            } = options;

            // Format sections for WhatsApp Business API
            const formattedSections = sections.map(section => ({
                title: section.title,
                rows: section.rows.map(row => ({
                    header: row.title,
                    title: row.title,
                    description: row.description || '',
                    id: row.id || this.generateId('row')
                }))
            }));

            const interactiveMessage = {
                interactiveMessage: {
                    body: { text: text },
                    footer: { text: footer },
                    nativeFlowMessage: {
                        buttons: [{
                            name: "single_select",
                            buttonParamsJson: JSON.stringify({
                                title: title,
                                sections: formattedSections
                            })
                        }],
                        messageParamsJson: JSON.stringify({
                            from: "bot",
                            timestamp: Date.now()
                        })
                    }
                }
            };

            // Fallback to standard list format
            const fallbackMessage = {
                text: text,
                footer: footer,
                title: title,
                buttonText: buttonText,
                sections: formattedSections.map(section => ({
                    title: section.title,
                    rows: section.rows.map(row => ({
                        title: row.title,
                        description: row.description,
                        rowId: row.id
                    }))
                }))
            };

            try {
                console.log('🔄 Attempting to send interactive list message...');
                return await this.sock.sendMessage(jid, interactiveMessage);
            } catch (interactiveError) {
                console.log('⚠️ Interactive list failed, using fallback list');
                try {
                    return await this.sock.sendMessage(jid, fallbackMessage);
                } catch (fallbackError) {
                    console.log('⚠️ List fallback failed, using text menu');
                    // Final fallback to text menu
                    let textMenu = `📋 *${title}*\n\n${text}\n\n`;
                    sections.forEach((section, sIndex) => {
                        textMenu += `*${section.title}*\n`;
                        section.rows.forEach((row, rIndex) => {
                            textMenu += `${sIndex + 1}.${rIndex + 1} ${row.title}`;
                            if (row.description) textMenu += ` - ${row.description}`;
                            textMenu += '\n';
                        });
                        textMenu += '\n';
                    });
                    return await this.sock.sendMessage(jid, { text: textMenu });
                }
            }

        } catch (error) {
            console.error('❌ Error sending interactive list:', error);
            return false;
        }
    }

    // Quick Reply Buttons (Modern approach)
    async sendQuickReplies(jid, options) {
        try {
            const {
                text,
                footer = 'WhatsApp Bot',
                replies = []
            } = options;

            const quickReplyButtons = replies.map(reply => ({
                name: "quick_reply",
                buttonParamsJson: JSON.stringify({
                    display_text: reply.text,
                    id: reply.id || this.generateId('qr')
                })
            }));

            const interactiveMessage = {
                interactiveMessage: {
                    body: { text: text },
                    footer: { text: footer },
                    nativeFlowMessage: {
                        buttons: quickReplyButtons,
                        messageParamsJson: JSON.stringify({
                            type: "quick_reply",
                            timestamp: Date.now()
                        })
                    }
                }
            };

            try {
                console.log('🔄 Attempting to send quick replies...');
                return await this.sock.sendMessage(jid, interactiveMessage);
            } catch (interactiveError) {
                console.log('⚠️ Quick replies failed, using standard buttons');
                return await this.sendInteractiveButtons(jid, {
                    text,
                    footer,
                    buttons: replies
                });
            }

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

    // Copy Code Button
    async sendCopyCodeButton(jid, options) {
        try {
            const {
                text,
                code,
                footer = 'WhatsApp Bot'
            } = options;

            const copyMessage = {
                interactiveMessage: {
                    body: { text: text },
                    footer: { text: footer },
                    nativeFlowMessage: {
                        buttons: [{
                            name: "copy_code",
                            buttonParamsJson: JSON.stringify({
                                copy_code: code
                            })
                        }],
                        messageParamsJson: JSON.stringify({
                            type: "copy",
                            timestamp: Date.now()
                        })
                    }
                }
            };

            try {
                console.log('🔄 Attempting to send copy code button...');
                return await this.sock.sendMessage(jid, copyMessage);
            } catch (copyError) {
                console.log('⚠️ Copy button failed, sending code as text');
                return await this.sock.sendMessage(jid, {
                    text: `${text}\n\n\`\`\`\n${code}\n\`\`\``
                });
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
}

module.exports = InteractiveUtils;