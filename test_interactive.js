// Test script for interactive message functionality
const { makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@neoxr/baileys');
const MessageUtils = require('./utils/messageUtils');

async function testInteractiveMessages() {
    console.log('🧪 Testing Interactive Message functionality...');

    try {
        // Load auth state
        const { state, saveCreds } = await useMultiFileAuthState('./wa-auth');
        
        // Create test socket
        const sock = makeWASocket({
            auth: state,
            printQRInTerminal: false,
            logger: require('pino')({ level: 'silent' })
        });

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('connection.update', async (update) => {
            const { connection } = update;
            
            if (connection === 'open') {
                console.log('✅ Connected! Testing interactive messages...');
                
                // Initialize MessageUtils
                const messageUtils = new MessageUtils(sock);
                
                // Get owner JID (you should replace this with your number)
                const ownerJid = sock.user.id.split(':')[0] + '@s.whatsapp.net';
                
                console.log('📤 Testing enhanced button messages...');
                await messageUtils.sendButtonMessage(ownerJid, "🎮 Testing Enhanced Interactive Buttons!", [
                    { id: 'test_btn1', text: '✅ Button 1' },
                    { id: 'test_btn2', text: '🚀 Button 2' },
                    { id: 'test_btn3', text: '💡 Button 3' }
                ], { footer: 'Hybrid Interactive Test' });

                setTimeout(async () => {
                    console.log('📤 Testing enhanced list messages...');
                    await messageUtils.sendListMessage(
                        ownerJid,
                        "🛒 Enhanced List Test",
                        "This list uses hybrid interactive functionality:",
                        [
                            {
                                title: "🎮 Interactive Features",
                                rows: [
                                    { id: 'native_btn', title: 'Native Buttons', description: 'Test native button functionality' },
                                    { id: 'native_list', title: 'Native Lists', description: 'Test native list functionality' },
                                    { id: 'quick_reply', title: 'Quick Replies', description: 'Test quick reply buttons' }
                                ]
                            },
                            {
                                title: "🔧 Test Features",
                                rows: [
                                    { id: 'copy_code', title: 'Copy Code', description: 'Test copy code button' },
                                    { id: 'flow_msg', title: 'Flow Message', description: 'Test native flow message' }
                                ]
                            }
                        ],
                        "Try Features"
                    );
                }, 2000);

                setTimeout(async () => {
                    console.log('📤 Testing quick replies...');
                    await messageUtils.sendQuickReplyMessage(
                        ownerJid,
                        "❓ Quick Reply Test\n\nDo you like the new interactive features?",
                        [
                            { id: 'love_it', text: '❤️ Love it!' },
                            { id: 'good', text: '👍 Good' },
                            { id: 'needs_work', text: '🔧 Needs work' }
                        ],
                        { footer: 'Quick Reply Test' }
                    );
                }, 4000);

                setTimeout(async () => {
                    console.log('📤 Testing copy code message...');
                    await messageUtils.sendCopyCodeMessage(
                        ownerJid,
                        "💻 Copy Code Test\n\nHere's some sample code:",
                        "console.log('Interactive WhatsApp Bot is working!');",
                        { footer: 'Copy Code Test' }
                    );
                }, 6000);

                // Disconnect after tests
                setTimeout(() => {
                    console.log('✅ Interactive message tests completed!');
                    console.log('📱 Check your WhatsApp to see the results.');
                    process.exit(0);
                }, 10000);
            }
        });

        // Handle responses
        sock.ev.on('messages.upsert', async ({ messages }) => {
            for (const message of messages) {
                if (!message.key.fromMe && message.message) {
                    const messageUtils = new MessageUtils(sock);
                    const response = messageUtils.parseInteractiveResponse(message);
                    
                    if (response) {
                        console.log('🎮 Interactive response received:', response);
                        await sock.sendMessage(message.key.remoteJid, { 
                            text: `✅ Interactive response processed!\nType: ${response.type}\nID: ${response.id}` 
                        });
                    }
                }
            }
        });

    } catch (error) {
        console.error('❌ Test failed:', error);
    }
}

// Run test if called directly
if (require.main === module) {
    testInteractiveMessages();
}

module.exports = { testInteractiveMessages };