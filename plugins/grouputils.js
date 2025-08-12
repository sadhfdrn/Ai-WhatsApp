class GroupUtilsPlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'grouputils';
        this.description = 'Group utility commands for tagging and member information';
        this.commands = ['tag', 'tagall', 'gstatus'];
        this.emoji = '👥';
    }

    async execute(messageData, command, args) {
        try {
            switch (command) {
                case 'tag':
                    return await this.handleTag(messageData, args);
                case 'tagall':
                    return await this.handleTagAll(messageData);
                case 'gstatus':
                    return await this.handleGroupStatus(messageData);
                default:
                    return false;
            }
        } catch (error) {
            console.error(`❌ Error in grouputils plugin (${command}):`, error);
            return false;
        }
    }

    async handleTag(messageData, args) {
        const tagMessage = args.join(' ').trim();
        
        if (!tagMessage) {
            const prefixDisplay = this.bot.prefix || '';
            await this.bot.sendMessage(messageData.from, `❌ Please provide a message after ${prefixDisplay}tag\nExample: ${prefixDisplay}tag Hello everyone!`);
            return false;
        }

        return await this.tagAllMembers(messageData.from, tagMessage);
    }

    async handleTagAll(messageData) {
        return await this.tagAllMembersLoud(messageData.from);
    }

    async handleGroupStatus(messageData) {
        return await this.getGroupStatus(messageData);
    }

    async tagAllMembers(groupId, message) {
        try {
            // Check if it's a group (group IDs end with @g.us)
            if (!groupId.includes('@g.us')) {
                await this.bot.sendMessage(groupId, '❌ This command only works in groups!');
                return false;
            }

            // Get group metadata to fetch all participants
            const groupMetadata = await this.bot.sock.groupMetadata(groupId);
            const participants = groupMetadata.participants;

            if (!participants || participants.length === 0) {
                await this.bot.sendMessage(groupId, '❌ Could not fetch group members');
                return false;
            }

            // Create mentions array (exclude the bot itself)
            const mentions = participants
                .map(participant => participant.id)
                .filter(id => !id.includes(this.bot.sock.user?.id || ''));

            // Create the message with all mentions
            const tagMessage = {
                text: `📢 ${message}`,
                mentions: mentions
            };

            // Send the message with all mentions
            await this.bot.sock.sendMessage(groupId, tagMessage);
            console.log(`👥 Tagged ${mentions.length} members in group ${groupId}`);
            return true;

        } catch (error) {
            console.error('❌ Error tagging group members:', error);
            await this.bot.sendMessage(groupId, '❌ Failed to tag group members. Make sure I have admin permissions.');
            return false;
        }
    }

    async tagAllMembersLoud(groupId) {
        try {
            // Check if it's a group (group IDs end with @g.us)
            if (!groupId.includes('@g.us')) {
                await this.bot.sendMessage(groupId, '❌ This command only works in groups!');
                return false;
            }

            // Get group metadata to fetch all participants
            const groupMetadata = await this.bot.sock.groupMetadata(groupId);
            const participants = groupMetadata.participants;

            if (!participants || participants.length === 0) {
                await this.bot.sendMessage(groupId, '❌ Could not fetch group members');
                return false;
            }

            // Create mentions array (exclude the bot itself)
            const mentions = participants
                .map(participant => participant.id)
                .filter(id => !id.includes(this.bot.sock.user?.id || ''));

            // Create a loud notification message that tags everyone
            let tagText = '🔔 *ATTENTION EVERYONE!* 🔔\n\n';
            
            // Add each mention on a separate numbered line
            for (let i = 0; i < mentions.length; i++) {
                const phoneNumber = mentions[i].split('@')[0];
                tagText += `${i + 1}. @${phoneNumber}\n`;
            }

            const tagMessage = {
                text: tagText,
                mentions: mentions
            };

            // Send the loud notification message
            await this.bot.sock.sendMessage(groupId, tagMessage);
            console.log(`🔔 Loudly tagged ${mentions.length} members in group ${groupId}`);
            return true;

        } catch (error) {
            console.error('❌ Error tagging group members loudly:', error);
            await this.bot.sendMessage(groupId, '❌ Failed to tag group members. Make sure I have admin permissions.');
            return false;
        }
    }

    async getGroupStatus(messageData) {
        try {
            const groupId = messageData.from;
            
            // Check if it's a group (group IDs end with @g.us)
            if (!groupId.includes('@g.us')) {
                await this.bot.sendMessage(groupId, '❌ This command only works in groups!');
                return false;
            }

            // Get group metadata
            const groupMetadata = await this.bot.sock.groupMetadata(groupId);
            
            // Determine target user - either replied user or command sender
            let targetUser = messageData.sender;
            let isReply = false;
            
            // Check if this is a reply to someone's message
            if (messageData.quotedMessage && messageData.quotedMessage.participant) {
                targetUser = messageData.quotedMessage.participant;
                isReply = true;
            }
            
            // Find target participant in group
            const participant = groupMetadata.participants.find(p => p.id === targetUser);
            
            if (!participant) {
                await this.bot.sendMessage(groupId, '❌ User not found in this group');
                return false;
            }
            
            // Extract user phone number for display
            const phoneNumber = participant.id.split('@')[0];
            
            // Determine admin status
            let adminStatus = 'Member';
            if (participant.admin === 'superadmin') {
                adminStatus = 'Super Admin (Creator)';
            } else if (participant.admin === 'admin') {
                adminStatus = 'Admin';
            }
            
            // Format join date if available (not always provided by WhatsApp)
            let joinInfo = 'Join date not available';
            if (groupMetadata.creation) {
                joinInfo = `Group created: ${new Date(groupMetadata.creation * 1000).toLocaleDateString()}`;
            }
            
            // Get contact name if available
            let displayName = phoneNumber;
            try {
                // Try to get contact info
                const contact = await this.bot.sock.onWhatsApp(participant.id);
                if (contact && contact[0] && contact[0].name) {
                    displayName = contact[0].name;
                }
            } catch (error) {
                console.log('Could not fetch contact name');
            }
            
            // Build status message
            const statusMessage = `👤 *Group Member Status*
            
${isReply ? '📝 Replied User Info:' : '🔍 Your Group Info:'}

📱 *Phone:* +${phoneNumber}
👤 *Name:* ${displayName}
🛡️ *Role:* ${adminStatus}
📋 *User ID:* ${participant.id}

📊 *Group Info:*
🏷️ *Group:* ${groupMetadata.subject || 'Unknown'}
👥 *Total Members:* ${groupMetadata.participants.length}
🔢 *Group ID:* ${groupId}
📅 ${joinInfo}

${adminStatus.includes('Admin') ? '⚡ *Admin Privileges:* Yes' : '👤 *Admin Privileges:* No'}`;

            await this.bot.sendMessage(groupId, statusMessage);
            console.log(`👤 Group status shown for ${phoneNumber} in ${groupId}`);
            return true;

        } catch (error) {
            console.error('❌ Error getting group status:', error);
            await this.bot.sendMessage(messageData.from, '❌ Failed to get group status. Please try again.');
            return false;
        }
    }

    isValidCommand(command) {
        return this.commands.includes(command);
    }
}

module.exports = GroupUtilsPlugin;