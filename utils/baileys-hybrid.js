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

// === INTERACTIVE COMPONENTS ===
// Use baileys-x specifically for interactive message creation
const createInteractiveMessage = (jid, options) => {
    try {
        // Use baileys-x native interactive capabilities
        return BaileysX.generateMessageFromContent(jid, {
            viewOnceMessage: {
                message: {
                    messageContextInfo: {
                        deviceListMetadata: {},
                        deviceListMetadataVersion: 2
                    },
                    interactiveMessage: options
                }
            }
        }, { quoted: options.quoted });
    } catch (error) {
        console.error('❌ Interactive message creation failed:', error);
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
    
    // Add enhanced button support
    socket.sendButtonMessage = async (jid, buttons, text, footer, options = {}) => {
        try {
            // Use baileys-x format for buttons
            const buttonMessage = {
                text: text,
                footer: footer,
                buttons: buttons.map((btn, index) => ({
                    buttonId: btn.id || `btn_${index}`,
                    buttonText: {
                        displayText: btn.text || btn.displayText || `Button ${index + 1}`
                    },
                    type: 1
                })),
                headerType: 1,
                viewOnce: false
            };
            
            return await socket.sendMessage(jid, buttonMessage, options);
        } catch (error) {
            console.error('❌ Button message failed, using fallback:', error);
            // Fallback to text menu
            const textMenu = `${text}\n\n📋 Options:\n${buttons.map((btn, i) => `${i + 1}. ${btn.text || btn.displayText}`).join('\n')}`;
            return await socket.sendMessage(jid, { text: textMenu }, options);
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
    createInteractiveMessage,
    
    // Access to individual libraries if needed
    libraries: {
        whiskeySockets: require('@whiskeysockets/baileys'),
        baileysX: require('baileys-x'),
        adiwajshing: require('@adiwajshing/baileys')
    }
};