const MessageUtils = require('../utils/messageUtils');

class InteractivePlugin {
    constructor(bot) {
        this.bot = bot;
        this.messageUtils = null; // Will be initialized when bot socket is ready
        this.name = 'interactive';
        this.description = 'Enhanced interactive messages with @neoxr/wb features';
        this.commands = ['buttons', 'list', 'poll', 'carousel', 'quick', 'location', 'contact'];
        this.emoji = '🎮';
        
        // Initialize messageUtils when socket becomes available
        this.initializeMessageUtils();
    }

    initializeMessageUtils() {
        // Check periodically for socket availability
        const checkSocket = () => {
            if (this.bot.sock && !this.messageUtils) {
                this.messageUtils = new MessageUtils(this.bot.sock);
                console.log('🎮 Interactive plugin initialized with socket');
            } else if (!this.bot.sock) {
                setTimeout(checkSocket, 1000);
            }
        };
        checkSocket();
    }

    async execute(command, messageData, args) {
        try {
            if (!this.bot.connected) {
                return await this.bot.sendMessage(messageData.from, 'Bot is not connected to WhatsApp');
            }

            // Ensure messageUtils is initialized
            if (!this.messageUtils && this.bot.sock) {
                this.messageUtils = new MessageUtils(this.bot.sock);
            }

            switch (command) {
                case 'buttons':
                    return await this.sendButtonDemo(messageData);
                
                case 'list':
                    return await this.sendListDemo(messageData);
                
                case 'poll':
                    return await this.sendPollDemo(messageData);
                
                case 'carousel':
                    return await this.sendCarouselDemo(messageData);
                
                case 'quick':
                    return await this.sendQuickReplyDemo(messageData);
                
                case 'location':
                    return await this.sendLocationDemo(messageData);
                
                case 'contact':
                    return await this.sendContactDemo(messageData);
                
                default:
                    return await this.sendInteractiveMenu(messageData);
            }
        } catch (error) {
            console.error('❌ Error in interactive plugin:', error);
            return await this.bot.sendMessage(messageData.from, 'Error executing interactive command');
        }
    }

    async sendButtonDemo(messageData) {
        const buttons = [
            { id: 'like', text: '👍 Like' },
            { id: 'share', text: '📤 Share' },
            { id: 'save', text: '💾 Save' }
        ];

        await this.messageUtils.sendButtonMessage(
            messageData.from,
            "🎮 Interactive Buttons Demo\n\nChoose an action below:",
            buttons,
            { footer: 'WhatsApp Bot Interactive Features' }
        );

        return true;
    }

    async sendListDemo(messageData) {
        const sections = [
            {
                title: "🍕 Food Menu",
                rows: [
                    { id: 'pizza', title: 'Pizza Margherita', description: 'Classic Italian pizza - $12.99' },
                    { id: 'burger', title: 'Cheeseburger', description: 'Juicy beef burger - $9.99' },
                    { id: 'pasta', title: 'Spaghetti Carbonara', description: 'Creamy pasta dish - $11.99' }
                ]
            },
            {
                title: "🥤 Beverages",
                rows: [
                    { id: 'coke', title: 'Coca Cola', description: 'Refreshing cold drink - $2.99' },
                    { id: 'coffee', title: 'Espresso', description: 'Strong Italian coffee - $3.99' },
                    { id: 'juice', title: 'Orange Juice', description: 'Fresh squeezed - $4.99' }
                ]
            }
        ];

        await this.messageUtils.sendListMessage(
            messageData.from,
            "🛒 Restaurant Menu",
            "Browse our delicious menu options below:",
            sections,
            "View Menu"
        );

        return true;
    }

    async sendPollDemo(messageData) {
        await this.messageUtils.sendPoll(
            messageData.from,
            "🗳️ What's your favorite programming language?",
            ["JavaScript", "Python", "Java", "C++", "Go", "Rust"],
            false // Single selection
        );

        return true;
    }

    async sendCarouselDemo(messageData) {
        const cards = [
            {
                id: 'web_dev',
                title: '🌐 Web Development',
                subtitle: 'Frontend & Backend',
                description: 'Learn HTML, CSS, JavaScript, React, Node.js and more'
            },
            {
                id: 'mobile_dev',
                title: '📱 Mobile Development',
                subtitle: 'iOS & Android',
                description: 'Build native and cross-platform mobile applications'
            },
            {
                id: 'ai_ml',
                title: '🤖 AI & Machine Learning',
                subtitle: 'Artificial Intelligence',
                description: 'Explore neural networks, deep learning, and AI algorithms'
            },
            {
                id: 'devops',
                title: '⚙️ DevOps',
                subtitle: 'Development Operations',
                description: 'Master CI/CD, Docker, Kubernetes, and cloud platforms'
            }
        ];

        await this.messageUtils.sendCarouselMessage(
            messageData.from,
            "🎓 Tech Learning Paths",
            cards
        );

        return true;
    }

    async sendQuickReplyDemo(messageData) {
        const quickReplies = [
            { id: 'yes', text: '✅ Yes' },
            { id: 'no', text: '❌ No' },
            { id: 'maybe', text: '🤔 Maybe Later' }
        ];

        await this.messageUtils.sendQuickReplyMessage(
            messageData.from,
            "❓ Quick Reply Demo\n\nWould you like to receive notifications about new features?",
            quickReplies,
            { footer: 'Choose your preference' }
        );

        return true;
    }

    async sendLocationDemo(messageData) {
        // Example: Sending location of Times Square, New York
        await this.messageUtils.sendLocation(
            messageData.from,
            40.7580,
            -73.9855,
            "Times Square, New York, NY"
        );

        await this.bot.sendMessage(messageData.from, "📍 Location Demo\n\nThis is Times Square in New York City!");

        return true;
    }

    async sendContactDemo(messageData) {
        const contacts = [
            {
                name: "WhatsApp Bot Support",
                number: "1234567890"
            }
        ];

        await this.messageUtils.sendContact(messageData.from, contacts);
        await this.bot.sendMessage(messageData.from, "📞 Contact Demo\n\nHere's a sample contact card!");

        return true;
    }

    async sendInteractiveMenu(messageData) {
        const sections = [
            {
                title: "🎮 Interactive Demos",
                rows: [
                    { id: 'demo_buttons', title: 'Button Messages', description: 'Test interactive buttons' },
                    { id: 'demo_list', title: 'List Messages', description: 'Browse through menu lists' },
                    { id: 'demo_poll', title: 'Poll Messages', description: 'Create voting polls' },
                    { id: 'demo_carousel', title: 'Carousel Messages', description: 'Swipeable card layouts' }
                ]
            },
            {
                title: "📱 Media & Contact",
                rows: [
                    { id: 'demo_quick', title: 'Quick Replies', description: 'Fast response buttons' },
                    { id: 'demo_location', title: 'Location Sharing', description: 'Send location coordinates' },
                    { id: 'demo_contact', title: 'Contact Cards', description: 'Share contact information' }
                ]
            }
        ];

        await this.messageUtils.sendListMessage(
            messageData.from,
            "🎮 Interactive Features",
            "Explore advanced WhatsApp message types:",
            sections,
            "Try Features"
        );

        return true;
    }

    // Handle interactive responses
    async handleInteractiveResponse(message, responseData) {
        try {
            const { type, id, text } = responseData;
            const from = message.key.remoteJid;

            switch (id) {
                case 'like':
                    await this.bot.sendMessage(from, "👍 You liked this message!");
                    break;
                case 'share':
                    await this.bot.sendMessage(from, "📤 Thanks for sharing!");
                    break;
                case 'save':
                    await this.bot.sendMessage(from, "💾 Message saved to your favorites!");
                    break;
                case 'yes':
                    await this.bot.sendMessage(from, "✅ Great! You'll receive notifications about new features.");
                    break;
                case 'no':
                    await this.bot.sendMessage(from, "❌ No problem! You can change this anytime.");
                    break;
                case 'maybe':
                    await this.bot.sendMessage(from, "🤔 We'll ask again later!");
                    break;
                default:
                    if (id.startsWith('demo_')) {
                        const command = id.replace('demo_', '');
                        await this.executeDemo(from, command);
                    } else {
                        await this.bot.sendMessage(from, `You selected: ${text} (ID: ${id})`);
                    }
            }
        } catch (error) {
            console.error('❌ Error handling interactive response:', error);
        }
    }

    async executeDemo(from, command) {
        const messageData = { from };
        
        switch (command) {
            case 'buttons':
                await this.sendButtonDemo(messageData);
                break;
            case 'list':
                await this.sendListDemo(messageData);
                break;
            case 'poll':
                await this.sendPollDemo(messageData);
                break;
            case 'carousel':
                await this.sendCarouselDemo(messageData);
                break;
            case 'quick':
                await this.sendQuickReplyDemo(messageData);
                break;
            case 'location':
                await this.sendLocationDemo(messageData);
                break;
            case 'contact':
                await this.sendContactDemo(messageData);
                break;
        }
    }
}

module.exports = InteractivePlugin;