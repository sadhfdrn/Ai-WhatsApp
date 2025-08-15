// Hybrid Baileys approach - using each library for its strengths
// This module provides the best functions from each Baileys variant

// === CORE CONNECTION & MESSAGE HANDLING ===
// Use @whiskeysockets/baileys for stable connection and decryption
const { 
    makeWASocket, 
    DisconnectReason, 
    useMultiFileAuthState, 
    fetchLatestBaileysVersion 
} = require('@whiskeysockets/baileys');

// === INTERACTIVE FEATURES ===
// Use baileys-x for advanced interactive capabilities
const BaileysX = require('baileys-x');

// === MEDIA HANDLING ===
// Try multiple libraries for media operations with fallbacks
let downloadMediaMessage, getContentType;

try {
    // Prefer @whiskeysockets/baileys for stable media downloads
    const whiskeySockets = require('@whiskeysockets/baileys');
    downloadMediaMessage = whiskeySockets.downloadMediaMessage;
    getContentType = whiskeySockets.getContentType;
} catch (error) {
    console.log('📦 Falling back to baileys-x for media operations');
    const baileysX = require('baileys-x');
    downloadMediaMessage = baileysX.downloadMediaMessage;
    getContentType = baileysX.getContentType;
}

// === INTERACTIVE COMPONENTS - 2024 WORKING FORMAT ===
// Use the latest WhatsApp interactive message format that actually works
const { generateWAMessageFromContent, proto } = require('@whiskeysockets/baileys');

const createModernInteractiveMessage = (jid, options) => {
    try {
        // Use the 2024 working format with nativeFlow
        return generateWAMessageFromContent(jid, {
            viewOnceMessage: {
                message: {
                    messageContextInfo: {
                        deviceListMetadata: {},
                        deviceListMetadataVersion: 2
                    },
                    interactiveMessage: proto.Message.InteractiveMessage.create({
                        body: proto.Message.InteractiveMessage.Body.create({
                            text: options.text
                        }),
                        footer: proto.Message.InteractiveMessage.Footer.create({
                            text: options.footer || "WhatsApp Bot"
                        }),
                        nativeFlowMessage: proto.Message.InteractiveMessage.NativeFlowMessage.create({
                            buttons: options.buttons.map(btn => ({
                                name: "single_select",
                                buttonParamsJson: JSON.stringify({
                                    title: btn.text,
                                    sections: [{
                                        title: "Options",
                                        rows: [{
                                            title: btn.text,
                                            description: btn.description || btn.text,
                                            id: btn.id
                                        }]
                                    }]
                                })
                            }))
                        })
                    })
                }
            }
        }, {});
    } catch (error) {
        console.error('❌ Modern interactive message creation failed:', error);
        return null;
    }
};

// === HYBRID SOCKET FACTORY ===
const createHybridSocket = (options = {}) => {
    // Use @whiskeysockets/baileys for the main socket (stable decryption)
    const socket = makeWASocket(options);
    
    // Enhance socket with baileys-x interactive capabilities
    socket.sendInteractiveMessage = async (jid, message, options = {}) => {
        try {
            // Try baileys-x interactive first
            const interactiveMsg = createInteractiveMessage(jid, message);
            if (interactiveMsg) {
                return await socket.relayMessage(jid, interactiveMsg.message, {});
            }
            
            // Fallback to standard message
            return await socket.sendMessage(jid, message, options);
        } catch (error) {
            console.error('❌ Hybrid interactive message failed:', error);
            return await socket.sendMessage(jid, message, options);
        }
    };
    
    // Add enhanced button support using 2024 working format
    socket.sendButtonMessage = async (jid, buttons, text, footer, options = {}) => {
        try {
            console.log('🎯 Sending 2024 format interactive buttons...');
            
            // Method 1: Try modern native flow format
            const modernMessage = generateWAMessageFromContent(jid, {
                viewOnceMessage: {
                    message: {
                        messageContextInfo: {
                            deviceListMetadata: {},
                            deviceListMetadataVersion: 2
                        },
                        interactiveMessage: proto.Message.InteractiveMessage.create({
                            body: proto.Message.InteractiveMessage.Body.create({
                                text: text
                            }),
                            footer: proto.Message.InteractiveMessage.Footer.create({
                                text: footer || "WhatsApp Bot"
                            }),
                            nativeFlowMessage: proto.Message.InteractiveMessage.NativeFlowMessage.create({
                                buttons: [{
                                    name: "single_select",
                                    buttonParamsJson: JSON.stringify({
                                        title: "Select Option",
                                        sections: [{
                                            title: "Available Actions",
                                            rows: buttons.map(btn => ({
                                                title: btn.text || btn.displayText,
                                                description: btn.description || btn.text,
                                                id: btn.id || `btn_${Math.random().toString(36).substr(2, 9)}`
                                            }))
                                        }]
                                    })
                                }]
                            })
                        })
                    }
                }
            }, {});
            
            const result = await socket.relayMessage(jid, modernMessage.message, {});
            console.log('✅ Modern interactive message sent successfully');
            return result;
            
        } catch (error) {
            console.error('❌ Modern button failed, using simple format:', error);
            
            try {
                // Method 2: Try simple button format (may work on some clients)
                const simpleButtonMessage = {
                    text: text,
                    footer: footer || "WhatsApp Bot",
                    buttons: buttons.map((btn, index) => ({
                        buttonId: btn.id || `btn_${index}`,
                        buttonText: {
                            displayText: btn.text || btn.displayText || `Button ${index + 1}`
                        },
                        type: 1
                    })),
                    headerType: 1
                };
                
                const result = await socket.sendMessage(jid, simpleButtonMessage, options);
                console.log('✅ Simple button format sent');
                return result;
                
            } catch (fallbackError) {
                console.error('❌ All button formats failed, using text menu:', fallbackError);
                // Final fallback to text menu
                const textMenu = `${text}\n\n📋 Options:\n${buttons.map((btn, i) => `${i + 1}. ${btn.text || btn.displayText}`).join('\n')}\n\nReply with the number or text of your choice.`;
                return await socket.sendMessage(jid, { text: textMenu }, options);
            }
        }
    };
    
    return socket;
};

// === EXPORTS ===
module.exports = {
    // Core connection (stable)
    makeWASocket: createHybridSocket,
    DisconnectReason,
    useMultiFileAuthState,
    fetchLatestBaileysVersion,
    
    // Media handling (with fallbacks)
    downloadMediaMessage,
    getContentType,
    
    // Interactive features (enhanced)
    createModernInteractiveMessage,
    
    // Access to individual libraries if needed
    libraries: {
        whiskeySockets: require('@whiskeysockets/baileys'),
        baileysX: require('baileys-x'),
        adiwajshing: require('@adiwajshing/baileys')
    }
};