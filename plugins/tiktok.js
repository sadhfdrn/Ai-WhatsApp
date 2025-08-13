const fs = require('fs').promises;
const path = require('path');
const Tiktok = require("@tobyg74/tiktok-api-dl");

class TikTokPlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'tiktok';
        this.description = 'Download TikTok videos using npm package';
        this.commands = ['tiktok', 'tt'];
        this.emoji = '🎵';
        this.cooldown = 5000; // 5 second cooldown
        this.userCooldowns = new Map();
        this.version = "v3"; // Using v3 API version for direct video URLs
    }

    // Helper function to check cooldown
    checkCooldown(userId) {
        const now = Date.now();
        const cooldownEnd = this.userCooldowns.get(userId) || 0;
        
        if (now < cooldownEnd) {
            const remaining = Math.ceil((cooldownEnd - now) / 1000);
            return { onCooldown: true, remaining };
        }
        
        this.userCooldowns.set(userId, now + this.cooldown);
        return { onCooldown: false };
    }

    // Helper function to extract TikTok URL variations
    getTikTokUrlVariations(originalUrl) {
        const variations = [originalUrl];
        
        // Handle shortened URLs (vt.tiktok.com)
        if (originalUrl.includes('vt.tiktok.com')) {
            // Extract short code properly handling trailing slash
            const shortCode = originalUrl.replace(/\/$/, '').split('/').pop().split('?')[0];
            if (shortCode) {
                variations.push(`https://www.tiktok.com/t/${shortCode}`);
                
                // Try case variations for the short code
                variations.push(`https://vt.tiktok.com/${shortCode.toUpperCase()}/`);
                variations.push(`https://vt.tiktok.com/${shortCode.toLowerCase()}/`);
            }
        }
        
        return variations;
    }

    // Helper function to format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Helper function to format duration
    formatDuration(seconds) {
        if (!seconds) return 'Unknown';
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return minutes > 0 ? `${minutes}:${remainingSeconds.toString().padStart(2, '0')}` : `${seconds}s`;
    }

    // Main download function using @tobyg74/tiktok-api-dl
    async downloadTikTokVideo(url) {
        try {
            console.log(`🎵 Starting TikTok download using npm package: ${url}`);
            
            const urlVariations = this.getTikTokUrlVariations(url);
            let lastError = null;
            
            // Try each URL variation
            for (const testUrl of urlVariations) {
                try {
                    console.log(`🔄 Trying URL: ${testUrl}`);
                    
                    const result = await Tiktok.Downloader(testUrl, {
                        version: this.version,
                        showOriginalResponse: false
                    });
                    
                    if (result && result.status === "success" && result.result) {
                        const data = result.result;
                        console.log(`🔍 API Response structure:`, JSON.stringify(data, null, 2));
                        
                        // Extract video information
                        const videoInfo = {
                            title: data.title || 'TikTok Video',
                            author: data.author || 'Unknown',
                            video_id: data.video_id || data.id || 'unknown',
                            duration: data.duration || 0,
                            description: data.description || data.title || '',
                            stats: {
                                views: data.play_count || data.statistics?.playCount || 0,
                                likes: data.digg_count || data.statistics?.diggCount || 0,
                                comments: data.comment_count || data.statistics?.commentCount || 0,
                                shares: data.share_count || data.statistics?.shareCount || 0
                            }
                        };
                        
                        // Get the best video URL - handle different API response structures
                        let videoUrl = null;
                        
                        console.log(`🔍 V3 API Response - Available video URLs:`, {
                            hasVideoSD: !!data.videoSD,
                            hasVideoHD: !!data.videoHD,
                            hasVideoWatermark: !!data.videoWatermark,
                            dataKeys: Object.keys(data)
                        });
                        
                        // V3 API provides direct video URLs - prefer HD, fallback to SD
                        if (data.videoHD) {
                            videoUrl = data.videoHD;
                            console.log(`✅ Using HD video: ${videoUrl}`);
                        } else if (data.videoSD) {
                            videoUrl = data.videoSD;
                            console.log(`✅ Using SD video: ${videoUrl}`);
                        } else if (data.videoWatermark) {
                            videoUrl = data.videoWatermark;
                            console.log(`✅ Using watermarked video: ${videoUrl}`);
                        }
                        
                        // Fallback for other API versions
                        else if (data.playUrl && Array.isArray(data.playUrl) && data.playUrl.length > 0) {
                            videoUrl = data.playUrl[0];
                            console.log(`✅ Fallback: Found video URL in playUrl[0]: ${videoUrl}`);
                        }
                        else if (data.video) {
                            if (data.video.noWatermark) {
                                videoUrl = data.video.noWatermark;
                                console.log(`✅ Fallback: Found video URL in video.noWatermark: ${videoUrl}`);
                            } else if (data.video.watermark) {
                                videoUrl = data.video.watermark;
                                console.log(`✅ Fallback: Found video URL in video.watermark: ${videoUrl}`);
                            }
                        }
                        
                        if (!videoUrl) {
                            throw new Error('No video download URL found');
                        }
                        
                        // Generate unique filename
                        const timestamp = Date.now();
                        const outputFile = `downloads/tiktok_${timestamp}.mp4`;
                        
                        // Download the video
                        console.log(`📥 Downloading video from: ${videoUrl}`);
                        
                        const https = require('https');
                        const http = require('http');
                        
                        const downloadPromise = new Promise((resolve, reject) => {
                            const client = videoUrl.startsWith('https://') ? https : http;
                            
                            client.get(videoUrl, {
                                headers: {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                }
                            }, (response) => {
                                if (response.statusCode !== 200) {
                                    reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
                                    return;
                                }
                                
                                const fileStream = require('fs').createWriteStream(outputFile);
                                const totalSize = parseInt(response.headers['content-length'] || '0');
                                
                                response.pipe(fileStream);
                                
                                fileStream.on('finish', () => {
                                    fileStream.close();
                                    resolve({
                                        success: true,
                                        ...videoInfo,
                                        file_size: totalSize,
                                        output_file: outputFile
                                    });
                                });
                                
                                fileStream.on('error', (error) => {
                                    fs.unlink(outputFile).catch(() => {});
                                    reject(error);
                                });
                            }).on('error', (error) => {
                                reject(error);
                            });
                        });
                        
                        return await downloadPromise;
                    }
                    
                } catch (error) {
                    console.log(`❌ Failed with URL ${testUrl}: ${error.message}`);
                    lastError = error;
                    continue;
                }
            }
            
            // If we get here, no URL worked
            throw new Error(lastError?.message || 'Failed to download from any URL variation');
            
        } catch (error) {
            console.error(`❌ TikTok download error: ${error.message}`);
            return { 
                success: false, 
                error: `Download failed: ${error.message}` 
            };
        }
    }

    // Main command handler
    async execute(messageData, command, args) {
        const userId = messageData.from;
        
        try {
            // Check cooldown
            const cooldownCheck = this.checkCooldown(userId);
            if (cooldownCheck.onCooldown) {
                await this.bot.sendMessage(userId, `⏰ Please wait ${cooldownCheck.remaining} seconds before using this command again.`);
                return false;
            }
            
            // Validate URL argument
            if (!args[0] || !args[0].includes('tiktok.com')) {
                await this.bot.sendMessage(userId, `❌ Please provide a valid TikTok URL.\n\nExample: .tt https://vt.tiktok.com/ZSSvq22PY/`);
                return false;
            }
            
            const url = args[0];
            
            // Send processing message
            await this.bot.sendMessage(userId, `🎵 *PROCESSING TIKTOK VIDEO*\n📍 Requested from: ${userId.includes('@g.us') ? 'Group' : 'Private'}\n🔗 URL: ${url}\n⏳ Downloading...`);
            
            // Download the video using npm package
            const result = await this.downloadTikTokVideo(url);
            
            if (result.success) {
                // Check if file exists and get size
                try {
                    const stats = await fs.stat(result.output_file);
                    const fileSize = stats.size;
                    
                    // WhatsApp file size limit is 64MB for videos
                    const maxSize = 64 * 1024 * 1024; // 64MB in bytes
                    
                    if (fileSize > maxSize) {
                        await this.bot.sendMessage(userId, `❌ Video is too large (${this.formatFileSize(fileSize)}). WhatsApp supports videos up to 64MB.`);
                        
                        // Clean up large file
                        await fs.unlink(result.output_file).catch(() => {});
                        return false;
                    }
                    
                    // Send the video
                    const videoBuffer = await fs.readFile(result.output_file);
                    
                    await this.bot.sendMessage(userId, {
                        video: videoBuffer,
                        caption: `✅ *TIKTOK VIDEO DOWNLOADED*\n\n📝 Title: ${result.title}\n👤 Author: @${result.author}\n⏱️ Duration: ${this.formatDuration(result.duration)}\n📊 Size: ${this.formatFileSize(fileSize)}\n\n📈 Stats:\n👀 Views: ${result.stats.views.toLocaleString()}\n❤️ Likes: ${result.stats.likes.toLocaleString()}\n💬 Comments: ${result.stats.comments.toLocaleString()}\n📤 Shares: ${result.stats.shares.toLocaleString()}`,
                        gifPlayback: false
                    });
                    
                    console.log(`✅ TikTok video sent successfully: ${result.output_file}`);
                    
                    // Clean up downloaded file after sending
                    setTimeout(async () => {
                        try {
                            await fs.unlink(result.output_file);
                            console.log(`🧹 Cleaned up: ${result.output_file}`);
                        } catch (error) {
                            console.log(`⚠️ Could not clean up ${result.output_file}: ${error.message}`);
                        }
                    }, 5000); // Clean up after 5 seconds
                    
                    return true;
                    
                } catch (error) {
                    console.error(`❌ File processing error: ${error.message}`);
                    await this.bot.sendMessage(userId, `❌ Failed to process downloaded video: ${error.message}`);
                    return false;
                }
                
            } else {
                // Send error message
                await this.bot.sendMessage(userId, `❌ Failed to download TikTok video: ${result.error}`);
                return false;
            }
            
        } catch (error) {
            console.error(`❌ TikTok command error: ${error.message}`);
            await this.bot.sendMessage(userId, `❌ An error occurred: ${error.message}`);
            return false;
        }
    }

    isValidCommand(command) {
        return this.commands.includes(command);
    }
}

module.exports = TikTokPlugin;