class MenuPlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'menu';
        this.description = 'Shows bot command menu and help information';
        this.commands = ['menu', 'help', 'commands'];
        this.emoji = '📋';
    }

    async execute(messageData, command, args) {
        try {
            // Show menu with all available commands
            const menuMessage = this.formatMenu();
            await this.bot.sendMessage(messageData.from, menuMessage);
            return true;
        } catch (error) {
            console.error('❌ Error in menu plugin:', error);
            return false;
        }
    }

    formatMenu() {
        const prefix = this.bot.prefix || '';
        
        return `╭─────────────────────────────╮
│          🤖 *BOT MENU*          │
╰─────────────────────────────╯

┌─ 📊 *GENERAL COMMANDS*
├ ${prefix}ping - Bot status & uptime
├ ${prefix}menu - Show this menu
└ ${prefix}help - Command help

┌─ 👥 *GROUP COMMANDS*
├ ${prefix}tag <message> - Tag all silently
├ ${prefix}tagall - Tag all loudly
├ ${prefix}gstatus - Group member info
└ (Reply + gstatus for user info)

┌─ ℹ️ *BOT INFO*
├ Prefix: "${prefix || 'none'}"
├ Status: Online ✅
├ Version: 2.0
└ Plugins: ${this.bot.plugins ? this.bot.plugins.size : 0} loaded

╭─────────────────────────────╮
│     Made with ❤️ by Bot Dev     │
╰─────────────────────────────╯

💡 *Tip:* Reply to someone's message and use ${prefix}gstatus to get their group information!`;
    }

    isValidCommand(command) {
        return this.commands.includes(command);
    }
}

module.exports = MenuPlugin;