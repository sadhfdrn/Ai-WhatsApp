const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('baileys-x');
const { Boom } = require('@hapi/boom');
const pino = require('pino');

// Your provided credentials
const credentials = {
    "noiseKey": {
        "private": { "type": "Buffer", "data": "8G/9x1GUbZyul1oGedPy2cXK0mDKIzmjeMWXuKwTbFU=" },
        "public": { "type": "Buffer", "data": "8fS1JtxXSXHrYE87JAHwhwVav8abvgmkUip4DuFZDwg=" }
    },
    "pairingEphemeralKeyPair": {
        "private": { "type": "Buffer", "data": "IJaV/rjtoS44KUwcTGaW4b6n/QMLEZ27BZTvi7SIoVY=" },
        "public": { "type": "Buffer", "data": "9JoaPmB76CVVF5SQUGe9dt1kU/sgTHRUe6xA1z09BgY=" }
    },
    "signedIdentityKey": {
        "private": { "type": "Buffer", "data": "6ID/cQ9YynRGFkkcwk88Howo8rvuFquwGF8i0Uc2Z20=" },
        "public": { "type": "Buffer", "data": "HHOX2YAg4bxX4kcsUYXGEjCs5YLgs01si6Lt8YoFaj0=" }
    },
    "signedPreKey": {
        "keyPair": {
            "private": { "type": "Buffer", "data": "8HkwFNhNZaBoihH6Pcqb9WiFsxjElLbw3i1f7ZrFR08=" },
            "public": { "type": "Buffer", "data": "0Dc27hmh1ZuwyveuNx46qxsex2m0B1EDulklCFGn6B0=" }
        },
        "signature": { "type": "Buffer", "data": "TCo0Rg8tWqphwv6fUBpSS+maRHA+sts/RzkZuhlwJjoIk2UUZqmV9KDWBfrGIFKtzcSKISu2dw+7ZX1ywY7/Ag==" },
        "keyId": 1
    },
    "registrationId": 49,
    "advSecretKey": "QnLuYHz1woUku4bRGk2RSAkBWS6Ib1kKEY6NP7v8EIk=",
    "processedHistoryMessages": [],
    "nextPreKeyId": 31,
    "firstUnuploadedPreKeyId": 31,
    "accountSyncCounter": 0,
    "accountSettings": { "unarchiveChats": false },
    "deviceId": "eVC0iaMbRuqluK_xDTuAUQ",
    "phoneId": "9a3d2ee3-6d3c-409f-b82e-78d63c02820d",
    "identityId": { "type": "Buffer", "data": "KouU2LEP/ueWQMhDjJTW2QFdgmo=" },
    "registered": true,
    "backupToken": { "type": "Buffer", "data": "0NePzR2YJ7YH77L9JT44+qdCdDk=" },
    "registration": {},
    "pairingCode": "CYRILDEV",
    "me": { "id": "2349113085799:17@s.whatsapp.net", "lid": "237963149619307:17@lid" },
    "account": {
        "details": "CNvP0ckFEJbY98QGGAEgACgA",
        "accountSignatureKey": "lt1k5zqnMQGLjuNB594jM7tPA+4IowKP60FUcRjTqyM=",
        "accountSignature": "A1u06ufJ7UO670uLoA6IXfPPK8+WMpO0hVWNkWeOYD6vZPzHoHuZAJNFX8+KTgD/Jfrx3yj/X9RYPYQyOstoAA==",
        "deviceSignature": "1h5hKlhh/hgl+MLQJ709vezPl+XsL+wpm+Zv1FwyGdh1vQ8iMZBtE9WxsaJ4zX9dwhhg3o/K/hd9VSqkonYXCQ=="
    },
    "signalIdentities": [{
        "identifier": { "name": "2349113085799:17@s.whatsapp.net", "deviceId": 0 },
        "identifierKey": { "type": "Buffer", "data": "BZbdZOc6pzEBi47jQefeIzO7TwPuCKMCj+tBVHEY06sj" }
    }],
    "platform": "android",
    "routingInfo": { "type": "Buffer", "data": "CAgIEg==" },
    "lastAccountSyncTimestamp": 1755180064,
    "lastPropHash": "2P1Yhf",
    "preKeys": {
        "private": { "type": "Buffer", "data": "gOQntc+2989e5t+v6vByS8uzaC8aJuEvVTZfZOkh7Xo=" },
        "public": { "type": "Buffer", "data": "X9uz698vKawWS+ioX4nLAokYGnQlNF7LWIWcD9haAT0=" }
    },
    "senderKeys": {},
    "timestamp": "2025-08-14T14:01:09.724Z"
};

// Convert Buffer data back to actual Buffers
function convertBufferData(obj) {
    if (obj && typeof obj === 'object') {
        if (obj.type === 'Buffer' && obj.data) {
            return Buffer.from(obj.data, 'base64');
        }
        
        const converted = {};
        for (const key in obj) {
            converted[key] = convertBufferData(obj[key]);
        }
        return converted;
    }
    return obj;
}

async function sendQuickReplyButton(sock) {
    try {
        // Get your own number from credentials - handle different possible formats
        let targetNumber;
        
        if (credentials.me && credentials.me.id) {
            targetNumber = credentials.me.id;
        } else {
            // Fallback: construct from phone number if available
            targetNumber = "2349113085799@s.whatsapp.net"; // Your number from credentials
        }
        
        console.log('Sending message to:', targetNumber);
        
        // CTA Copy Button Message using templateMessage (baileys-mod compatible)
        const ctaMessage = {
            templateMessage: {
                hydratedTemplate: {
                    hydratedContentText: '🚀 *Special Offer!* Get 50% off our premium service!\n\n✨ Limited time only - Don\'t miss out!\n\nPromo Code: *SAVE50*',
                    hydratedFooterText: 'Valid until end of month | Terms apply',
                    hydratedButtons: [
                        {
                            urlButton: {
                                displayText: '🌐 Visit Website',
                                url: 'https://yourwebsite.com'
                            }
                        },
                        {
                            callButton: {
                                displayText: '📞 Call Us',
                                phoneNumber: '+1234567890'
                            }
                        },
                        {
                            quickReplyButton: {
                                displayText: '📋 Copy Code',
                                id: 'copy_promo_code'
                            }
                        }
                    ]
                }
            }
        };

        await sock.sendMessage(targetNumber, ctaMessage);
        console.log('CTA copy button message sent successfully!');
        
    } catch (error) {
        console.error('Error sending CTA copy button:', error);
        
        // Fallback to simple buttons if template message fails
        console.log('Trying fallback button message...');
        try {
            const targetNumber = credentials.me.id || "2349113085799@s.whatsapp.net";
            
            const fallbackMessage = {
                text: '🚀 *Special Offer!* Get 50% off our premium service!\n\n✨ Limited time only - Don\'t miss out!\n\nPromo Code: *SAVE50*\n\nClick button to copy:',
                footer: 'Valid until end of month | Terms apply',
                buttons: [
                    {
                        buttonId: 'copy_code',
                        buttonText: { displayText: '📋 Copy Code: SAVE50' },
                        type: 1
                    },
                    {
                        buttonId: 'visit_site',
                        buttonText: { displayText: '🌐 Visit Website' },
                        type: 1
                    },
                    {
                        buttonId: 'get_support',
                        buttonText: { displayText: '💬 Get Support' },
                        type: 1
                    }
                ],
                headerType: 1
            };
            
            await sock.sendMessage(targetNumber, fallbackMessage);
            console.log('Fallback button message sent successfully!');
        } catch (fallbackError) {
            console.error('Fallback also failed:', fallbackError);
        }
    }
}

async function startBot() {
    console.log('Starting WhatsApp Bot...');
    
    try {
        // Convert credentials to proper format
        const convertedCredentials = convertBufferData(credentials);
        
        // Create socket with existing credentials
        const sock = makeWASocket({
            logger: pino({ level: 'silent' }),
            printQRInTerminal: false,
            auth: {
                creds: convertedCredentials,
                keys: {
                    get: async (type, ids) => {
                        const data = {};
                        for (const id of ids) {
                            let value = convertedCredentials[type]?.[id];
                            if (value) {
                                if (typeof value === 'object' && value.data) {
                                    value = Buffer.from(value.data, 'base64');
                                }
                                data[id] = value;
                            }
                        }
                        return data;
                    },
                    set: async (data) => {
                        for (const category in data) {
                            for (const id in data[category]) {
                                const value = data[category][id];
                                if (!convertedCredentials[category]) {
                                    convertedCredentials[category] = {};
                                }
                                convertedCredentials[category][id] = value;
                            }
                        }
                    }
                }
            }
        });

        // Connection events
        sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect } = update;
            
            if (connection === 'close') {
                const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
                console.log('Connection closed due to', lastDisconnect?.error, ', reconnecting:', shouldReconnect);
                
                if (shouldReconnect) {
                    startBot();
                }
            } else if (connection === 'open') {
                console.log('WhatsApp connection opened successfully!');
                
                // Send quick reply button after connection
                setTimeout(() => {
                    sendQuickReplyButton(sock);
                }, 2000);
            }
        });

        // Message events
        sock.ev.on('messages.upsert', async (m) => {
            const message = m.messages[0];
            
            if (!message.key.fromMe && m.type === 'notify') {
                console.log('Received message:', message);
                
                // Handle button responses
                if (message.message?.buttonsResponseMessage) {
                    const buttonResponse = message.message.buttonsResponseMessage.selectedButtonId;
                    const from = message.key.remoteJid;
                    
                    console.log(`Button clicked: ${buttonResponse}`);
                    
                    // Handle different button responses
                    switch(buttonResponse) {
                        case 'copy_promo_code':
                        case 'copy_code':
                            await sock.sendMessage(from, {
                                text: '🎉 *Promo Code Ready!*\n\n📋 Your code: *SAVE50*\n\n✅ *How to use:*\n1. Copy this code: SAVE50\n2. Go to our website\n3. Add items to cart\n4. Paste code at checkout\n5. Enjoy 50% discount!\n\n💡 *Tip:* Select and copy the code above to your clipboard.'
                            });
                            break;
                            
                        case 'visit_site':
                            await sock.sendMessage(from, {
                                text: '🌐 *Visit Our Website*\n\n🔗 Link: https://yourwebsite.com\n\n✨ *What you\'ll find:*\n• Browse our products\n• Special offers section\n• Easy checkout process\n• Customer reviews\n\n💡 Don\'t forget to use code SAVE50 at checkout!'
                            });
                            break;
                            
                        case 'get_support':
                            await sock.sendMessage(from, {
                                text: '💬 *Support Available 24/7*\n\n📧 Email: support@company.com\n📱 WhatsApp: Just reply here!\n🕒 Response time: Usually under 1 hour\n\n💡 *Need help with:*\n• Using your promo code\n• Account issues\n• Product questions\n• Technical support\n\nHow can we help you today?'
                            });
                            break;
                            
                        default:
                            await sock.sendMessage(from, {
                                text: `Button clicked: ${buttonResponse}`
                            });
                    }
                }

                // Handle template button responses
                if (message.message?.templateButtonReplyMessage) {
                    const templateResponse = message.message.templateButtonReplyMessage;
                    const from = message.key.remoteJid;
                    
                    console.log('Template button response:', templateResponse);
                    
                    if (templateResponse.selectedId === 'copy_promo_code') {
                        await sock.sendMessage(from, {
                            text: '🎉 *Promo Code Ready!*\n\n📋 Code: *SAVE50*\n\nThis code gives you 50% off your purchase!'
                        });
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error starting bot:', error);
    }
}

// Start the bot
startBot();
