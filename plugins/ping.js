class PingPlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'ping';
        this.description = 'Shows bot status, uptime, and network speed';
        this.commands = ['ping'];
        this.emoji = '⚡';
    }

    async execute(messageData, command, args) {
        try {
            // Measure network speed by timing a simple request
            const networkSpeed = await this.measureNetworkSpeed();
            const uptime = Math.floor((Date.now() - this.bot.startTime) / 1000);
            
            const response = `🏓 Pong!\n⏱️ Uptime: ${this.formatUptime(uptime)}\n🌐 Network: ${networkSpeed}ms\n✅ Status: Online`;
            await this.bot.sendMessage(messageData.from, response);
            return true;
        } catch (error) {
            console.error('❌ Error in ping plugin:', error);
            return false;
        }
    }

    async measureNetworkSpeed() {
        try {
            const startTime = Date.now();
            
            await new Promise((resolve, reject) => {
                const https = require('https');
                const req = https.get('https://www.google.com', (res) => {
                    res.on('data', () => {});
                    res.on('end', resolve);
                });
                req.on('error', () => {
                    // Fallback to localhost health check
                    const http = require('http');
                    const fallbackReq = http.get('http://localhost:8080/health', (res) => {
                        res.on('data', () => {});
                        res.on('end', resolve);
                    });
                    fallbackReq.on('error', reject);
                    fallbackReq.setTimeout(2000, () => {
                        fallbackReq.destroy();
                        reject(new Error('Timeout'));
                    });
                });
                req.setTimeout(3000, () => {
                    req.destroy();
                    // Don't reject immediately, let the fallback handle it
                });
            });
            
            const endTime = Date.now();
            const latency = endTime - startTime;
            return `${latency}ms`;
            
        } catch (error) {
            console.error('❌ Error measuring network speed:', error);
            return 'N/A';
        }
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m ${secs}s`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }

    isValidCommand(command) {
        return this.commands.includes(command);
    }
}

module.exports = PingPlugin;