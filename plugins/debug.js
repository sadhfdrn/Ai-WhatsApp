class DebugPlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'debug';
        this.description = 'Debug message structures';
        this.commands = ['debug'];
        this.emoji = '🔍';
        this.ownerJid = null;
    }

    async execute(messageData, command, args) {
        try {
            // Get owner JID for DM functionality
            if (!this.ownerJid && this.bot.ownerNumber) {
                this.ownerJid = this.bot.ownerNumber + '@s.whatsapp.net';
            }

            switch (command) {
                case 'debug':
                    return await this.debugMessage(messageData);
                default:
                    return false;
            }
        } catch (error) {
            console.error(`❌ Error in debug plugin (${command}):`, error);
            return false;
        }
    }

    async debugMessage(messageData) {
        try {
            // Check if this is a reply to a message
            if (!messageData.quotedMessage) {
                await this.bot.sendMessage(messageData.from, '❌ Please reply to a message with .debug to see its structure');
                return true;
            }

            console.log('🔍 DEBUG: Full messageData structure:');
            console.log(JSON.stringify(messageData, null, 2));
            
            console.log('🔍 DEBUG: Quoted message structure:');
            console.log(JSON.stringify(messageData.quotedMessage, null, 2));
            
            if (messageData.originalMessage) {
                console.log('🔍 DEBUG: Original message structure:');
                console.log(JSON.stringify(messageData.originalMessage, null, 2));
            }

            // Send debug info to owner
            if (this.ownerJid) {
                const debugInfo = `🔍 *DEBUG INFO*

📋 **Message Data:**
- From: ${messageData.from}
- Sender: ${messageData.sender}
- Body: ${messageData.body}

📋 **Quoted Message:**
- ID: ${messageData.quotedMessage?.id || 'N/A'}
- Participant: ${messageData.quotedMessage?.participant || 'N/A'}
- Has content: ${messageData.quotedMessage?.content ? 'Yes' : 'No'}
- Has message: ${messageData.quotedMessage?.message ? 'Yes' : 'No'}

📋 **Original Message:**
- Available: ${messageData.originalMessage ? 'Yes' : 'No'}
- Has contextInfo: ${messageData.originalMessage?.message?.extendedTextMessage?.contextInfo ? 'Yes' : 'No'}

*Check console for full JSON structures*`;

                await this.bot.sendMessage(this.ownerJid, debugInfo);
            }

            await this.bot.sendMessage(messageData.from, '✅ Debug info sent to console and owner DM');
            return true;
        } catch (error) {
            console.error('❌ Error in debug:', error);
            await this.bot.sendMessage(messageData.from, '❌ Error processing debug');
            return false;
        }
    }

    isValidCommand(command) {
        return this.commands.includes(command);
    }
}

module.exports = DebugPlugin;