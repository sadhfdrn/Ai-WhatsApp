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

async function sendListMessage(sock) {
    try {
        // Get your own number from credentials
        let targetNumber;
        
        if (credentials.me && credentials.me.id) {
            targetNumber = credentials.me.id;
        } else {
            targetNumber = "2349113085799@s.whatsapp.net";
        }
        
        console.log('Sending list message to:', targetNumber);
        
        // List Message Format
        const listMessage = {
            text: '🛍️ *Welcome to Our Store!*\n\nChoose from our amazing products below:',
            footer: 'Best deals of the season 🔥',
            title: '📱 Product Catalog',
            buttonText: 'View Products',
            sections: [
                {
                    title: '📱 Electronics',
                    rows: [
                        {
                            title: 'iPhone 15 Pro',
                            description: 'Latest iPhone with Pro features - $999',
                            rowId: 'iphone_15_pro'
                        },
                        {
                            title: 'Samsung Galaxy S24',
                            description: 'Premium Android experience - $899',
                            rowId: 'samsung_s24'
                        },
                        {
                            title: 'iPad Pro 12.9"',
                            description: 'Professional tablet for creators - $1,099',
                            rowId: 'ipad_pro'
                        }
                    ]
                },
                {
                    title: '💻 Computers',
                    rows: [
                        {
                            title: 'MacBook Air M3',
                            description: 'Lightweight and powerful - $1,199',
                            rowId: 'macbook_air'
                        },
                        {
                            title: 'Dell XPS 13',
                            description: 'Windows ultrabook - $999',
                            rowId: 'dell_xps'
                        },
                        {
                            title: 'Gaming PC Setup',
                            description: 'High-end gaming computer - $2,499',
                            rowId: 'gaming_pc'
                        }
                    ]
                },
                {
                    title: '🎧 Accessories',
                    rows: [
                        {
                            title: 'AirPods Pro',
                            description: 'Noise-canceling earbuds - $249',
                            rowId: 'airpods_pro'
                        },
                        {
                            title: 'Sony WH-1000XM5',
                            description: 'Premium over-ear headphones - $399',
                            rowId: 'sony_headphones'
                        },
                        {
                            title: 'Apple Watch Series 9',
                            description: 'Advanced fitness tracking - $399',
                            rowId: 'apple_watch'
                        }
                    ]
                },
                {
                    title: '🎯 Special Offers',
                    rows: [
                        {
                            title: '💰 Get 20% Off',
                            description: 'Use code SAVE20 for instant discount',
                            rowId: 'discount_20'
                        },
                        {
                            title: '📦 Free Shipping',
                            description: 'Free delivery on orders over $500',
                            rowId: 'free_shipping'
                        },
                        {
                            title: '💬 Contact Support',
                            description: 'Get help with your order',
                            rowId: 'contact_support'
                        }
                    ]
                }
            ]
        };

        await sock.sendMessage(targetNumber, listMessage);
        console.log('List message sent successfully!');
        
    } catch (error) {
        console.error('Error sending list message:', error);
        
        // Fallback to simple text message if list fails
        console.log('Trying fallback message...');
        try {
            const targetNumber = credentials.me.id || "2349113085799@s.whatsapp.net";
            
            const fallbackMessage = {
                text: '🛍️ *Welcome to Our Store!*\n\n📱 *Electronics:*\n• iPhone 15 Pro - $999\n• Samsung Galaxy S24 - $899\n• iPad Pro 12.9" - $1,099\n\n💻 *Computers:*\n• MacBook Air M3 - $1,199\n• Dell XPS 13 - $999\n• Gaming PC Setup - $2,499\n\n🎧 *Accessories:*\n• AirPods Pro - $249\n• Sony WH-1000XM5 - $399\n• Apple Watch Series 9 - $399\n\n🎯 *Special Offers:*\n• 20% off with code SAVE20\n• Free shipping over $500\n\nReply with product name for more details! 🛒'
            };
            
            await sock.sendMessage(targetNumber, fallbackMessage);
            console.log('Fallback message sent successfully!');
        } catch (fallbackError) {
            console.error('Fallback also failed:', fallbackError);
        }
    }
}

// Shopping cart to store multiple selections
let userCarts = {};

async function startBot() {
    console.log('Starting WhatsApp List Bot...');
    
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
                
                // Send list message after connection
                setTimeout(() => {
                    sendListMessage(sock);
                }, 2000);
            }
        });

        // Message events
        sock.ev.on('messages.upsert', async (m) => {
            const message = m.messages[0];
            
            if (!message.key.fromMe && m.type === 'notify') {
                console.log('Received message:', message);
                
                // Handle list response messages
                if (message.message?.listResponseMessage) {
                    const listResponse = message.message.listResponseMessage;
                    const selectedRowId = listResponse.singleSelectReply?.selectedRowId;
                    const from = message.key.remoteJid;
                    
                    console.log(`List item selected: ${selectedRowId}`);
                    
                    // Handle different list responses
                    switch(selectedRowId) {
                        case 'iphone_15_pro':
                            await sock.sendMessage(from, {
                                text: '📱 *iPhone 15 Pro*\n\n✨ *Features:*\n• A17 Pro chip\n• Pro camera system\n• Titanium design\n• Action Button\n• USB-C\n\n💰 *Price:* $999\n🚚 *Shipping:* 2-3 business days\n📞 *Warranty:* 1 year Apple Care\n\nWould you like to place an order? Reply "ORDER IPHONE" to proceed!'
                            });
                            break;
                            
                        case 'samsung_s24':
                            await sock.sendMessage(from, {
                                text: '📱 *Samsung Galaxy S24*\n\n✨ *Features:*\n• Snapdragon 8 Gen 3\n• AI-enhanced camera\n• 120Hz AMOLED display\n• S Pen compatible\n• 5G connectivity\n\n💰 *Price:* $899\n🚚 *Shipping:* 1-2 business days\n📞 *Warranty:* 2 years Samsung Care\n\nWould you like to place an order? Reply "ORDER SAMSUNG" to proceed!'
                            });
                            break;
                            
                        case 'macbook_air':
                            await sock.sendMessage(from, {
                                text: '💻 *MacBook Air M3*\n\n✨ *Specifications:*\n• Apple M3 chip\n• 8GB unified memory\n• 256GB SSD storage\n• 13.6" Liquid Retina display\n• Up to 18 hours battery\n\n💰 *Price:* $1,199\n🚚 *Shipping:* 3-5 business days\n📞 *Warranty:* 1 year AppleCare\n\nWould you like to place an order? Reply "ORDER MACBOOK" to proceed!'
                            });
                            break;
                            
                        case 'airpods_pro':
                            await sock.sendMessage(from, {
                                text: '🎧 *AirPods Pro (2nd Gen)*\n\n✨ *Features:*\n• Active Noise Cancellation\n• Adaptive Transparency\n• Spatial Audio\n• MagSafe charging case\n• Up to 6 hours listening time\n\n💰 *Price:* $249\n🚚 *Shipping:* Same day delivery\n📞 *Warranty:* 1 year limited warranty\n\nWould you like to place an order? Reply "ORDER AIRPODS" to proceed!'
                            });
                            break;
                            
                        case 'discount_20':
                            await sock.sendMessage(from, {
                                text: '💰 *20% Discount Code*\n\n🎉 *SAVE20* - Your exclusive discount code!\n\n✅ *How to use:*\n1. Choose your products\n2. Add to cart\n3. Enter code: SAVE20\n4. Get 20% off instantly!\n\n⏰ *Valid until:* End of this month\n🛒 *Minimum order:* $100\n📦 *Cannot combine* with other offers\n\nStart shopping now and save big! 🛍️'
                            });
                            break;
                            
                        case 'contact_support':
                            await sock.sendMessage(from, {
                                text: '💬 *Customer Support*\n\n👋 Hi! How can we help you today?\n\n📞 *Contact Options:*\n• WhatsApp: Just reply here!\n• Email: support@store.com\n• Phone: +1-800-SUPPORT\n• Live Chat: Available 24/7\n\n🕒 *Response Times:*\n• WhatsApp: Instant\n• Email: Within 2 hours\n• Phone: Available 9AM-9PM\n\n💡 *Common Help Topics:*\n• Order status\n• Product information\n• Returns & exchanges\n• Technical support\n• Payment issues\n\nWhat can we help you with?'
                            });
                            break;
                            
                        default:
                            await sock.sendMessage(from, {
                                text: `Thanks for selecting: ${selectedRowId}\n\nFor more information about this product, please contact our support team or visit our website!`
                            });
                    }
                }
                
                // Handle regular text messages
                if (message.message?.conversation || message.message?.extendedTextMessage?.text) {
                    const text = message.message?.conversation || message.message?.extendedTextMessage?.text;
                    const from = message.key.remoteJid;
                    
                    // Handle order commands
                    if (text.toUpperCase().includes('ORDER')) {
                        await sock.sendMessage(from, {
                            text: '🛒 *Ready to Order!*\n\nGreat choice! To complete your order:\n\n1️⃣ Confirm your shipping address\n2️⃣ Choose payment method\n3️⃣ Review your order\n\nPlease provide your:\n📍 Full shipping address\n📞 Phone number\n💳 Preferred payment method\n\nOur team will contact you within 30 minutes to finalize! 🚀'
                        });
                    } else if (text.toLowerCase().includes('help') || text.toLowerCase().includes('menu')) {
                        // Send the list message again
                        setTimeout(() => {
                            sendListMessage(sock);
                        }, 500);
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
