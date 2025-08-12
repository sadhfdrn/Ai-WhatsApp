const fs = require('fs');
const path = require('path');

class PluginManager {
    constructor(bot) {
        this.bot = bot;
        this.plugins = new Map();
        this.loadedCount = 0;
    }

    async loadPlugins() {
        try {
            const pluginsDir = path.join(__dirname);
            const pluginFiles = fs.readdirSync(pluginsDir)
                .filter(file => file.endsWith('.js') && file !== 'pluginManager.js');

            console.log(`🔌 Loading ${pluginFiles.length} plugins...`);

            for (const file of pluginFiles) {
                try {
                    const pluginPath = path.join(pluginsDir, file);
                    
                    // Clear require cache to allow reloading
                    delete require.cache[require.resolve(pluginPath)];
                    
                    const PluginClass = require(pluginPath);
                    const plugin = new PluginClass(this.bot);
                    
                    // Validate plugin structure
                    if (!plugin.name || !plugin.commands || !plugin.execute) {
                        console.log(`⚠️ Invalid plugin structure: ${file}`);
                        continue;
                    }

                    // Register plugin commands
                    for (const command of plugin.commands) {
                        if (this.plugins.has(command)) {
                            console.log(`⚠️ Command conflict: ${command} already exists`);
                        } else {
                            this.plugins.set(command, plugin);
                        }
                    }

                    this.loadedCount++;
                    console.log(`✅ Loaded plugin: ${plugin.name} (${plugin.commands.join(', ')})`);

                } catch (error) {
                    console.error(`❌ Failed to load plugin ${file}:`, error.message);
                }
            }

            console.log(`🎉 Successfully loaded ${this.loadedCount} plugins with ${this.plugins.size} commands`);
            
        } catch (error) {
            console.error('❌ Error loading plugins:', error);
        }
    }

    async executeCommand(messageData, command, args) {
        const plugin = this.plugins.get(command);
        
        if (!plugin) {
            return false; // Command not found
        }

        try {
            // Execute the plugin command (don't add extra reactions here since main.js handles them)
            const success = await plugin.execute(command, messageData, args);
            return success;

        } catch (error) {
            console.error(`❌ Error executing command ${command}:`, error);
            return false;
        }
    }

    getPlugin(command) {
        return this.plugins.get(command);
    }

    getAllPlugins() {
        const pluginMap = new Map();
        this.plugins.forEach((plugin, command) => {
            if (!pluginMap.has(plugin.name)) {
                pluginMap.set(plugin.name, plugin);
            }
        });
        return Array.from(pluginMap.values());
    }

    getCommandList() {
        return Array.from(this.plugins.keys());
    }

    async reloadPlugins() {
        console.log('🔄 Reloading all plugins...');
        this.plugins.clear();
        this.loadedCount = 0;
        await this.loadPlugins();
    }
}

module.exports = PluginManager;