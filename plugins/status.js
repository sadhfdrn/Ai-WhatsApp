const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const { downloadMediaMessage } = require('baileys');

const execAsync = promisify(exec);

class StatusPlugin {
    constructor(bot) {
        this.bot = bot;
        this.name = 'status';
        this.description = 'Post text, images, videos, or voice messages to WhatsApp Status';
        this.commands = ['status', 'poststatus'];
        this.emoji = '📢';
        this.cooldown = 10000; // 10 second cooldown for status posts
        this.userCooldowns = new Map();
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

    // Helper function to format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Helper function to get video duration using ffprobe
    async getVideoDuration(videoPath) {
        try {
            const { stdout } = await execAsync(`ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${videoPath}"`);
            return parseFloat(stdout.trim());
        } catch (error) {
            console.error('❌ Error getting video duration:', error.message);
            return 0;
        }
    }

    // Helper function to trim video using ffmpeg
    async trimVideo(inputPath, outputPath, startTime, duration) {
        try {
            const command = `ffmpeg -i "${inputPath}" -ss ${startTime} -t ${duration} -c copy -avoid_negative_ts make_zero "${outputPath}" -y`;
            await execAsync(command);
            return true;
        } catch (error) {
            console.error('❌ Error trimming video:', error.message);
            return false;
        }
    }

    // Main function to split long videos into 1-minute segments
    async splitVideoForStatus(videoPath) {
        const duration = await this.getVideoDuration(videoPath);
        if (duration === 0) {
            throw new Error('Unable to get video duration');
        }

        console.log(`📏 Video duration: ${Math.ceil(duration)} seconds`);

        const segments = [];
        const segmentDuration = 60; // 1 minute
        let currentTime = 0;
        let segmentIndex = 1;

        while (currentTime < duration) {
            const remainingTime = duration - currentTime;
            const actualDuration = Math.min(segmentDuration, remainingTime);
            
            const outputPath = `downloads/status_segment_${Date.now()}_${segmentIndex}.mp4`;
            
            console.log(`✂️ Creating segment ${segmentIndex}: ${currentTime}s to ${currentTime + actualDuration}s`);
            
            const success = await this.trimVideo(videoPath, outputPath, currentTime, actualDuration);
            if (success) {
                segments.push({
                    path: outputPath,
                    index: segmentIndex,
                    startTime: currentTime,
                    duration: actualDuration
                });
            }

            currentTime += segmentDuration;
            segmentIndex++;
        }

        return segments;
    }

    // Main execution function
    async execute(messageData, command, args) {
        const userId = messageData.from;
        const isOwner = this.bot.ownerNumber && userId.includes(this.bot.ownerNumber);

        try {
            // Only allow owner to post status
            if (!isOwner) {
                await this.bot.sendMessage(userId, '❌ Only the bot owner can post to WhatsApp Status.');
                return false;
            }

            // Check cooldown
            const cooldownCheck = this.checkCooldown(userId);
            if (cooldownCheck.onCooldown) {
                await this.bot.sendMessage(userId, `⏰ Please wait ${cooldownCheck.remaining} seconds before posting another status.`);
                return false;
            }

            // Check if there's quoted/replied message with media or text
            const quotedMessage = messageData.originalMessage?.message?.extendedTextMessage?.contextInfo?.quotedMessage;
            
            if (!quotedMessage && !args.length) {
                await this.bot.sendMessage(userId, `📢 *WHATSAPP STATUS POSTER*\n\n**Usage:**\n• Reply to a message with \`.status\` to post it to your status\n• Use \`.status Your text here\` to post text status\n\n**Supported:**\n📝 Text messages\n📸 Images\n🎥 Videos (auto-trimmed to 1min segments)\n🎵 Voice messages\n\n**Note:** Videos longer than 1 minute will be automatically split into multiple status updates.`);
                return false;
            }

            // Handle text status
            if (args.length > 0 && !quotedMessage) {
                const statusText = args.join(' ');
                await this.postTextStatus(statusText);
                await this.bot.sendMessage(userId, `✅ Text status posted successfully!`);
                return true;
            }

            // Handle quoted message
            if (quotedMessage) {
                await this.bot.sendMessage(userId, '📢 Processing your status post...');
                await this.handleQuotedMessage(quotedMessage, userId);
                return true;
            }

        } catch (error) {
            console.error('❌ Status command error:', error.message);
            await this.bot.sendMessage(userId, `❌ Failed to post status: ${error.message}`);
            return false;
        }
    }

    // Handle different types of quoted messages
    async handleQuotedMessage(quotedMessage, userId) {
        try {
            // Text message
            if (quotedMessage.conversation) {
                await this.postTextStatus(quotedMessage.conversation);
                await this.bot.sendMessage(userId, '✅ Text status posted successfully!');
                return;
            }

            // Extended text message
            if (quotedMessage.extendedTextMessage?.text) {
                await this.postTextStatus(quotedMessage.extendedTextMessage.text);
                await this.bot.sendMessage(userId, '✅ Text status posted successfully!');
                return;
            }

            // Image message
            if (quotedMessage.imageMessage) {
                await this.handleImageStatus(quotedMessage.imageMessage, userId);
                return;
            }

            // Video message
            if (quotedMessage.videoMessage) {
                await this.handleVideoStatus(quotedMessage.videoMessage, userId);
                return;
            }

            // Audio/Voice message
            if (quotedMessage.audioMessage) {
                await this.handleAudioStatus(quotedMessage.audioMessage, userId);
                return;
            }

            await this.bot.sendMessage(userId, '❌ Unsupported message type for status posting.');

        } catch (error) {
            console.error('❌ Error handling quoted message:', error.message);
            await this.bot.sendMessage(userId, `❌ Failed to process quoted message: ${error.message}`);
        }
    }

    // Post text status
    async postTextStatus(text) {
        const statusJid = 'status@broadcast';
        await this.bot.sock.sendMessage(statusJid, { text: text });
        console.log('📢 Text status posted:', text.substring(0, 50) + (text.length > 50 ? '...' : ''));
    }

    // Handle image status
    async handleImageStatus(imageMessage, userId) {
        try {
            // Create message structure for download
            const messageForDownload = {
                key: { remoteJid: userId },
                message: { imageMessage }
            };

            // Download the image
            const buffer = await downloadMediaMessage(
                messageForDownload,
                'buffer',
                {},
                {
                    logger: console,
                    reuploadRequest: this.bot.sock.updateMediaMessage
                }
            );

            const statusJid = 'status@broadcast';
            const caption = imageMessage.caption || '';

            await this.bot.sock.sendMessage(statusJid, {
                image: buffer,
                caption: caption
            });

            await this.bot.sendMessage(userId, '✅ Image status posted successfully!');
            console.log('📢 Image status posted with size:', this.formatFileSize(buffer.length));

        } catch (error) {
            console.error('❌ Error posting image status:', error.message);
            await this.bot.sendMessage(userId, `❌ Failed to post image status: ${error.message}`);
        }
    }

    // Handle video status with auto-trimming
    async handleVideoStatus(videoMessage, userId) {
        try {
            // Create message structure for download
            const messageForDownload = {
                key: { remoteJid: userId },
                message: { videoMessage }
            };

            // Download the video
            const buffer = await downloadMediaMessage(
                messageForDownload,
                'buffer',
                {},
                {
                    logger: console,
                    reuploadRequest: this.bot.sock.updateMediaMessage
                }
            );

            const tempVideoPath = `downloads/temp_status_video_${Date.now()}.mp4`;
            await fs.writeFile(tempVideoPath, buffer);

            console.log('📥 Downloaded video for status:', this.formatFileSize(buffer.length));

            // Get video duration
            const duration = await this.getVideoDuration(tempVideoPath);
            
            if (duration <= 60) {
                // Video is 1 minute or less, post directly
                const statusJid = 'status@broadcast';
                const caption = videoMessage.caption || '';

                await this.bot.sock.sendMessage(statusJid, {
                    video: buffer,
                    caption: caption
                });

                await this.bot.sendMessage(userId, '✅ Video status posted successfully!');
                console.log('📢 Video status posted (single segment):', Math.ceil(duration), 'seconds');

            } else {
                // Video is longer than 1 minute, split it
                await this.bot.sendMessage(userId, `📏 Video is ${Math.ceil(duration)} seconds long. Splitting into ${Math.ceil(duration / 60)} segments...`);

                const segments = await this.splitVideoForStatus(tempVideoPath);
                
                if (segments.length === 0) {
                    throw new Error('Failed to create video segments');
                }

                const statusJid = 'status@broadcast';
                let successCount = 0;

                for (let i = 0; i < segments.length; i++) {
                    const segment = segments[i];
                    
                    try {
                        const segmentBuffer = await fs.readFile(segment.path);
                        const caption = videoMessage.caption ? 
                            `${videoMessage.caption} (Part ${segment.index}/${segments.length})` :
                            `Part ${segment.index}/${segments.length}`;

                        await this.bot.sock.sendMessage(statusJid, {
                            video: segmentBuffer,
                            caption: caption
                        });

                        successCount++;
                        console.log(`📢 Posted video segment ${segment.index}/${segments.length}`);

                        // Add small delay between posts
                        if (i < segments.length - 1) {
                            await new Promise(resolve => setTimeout(resolve, 2000));
                        }

                        // Clean up segment file
                        await fs.unlink(segment.path).catch(() => {});

                    } catch (segmentError) {
                        console.error(`❌ Error posting segment ${segment.index}:`, segmentError.message);
                        await fs.unlink(segment.path).catch(() => {});
                    }
                }

                await this.bot.sendMessage(userId, `✅ Video status posted in ${successCount}/${segments.length} segments!`);
            }

            // Clean up temporary file
            await fs.unlink(tempVideoPath).catch(() => {});

        } catch (error) {
            console.error('❌ Error posting video status:', error.message);
            await this.bot.sendMessage(userId, `❌ Failed to post video status: ${error.message}`);
        }
    }

    // Handle audio/voice status
    async handleAudioStatus(audioMessage, userId) {
        try {
            // Create message structure for download
            const messageForDownload = {
                key: { remoteJid: userId },
                message: { audioMessage }
            };

            // Download the audio
            const buffer = await downloadMediaMessage(
                messageForDownload,
                'buffer',
                {},
                {
                    logger: console,
                    reuploadRequest: this.bot.sock.updateMediaMessage
                }
            );

            const statusJid = 'status@broadcast';

            await this.bot.sock.sendMessage(statusJid, {
                audio: buffer,
                mimetype: 'audio/mp4',
                ptt: audioMessage.ptt || false // Voice note or regular audio
            });

            await this.bot.sendMessage(userId, '✅ Audio status posted successfully!');
            console.log('📢 Audio status posted with size:', this.formatFileSize(buffer.length));

        } catch (error) {
            console.error('❌ Error posting audio status:', error.message);
            await this.bot.sendMessage(userId, `❌ Failed to post audio status: ${error.message}`);
        }
    }

    isValidCommand(command) {
        return this.commands.includes(command);
    }
}

module.exports = StatusPlugin;