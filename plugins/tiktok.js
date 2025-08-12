const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs');
const path = require('path');

const execAsync = promisify(exec);

class TikTokPlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'tiktok';
        this.description = 'Download TikTok videos from URL';
        this.commands = ['tiktok', 'tt'];
        this.emoji = '🎵';
        this.ownerJid = null;
        this.downloadDir = './downloads';
        
        // Create downloads directory
        if (!fs.existsSync(this.downloadDir)) {
            fs.mkdirSync(this.downloadDir, { recursive: true });
        }
    }

    async execute(messageData, command, args) {
        try {
            // Get owner JID for DM functionality
            if (!this.ownerJid && this.bot.ownerNumber) {
                this.ownerJid = this.bot.ownerNumber + '@s.whatsapp.net';
            }

            if (['tiktok', 'tt'].includes(command)) {
                return await this.downloadTikTok(messageData, args);
            }

            return false;
        } catch (error) {
            console.error(`❌ Error in tiktok plugin (${command}):`, error);
            return false;
        }
    }

    async downloadTikTok(messageData, args) {
        try {
            if (!args || args.length === 0) {
                // Send usage to DM only
                if (this.ownerJid) {
                    const usage = `🎵 *TIKTOK DOWNLOADER*\n\n` +
                                `📝 Usage:\n` +
                                `.tiktok {url} - Download TikTok video\n` +
                                `.tt {url} - Short version\n\n` +
                                `📋 Example:\n` +
                                `.tiktok https://www.tiktok.com/@user/video/123456789\n\n` +
                                `🔄 The video will be sent to current chat and saved to your DM`;
                    
                    await this.bot.sendMessage(this.ownerJid, usage);
                }
                return true;
            }

            const url = args.join(' ').trim();
            
            // Validate TikTok URL
            if (!this.isValidTikTokURL(url)) {
                if (this.ownerJid) {
                    await this.bot.sendMessage(this.ownerJid, '❌ Invalid TikTok URL. Please provide a valid TikTok video link.');
                }
                return true;
            }

            console.log(`🎵 Starting TikTok download: ${url}`);
            
            // Send processing message to DM
            if (this.ownerJid) {
                await this.bot.sendMessage(this.ownerJid, `🎵 *PROCESSING TIKTOK VIDEO*\n\n📍 Requested from: ${messageData.from.includes('@g.us') ? 'Group' : 'Private'}\n🔗 URL: ${url}\n⏳ Downloading...`);
            }

            // Download the video
            const result = await this.downloadVideo(url);
            
            if (result.success) {
                console.log(`✅ TikTok video downloaded: ${result.filename}`);
                
                // Send video to current chat
                await this.sendVideo(messageData.from, result.filepath, result.title);
                
                // Also send to owner DM with context
                if (this.ownerJid && messageData.from !== this.ownerJid) {
                    await this.sendVideo(this.ownerJid, result.filepath, result.title);
                    
                    const chatType = messageData.from.includes('@g.us') ? 'Group' : 'Private';
                    const dmNotification = `🎵 *TIKTOK VIDEO DOWNLOADED*\n` +
                                         `⏰ Time: ${new Date().toLocaleString()}\n` +
                                         `📍 From: ${chatType} (${messageData.from})\n` +
                                         `👤 Requested by: ${messageData.sender}\n` +
                                         `🎬 Title: ${result.title || 'TikTok Video'}\n` +
                                         `💾 Video sent above`;
                    
                    await this.bot.sendMessage(this.ownerJid, dmNotification);
                }
                
                // Clean up downloaded file
                setTimeout(() => {
                    try {
                        if (fs.existsSync(result.filepath)) {
                            fs.unlinkSync(result.filepath);
                            console.log(`🧹 Cleaned up: ${result.filename}`);
                        }
                    } catch (error) {
                        console.error('❌ Error cleaning up file:', error);
                    }
                }, 30000); // Delete after 30 seconds
                
            } else {
                console.log(`❌ TikTok download failed: ${result.error}`);
                if (this.ownerJid) {
                    await this.bot.sendMessage(this.ownerJid, `❌ Failed to download TikTok video: ${result.error}`);
                }
            }

            return true;
        } catch (error) {
            console.error('❌ Error downloading TikTok video:', error);
            if (this.ownerJid) {
                await this.bot.sendMessage(this.ownerJid, '❌ Error processing TikTok download request');
            }
            return false;
        }
    }

    isValidTikTokURL(url) {
        const tiktokPatterns = [
            /^https?:\/\/(www\.)?tiktok\.com\/@[\w.-]+\/video\/\d+/,
            /^https?:\/\/vm\.tiktok\.com\/[\w]+/,
            /^https?:\/\/vt\.tiktok\.com\/[\w]+/,
            /^https?:\/\/m\.tiktok\.com\/v\/\d+/,
            /^https?:\/\/www\.tiktok\.com\/t\/[\w]+/
        ];
        
        return tiktokPatterns.some(pattern => pattern.test(url));
    }

    async downloadVideo(url) {
        try {
            const timestamp = Date.now();
            const outputTemplate = path.join(this.downloadDir, `tiktok_${timestamp}_%(title)s.%(ext)s`);
            
            // Use yt-dlp to download TikTok video
            const command = `python3 -m yt_dlp "${url}" -o "${outputTemplate}" --format "best[height<=720]" --no-playlist --extract-flat false --write-info-json --print filename`;
            
            console.log(`🔄 Running command: ${command}`);
            
            const { stdout, stderr } = await execAsync(command, {
                timeout: 60000, // 60 second timeout
                maxBuffer: 1024 * 1024 * 10 // 10MB buffer
            });
            
            if (stderr && !stderr.includes('WARNING')) {
                console.error('❌ yt-dlp stderr:', stderr);
                return { success: false, error: 'Download command failed' };
            }
            
            // Parse output to get filename
            const lines = stdout.trim().split('\n');
            const filename = lines[lines.length - 1].trim();
            const filepath = path.resolve(filename);
            
            if (!fs.existsSync(filepath)) {
                return { success: false, error: 'Downloaded file not found' };
            }
            
            // Try to get title from info file
            let title = 'TikTok Video';
            try {
                const infoFile = filepath.replace(/\.[^/.]+$/, '') + '.info.json';
                if (fs.existsSync(infoFile)) {
                    const info = JSON.parse(fs.readFileSync(infoFile, 'utf8'));
                    title = info.title || info.description || 'TikTok Video';
                    // Clean up info file
                    fs.unlinkSync(infoFile);
                }
            } catch (error) {
                console.log('⚠️ Could not read video info:', error.message);
            }
            
            return {
                success: true,
                filepath: filepath,
                filename: path.basename(filepath),
                title: title
            };
            
        } catch (error) {
            console.error('❌ Download error:', error);
            
            if (error.message.includes('timeout')) {
                return { success: false, error: 'Download timeout - video may be too large' };
            } else if (error.message.includes('not available')) {
                return { success: false, error: 'Video not available or private' };
            } else {
                return { success: false, error: 'Download failed: ' + error.message };
            }
        }
    }

    async sendVideo(chatId, filepath, title) {
        try {
            const videoBuffer = fs.readFileSync(filepath);
            const fileSize = videoBuffer.length;
            
            // Check file size (WhatsApp limit is around 16MB for videos)
            if (fileSize > 15 * 1024 * 1024) {
                await this.bot.sendMessage(chatId, '❌ Video too large for WhatsApp (>15MB). Please try a shorter video.');
                return false;
            }
            
            await this.bot.sock.sendMessage(chatId, {
                video: videoBuffer,
                caption: `🎵 ${title}\n\n📥 Downloaded from TikTok`,
                mimetype: 'video/mp4'
            });
            
            return true;
        } catch (error) {
            console.error('❌ Error sending video:', error);
            await this.bot.sendMessage(chatId, '❌ Error sending video: ' + error.message);
            return false;
        }
    }
}

module.exports = TikTokPlugin;