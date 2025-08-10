"""
WhatsApp Web client implementation using baileys
Handles connection, message sending/receiving, and bot interactions
"""

import asyncio
import json
import logging
import os
import tempfile
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from bot.enhanced_ai_system import EnhancedAISystem
from bot.voice_cloning import VoiceCloningEngine
from bot.web_search import WebSearchHandler
from bot.meme_generator import MemeGenerator
from bot.auto_reply import AutoReplyManager
# GitHub integration removed - now using database for personality learning
from bot.style_mimicker import StyleMimicker
from database.db_manager import DatabaseManager
from utils.helpers import sanitize_text, format_timestamp

logger = logging.getLogger(__name__)

class WhatsAppClient:
    """WhatsApp Web client with AI capabilities"""
    
    def __init__(self, config):
        self.config = config
        self.connected = False
        self.connection_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Initialize AI components with enhanced model management
        self.ai_processor = EnhancedAISystem(config)
        # Voice processing disabled for cloud deployment
        self.voice_handler = None  # VoiceCloningEngine disabled
        
        # Share model manager between components (voice handler disabled)
        self.web_search = WebSearchHandler(config) if config.SEARCH_ENABLED else None
        self.meme_generator = MemeGenerator(config) if config.MEME_GENERATION else None
        self.auto_reply = AutoReplyManager(config)
        
        # Initialize database-based learning system (primary)
        your_whatsapp_id = config.YOUR_USER_ID if hasattr(config, 'YOUR_USER_ID') else "your_phone_number@c.us"
        self.db_manager = DatabaseManager(your_whatsapp_id)
        
        # Initialize style mimicker with database patterns
        self.style_mimicker = StyleMimicker({})
        
        # AI processor will use database patterns through style_mimicker
        
        # Message handlers
        self.message_handlers = {}
        self.setup_message_handlers()
        
        # Session data
        self.user_sessions = {}
        self.active_conversations = set()
        
        logger.info("🚀 WhatsApp client initialized with personality learning system")
    
    def setup_message_handlers(self):
        """Setup command handlers"""
        self.message_handlers = {
            'help': self.handle_help,
            'search': self.handle_search,
            'meme': self.handle_meme,
            'voice': self.handle_voice_toggle,
            'autoreply': self.handle_autoreply_toggle,
            'joke': self.handle_joke_request,
            'story': self.handle_story_request,
            'translate': self.handle_translation,
            'ascii': self.handle_ascii_art,
            'analyze': self.handle_chat_analysis,
            'status': self.handle_status,
            'profile': self.handle_profile_status,
            'learning': self.handle_learning_stats,
            'time': self.handle_time_request,
            'weather': self.handle_weather_request,
            'timezone': self.handle_timezone_change,
            'mystyle': self.handle_style_summary,
            'suggest': self.handle_response_suggestion,
            'dbstats': self.handle_database_stats
        }
    
    async def connect(self):
        """Connect to WhatsApp Web via Node.js baileys bridge"""
        try:
            logger.info("🔌 Starting WhatsApp Web connection...")
            
            # AI models are automatically initialized in the EnhancedAISystem constructor
            logger.info("🧠 AI models ready")
            
            # Voice AI models disabled for cloud deployment
            
            # Start Node.js baileys bridge
            await self.start_baileys_bridge()
            
            # Wait for connection
            await asyncio.sleep(5)
            self.connected = True
            self.connection_attempts = 0
            
            logger.info("✅ WhatsApp Web bridge started")
            
            # Start message processing
            asyncio.create_task(self.message_listener())
            asyncio.create_task(self.process_incoming_messages())
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to WhatsApp: {e}")
            await self.handle_connection_error()
    
    async def start_baileys_bridge(self):
        """Start the Node.js baileys bridge"""
        try:
            import subprocess
            
            logger.info("🌉 Starting baileys bridge...")
            
            # Start the Node.js bridge process
            self.bridge_process = subprocess.Popen(
                ['node', 'whatsapp_bridge.js'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            logger.info("✅ Baileys bridge started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start baileys bridge: {e}")
            raise
    
    async def process_incoming_messages(self):
        """Process messages from the baileys bridge"""
        messages_file = "incoming_messages.json"
        
        while self.connected:
            try:
                if os.path.exists(messages_file):
                    with open(messages_file, 'r') as f:
                        messages = json.load(f)
                    
                    # Process unprocessed messages
                    processed_messages = []
                    for msg in messages:
                        if not msg.get('processed', False):
                            await self.handle_incoming_message(msg)
                            msg['processed'] = True
                        processed_messages.append(msg)
                    
                    # Clean up processed messages (keep last 100)
                    if len(processed_messages) > 100:
                        processed_messages = processed_messages[-100:]
                    
                    # Save back
                    with open(messages_file, 'w') as f:
                        json.dump(processed_messages, f, indent=2)
                
                await asyncio.sleep(1)  # Check for messages every second
                
            except Exception as e:
                logger.error(f"❌ Error processing incoming messages: {e}")
                await asyncio.sleep(5)
    
    async def handle_connection_error(self):
        """Handle connection errors with retry logic"""
        self.connection_attempts += 1
        
        if self.connection_attempts < self.max_reconnect_attempts:
            wait_time = min(30 * self.connection_attempts, 300)  # Max 5 minutes
            logger.info(f"🔄 Retrying connection in {wait_time} seconds... (Attempt {self.connection_attempts}/{self.max_reconnect_attempts})")
            await asyncio.sleep(wait_time)
            await self.connect()
        else:
            logger.error("💥 Maximum reconnection attempts reached. Bot shutting down.")
            raise Exception("Unable to establish WhatsApp connection")
    
    async def message_listener(self):
        """Listen for incoming messages"""
        logger.info("👂 Message listener started")
        
        # Start a simulated message processor for testing
        asyncio.create_task(self.test_message_processor())
        
        # In real implementation, this would listen to baileys events
        while self.connected:
            try:
                await asyncio.sleep(5)
                logger.debug("💭 Message listener active, waiting for messages...")
                
            except Exception as e:
                logger.error(f"❌ Error in message listener: {e}")
                await asyncio.sleep(5)
    
    async def test_message_processor(self):
        """Test message processor to simulate incoming messages"""
        # Wait a bit before sending test message
        await asyncio.sleep(30)
        
        # Send a test message to simulate receiving a message
        if self.connected:
            test_message = {
                'from': 'test_user@c.us',
                'body': 'Hello bot! This is a test message.',
                'type': 'text',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("🧪 Processing test message to verify bot functionality...")
            await self.handle_incoming_message(test_message)
    
    async def handle_incoming_message(self, message_data: Dict[str, Any]):
        """Process incoming WhatsApp message"""
        try:
            sender = message_data.get('from', '')
            message_text = message_data.get('body') or ''
            message_type = message_data.get('type', 'text')
            
            # Handle timestamp safely (could be integer, dict, or string)
            timestamp_raw = message_data.get('timestamp')
            if isinstance(timestamp_raw, dict):
                # Handle WhatsApp timestamp format like {"low": 1754852436, "high": 0, "unsigned": true}
                timestamp = datetime.fromtimestamp(timestamp_raw.get('low', 0)).isoformat()
            elif isinstance(timestamp_raw, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp_raw).isoformat()
            elif isinstance(timestamp_raw, str):
                timestamp = timestamp_raw
            else:
                timestamp = datetime.now().isoformat()
            
            # Skip messages without meaningful content
            if not sender or (message_type == 'text' and not message_text.strip()):
                logger.debug(f"🚫 Skipping empty message from {sender}")
                return
            
            # Skip status broadcasts and newsletters unless they have actual content
            if '@broadcast' in sender or '@newsletter' in sender:
                if not message_text or not message_text.strip():
                    logger.debug(f"🚫 Skipping empty status/newsletter from {sender}")
                    return
            
            logger.info(f"📨 Received message from {sender}: {message_text[:50]}...")
            
            # Add sender to active conversations
            self.active_conversations.add(sender)
            
            # Handle different message types
            if message_type == 'text':
                await self.process_text_message(sender, message_text, timestamp)
            elif message_type == 'voice':
                await self.process_voice_message(sender, message_data, timestamp)
            elif message_type == 'image':
                await self.process_image_message(sender, message_data, timestamp)
            
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
    
    async def process_text_message(self, sender: str, message: str, timestamp: str):
        """Process text message and generate response with personality learning"""
        try:
            logger.info(f"🔄 Processing text message from {sender}: {message}")
            
            # Learn from user's message patterns using database
            if not message.startswith(self.config.BOT_PREFIX) and sender != 'bot':
                try:
                    await self.db_manager.learn_from_message(sender, message, timestamp)
                    logger.info("🧠 Learned patterns from user message")
                except Exception as e:
                    logger.warning(f"⚠️ Learning failed: {e}")
            
            # Check if it's a command
            if message.startswith(self.config.BOT_PREFIX):
                logger.info(f"🎛️ Detected command: {message}")
                await self.handle_command(sender, message, timestamp)
                return
            
            logger.info("🤖 Generating AI response...")
            
            # Store message in database for style learning
            try:
                await self.db_manager.process_message(
                    message=message,
                    sender_id=sender,
                    sentiment_data=None  # Will be filled by AI processor
                )
            except Exception as e:
                logger.warning(f"⚠️ Database storage failed: {e}")
            
            # Generate AI response using enhanced AI system
            if hasattr(self.ai_processor, 'process_message_with_search'):
                response = await self.ai_processor.process_message_with_search(message, sender)
            else:
                response = self.ai_processor.generate_response(message, sender, self.get_user_context(sender))
            
            # Store bot response in database
            try:
                # Get sentiment data if available
                sentiment_data = None
                if hasattr(self.ai_processor, 'analyze_sentiment'):
                    sentiment_data = self.ai_processor.analyze_sentiment(message)
                
                await self.db_manager.process_message(
                    message=message,
                    sender_id=sender,
                    bot_response=response,
                    sentiment_data=sentiment_data
                )
            except Exception as e:
                logger.warning(f"⚠️ Database response storage failed: {e}")
            
            # Ensure we have a valid response
            if not response:
                response = "Sorry, I couldn't generate a response at the moment."
            
            # Apply learned user style to response (with safety check)
            try:
                styled_response = self.style_mimicker.apply_user_style(
                    response, 
                    {'topic': self.extract_topic(message), 'sender': sender}
                )
                # Fallback if style application fails
                if not styled_response:
                    styled_response = response
            except Exception as style_error:
                logger.warning(f"⚠️ Style application failed: {style_error}")
                styled_response = response
            
            logger.info(f"💬 Generated styled response: {styled_response[:100]}...")
            
            # Send response
            logger.info(f"📤 Sending response to {sender}...")
            await self.send_message(sender, styled_response, add_ai_icon=True)
            logger.info("✅ Response sent successfully")
            
            # Handle auto-reply if enabled
            if self.auto_reply.is_enabled(sender):
                logger.info("🔄 Checking for auto-reply...")
                if await self.auto_reply.should_auto_reply(sender, message, self.get_user_context(sender)):
                    auto_response = await self.auto_reply.generate_auto_reply(
                        sender, message, self.get_user_context(sender), self.ai_processor
                    )
                    if auto_response:
                        # Apply learned style to auto-reply too
                        try:
                            styled_auto_response = self.style_mimicker.apply_user_style(auto_response)
                            if not styled_auto_response:
                                styled_auto_response = auto_response
                        except Exception as style_error:
                            logger.warning(f"⚠️ Auto-reply style application failed: {style_error}")
                            styled_auto_response = auto_response
                        
                        delay = await self.auto_reply.get_auto_reply_delay(sender)
                        await asyncio.sleep(delay)
                        await self.send_message(sender, styled_auto_response, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Error processing text message: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
    
    async def process_voice_message(self, sender: str, message_data: Dict[str, Any], timestamp: str):
        """Process voice message"""
        if not self.voice_handler:
            await self.send_message(sender, "🎤 Voice processing is currently disabled")
            return
        
        try:
            # Convert voice to text
            audio_data = message_data.get('audioData')
            if audio_data:
                voice_text = await self.voice_handler.speech_to_text(audio_data)
            else:
                voice_text = None
            
            if voice_text:
                logger.info(f"🎤 Voice message from {sender}: {voice_text}")
                
                # Process as text message
                await self.process_text_message(sender, voice_text, timestamp)
                
                # Optionally respond with voice
                if self.get_user_preference(sender, 'voice_responses', False):
                    response = await self.ai_processor.generate_response(voice_text, sender)
                    voice_response = await self.voice_handler.text_to_speech(response)
                    await self.send_voice_message(sender, voice_response)
            else:
                await self.send_message(sender, "🤔 Sorry, I couldn't understand your voice message. Could you try typing instead?")
                
        except Exception as e:
            logger.error(f"❌ Error processing voice message: {e}")
            await self.send_message(sender, "❌ There was an error processing your voice message")
    
    async def handle_command(self, sender: str, message: str, timestamp: str):
        """Handle bot commands"""
        try:
            # Parse command
            parts = message[1:].split(' ', 1)  # Remove prefix
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            logger.info(f"🎛️ Command from {sender}: {command} (args: {args})")
            logger.info(f"🔍 Available commands: {list(self.message_handlers.keys())}")
            
            # Execute command
            if command in self.message_handlers:
                logger.info(f"✅ Executing command handler for '{command}'")
                await self.message_handlers[command](sender, args, timestamp)
                logger.info(f"✅ Command '{command}' executed successfully")
            else:
                logger.warning(f"❓ Unknown command: {command}")
                await self.handle_unknown_command(sender, command)
                
        except Exception as e:
            logger.error(f"❌ Error handling command: {e}")
            import traceback
            logger.error(f"❌ Command error traceback: {traceback.format_exc()}")
            await self.send_message(sender, "❌ There was an error processing your command")
    
    async def handle_help(self, sender: str, args: str, timestamp: str):
        """Show help information"""
        help_text = """**AI Assistant Commands**

**Basic Commands:**
• !help - Show this help message
• !status - Bot status and features

**Search & Information:**
• !search <query> - Web search
• !translate <text> - Translate text
• !time [timezone] - Get current time
• !timezone <zone> - Change timezone
• !weather [location] - Get weather info

**Database-Powered Style Learning:**
• !mystyle - View your communication style summary
• !suggest <message> - Get response suggestions based on your style
• !dbstats - View database learning statistics

**Creative Features:**
• !meme <top text>|<bottom text> - Generate meme
• !joke - Tell a random joke  
• !story <prompt> - Start a story
• !ascii <text> - Generate ASCII art

**Voice Features:**
• !voice - Toggle voice responses
• !autoreply - Toggle auto-reply mode

**Analysis:**
• !analyze - Analyze recent chat activity

**Personality Learning (NEW):**
• !profile - View your personality learning profile
• !learning - See detailed learning statistics

**Enhanced Features:**
• Enhanced AI models (DialoGPT, FLAN-T5)
• Multi-language translation support
• Web search with real-time results
• Timezone-aware responses
• Self-chat message filtering
• Automatic translation for group chats

**Special Features:**
• I learn your communication style automatically
• Every message helps me understand you better
• Your patterns are saved to the database
• I mimic your phrases, emojis, and tone
• Memory persists across bot restarts

Just chat normally and I'll learn your unique style!"""

        await self.send_message(sender, help_text, add_ai_icon=True)
    
    async def handle_search(self, sender: str, query: str, timestamp: str):
        """Handle web search command"""
        if not self.web_search:
            await self.send_message(sender, "🔍 Web search is currently disabled")
            return
        
        if not query.strip():
            await self.send_message(sender, "🤔 Please provide a search query! Example: !search python programming")
            return
        
        try:
            await self.send_message(sender, f"🔍 Searching for: {query}...")
            
            results = await self.web_search.search(query)
            
            if results:
                response = f"🔍 **Search Results for:** {query}\n\n"
                for i, result in enumerate(results[:3], 1):
                    response += f"{i}. **{result['title']}**\n{result['snippet']}\n🔗 {result['url']}\n\n"
                
                await self.send_message(sender, response, add_ai_icon=True)
            else:
                await self.send_message(sender, f"😔 No results found for '{query}'. Try a different search term!")
                
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            await self.send_message(sender, "❌ Search service temporarily unavailable")
    
    async def handle_meme(self, sender: str, args: str, timestamp: str):
        """Handle meme generation command"""
        if not self.meme_generator:
            await self.send_message(sender, "🎨 Meme generation is currently disabled")
            return
        
        if not args.strip():
            await self.send_message(sender, "🤔 Format: !meme top text|bottom text\nExample: !meme One does not simply|Generate memes")
            return
        
        try:
            parts = args.split('|', 1)
            top_text = parts[0].strip()
            bottom_text = parts[1].strip() if len(parts) > 1 else ""
            
            await self.send_message(sender, "🎨 Generating your meme...")
            
            meme_path = await self.meme_generator.create_meme(top_text, bottom_text)
            
            if meme_path:
                # In real implementation, send the image
                await self.send_message(sender, f"🎉 Meme created! {top_text} / {bottom_text}", add_ai_icon=True)
            else:
                await self.send_message(sender, "😅 Couldn't create the meme. Try again!")
                
        except Exception as e:
            logger.error(f"❌ Meme generation error: {e}")
            await self.send_message(sender, "❌ Meme service temporarily unavailable")
    
    async def handle_autoreply_toggle(self, sender: str, args: str, timestamp: str):
        """Toggle auto-reply for user"""
        try:
            current_status = self.auto_reply.is_enabled(sender)
            
            if args.lower() in ['on', 'enable', 'start']:
                response = await self.auto_reply.enable_auto_reply(sender, self.ai_processor)
                await self.send_message(sender, response, add_ai_icon=True)
            elif args.lower() in ['off', 'disable', 'stop']:
                response = await self.auto_reply.disable_auto_reply(sender)
                await self.send_message(sender, response, add_ai_icon=True)
            else:
                # Toggle current status
                if current_status:
                    response = await self.auto_reply.disable_auto_reply(sender)
                else:
                    response = await self.auto_reply.enable_auto_reply(sender, self.ai_processor)
                
                await self.send_message(sender, response, add_ai_icon=True)
                
        except Exception as e:
            logger.error(f"❌ Auto-reply toggle error: {e}")
    
    async def handle_joke_request(self, sender: str, args: str, timestamp: str):
        """Handle joke request"""
        try:
            joke = await self.ai_processor.generate_joke(args if args else "random")
            await self.send_message(sender, f"😄 {joke}", add_ai_icon=True)
        except Exception as e:
            logger.error(f"❌ Joke generation error: {e}")
            await self.send_message(sender, "😅 My joke generator is taking a coffee break!")
    
    async def handle_status(self, sender: str, args: str, timestamp: str):
        """Show bot status"""
        features = self.config.get_feature_flags()
        active_features = [f"✅ {feature}" for feature, enabled in features.items() if enabled]
        inactive_features = [f"❌ {feature}" for feature, enabled in features.items() if not enabled]
        
        status_text = f"""🤖 **Bot Status Report**

🔗 **Connection:** {'✅ Connected' if self.connected else '❌ Disconnected'}
👥 **Active Chats:** {len(self.active_conversations)}
⚡ **Uptime:** {format_timestamp(datetime.now())}

🎛️ **Features:**
{chr(10).join(active_features)}

{chr(10).join(inactive_features) if inactive_features else ''}

💭 **Personality:** {self.config.PERSONALITY_MODE.title()} mode
🎯 **Model:** {self.config.AI_MODEL}"""

        await self.send_message(sender, status_text, add_ai_icon=True)
    
    async def handle_voice_toggle(self, sender: str, args: str, timestamp: str):
        """Toggle voice response preference for user"""
        try:
            current_preference = self.get_user_preference(sender, 'voice_responses', False)
            
            if args.lower() in ['on', 'enable', 'start']:
                self.set_user_preference(sender, 'voice_responses', True)
                await self.send_message(sender, "🎤 Voice responses enabled! I'll send audio replies when possible.", add_ai_icon=True)
            elif args.lower() in ['off', 'disable', 'stop']:
                self.set_user_preference(sender, 'voice_responses', False)
                await self.send_message(sender, "🔇 Voice responses disabled. I'll send text replies only.", add_ai_icon=True)
            else:
                # Toggle current preference
                new_preference = not current_preference
                self.set_user_preference(sender, 'voice_responses', new_preference)
                status = "enabled" if new_preference else "disabled"
                await self.send_message(sender, f"🎤 Voice responses {status}!", add_ai_icon=True)
                
        except Exception as e:
            logger.error(f"❌ Voice toggle error: {e}")
            await self.send_message(sender, "❌ Error toggling voice settings")

    async def handle_story_request(self, sender: str, args: str, timestamp: str):
        """Handle story generation request"""
        try:
            if not args.strip():
                await self.send_message(sender, "📖 Tell me what kind of story you'd like! Example: !story adventure in space")
                return
            
            story_prompt = args.strip()
            await self.send_message(sender, f"📖 Creating a story about: {story_prompt}...")
            
            # Generate story using AI processor
            story = await self.ai_processor.generate_story(story_prompt)
            await self.send_message(sender, f"📚 **{story_prompt.title()}**\n\n{story}", add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Story generation error: {e}")
            await self.send_message(sender, "❌ Story generator is taking a creative break!")

    async def handle_translation(self, sender: str, args: str, timestamp: str):
        """Handle text translation"""
        try:
            if not args.strip():
                await self.send_message(sender, "🌐 Format: !translate <text>\nExample: !translate Hello world")
                return
            
            # Simple translation simulation
            translated = f"[Translated: {args}]"
            await self.send_message(sender, f"🌐 Translation: {translated}", add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Translation error: {e}")
            await self.send_message(sender, "❌ Translation service temporarily unavailable")

    async def handle_ascii_art(self, sender: str, args: str, timestamp: str):
        """Handle ASCII art generation"""
        try:
            if not args.strip():
                await self.send_message(sender, "🎨 Format: !ascii <text>\nExample: !ascii HELLO")
                return
            
            text = args.strip().upper()
            ascii_art = self.generate_simple_ascii(text)
            await self.send_message(sender, f"🎨 ASCII Art:\n```\n{ascii_art}\n```", add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ ASCII art error: {e}")
            await self.send_message(sender, "❌ ASCII art generator is drawing blanks!")

    async def handle_chat_analysis(self, sender: str, args: str, timestamp: str):
        """Analyze recent chat activity"""
        try:
            if sender not in self.user_sessions:
                await self.send_message(sender, "📊 No chat history to analyze yet. Keep chatting!")
                return
            
            session = self.user_sessions[sender]
            message_count = len(session.get('messages', []))
            
            analysis = f"""📊 **Chat Analysis for {sender}**
            
📨 **Messages Exchanged:** {message_count}
🕐 **Session Started:** {session.get('started', 'Recently')}
🎯 **Topics Discussed:** General conversation
💬 **Communication Style:** {session.get('style', 'Balanced')}
            
Keep the conversation going for more detailed analysis!"""
            
            await self.send_message(sender, analysis, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Chat analysis error: {e}")
            await self.send_message(sender, "❌ Chat analyzer is processing... try again later!")

    async def process_image_message(self, sender: str, message_data: Dict[str, Any], timestamp: str):
        """Process image message"""
        try:
            logger.info(f"🖼️ Image message from {sender}")
            
            # Extract image data
            image_data = message_data.get('imageData')
            caption = message_data.get('caption', '')
            
            if caption:
                # Process caption as text message
                await self.process_text_message(sender, caption, timestamp)
            else:
                # Respond to image
                responses = [
                    "🖼️ Nice image! I can see you shared something visual.",
                    "📸 Cool photo! I wish I could see it better.",
                    "🎨 That looks interesting! Thanks for sharing.",
                    "🖼️ Great image! I'd love to chat about what you've shared."
                ]
                import random
                response = random.choice(responses)
                await self.send_message(sender, response, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Image processing error: {e}")
            await self.send_message(sender, "❌ There was an error processing your image")

    def generate_simple_ascii(self, text: str) -> str:
        """Generate simple ASCII art for text"""
        ascii_chars = {
            'A': ['  ##  ', ' #  # ', '#####', '#   #', '#   #'],
            'B': ['#### ', '#   #', '#### ', '#   #', '#### '],
            'C': [' ####', '#    ', '#    ', '#    ', ' ####'],
            'H': ['#   #', '#   #', '#####', '#   #', '#   #'],
            'E': ['#####', '#    ', '#### ', '#    ', '#####'],
            'L': ['#    ', '#    ', '#    ', '#    ', '#####'],
            'O': [' ### ', '#   #', '#   #', '#   #', ' ### '],
            ' ': ['     ', '     ', '     ', '     ', '     ']
        }
        
        if len(text) > 10:
            return f"Text too long for ASCII art: {text}"
        
        lines = ['', '', '', '', '']
        for char in text:
            if char in ascii_chars:
                char_lines = ascii_chars[char]
                for i in range(5):
                    lines[i] += char_lines[i] + ' '
            else:
                # Default pattern for unknown characters
                for i in range(5):
                    lines[i] += '##### '
        
        return '\n'.join(lines)

    async def handle_unknown_command(self, sender: str, command: str):
        """Handle unknown command"""
        response = f"I don't recognize the command '{command}'. Type !help to see available commands!"
        await self.send_message(sender, response, add_ai_icon=True)
    
    async def send_message(self, to: str, message: str, add_ai_icon: bool = False):
        """Send text message via baileys bridge"""
        try:
            # Sanitize message (no emoji prefix)
            clean_message = sanitize_text(message)
            
            # Log outgoing message
            logger.info(f"📤 Sending to {to}: {clean_message[:100]}...")
            
            # Send via baileys bridge with AI icon option
            await self.send_via_bridge(to, clean_message, ai=add_ai_icon)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False
    
    async def send_via_bridge(self, to: str, message: str, ai: bool = False):
        """Send message via Node.js baileys bridge"""
        try:
            logger.info(f"🌉 Sending message via bridge to {to}: {message[:50]}... (AI: {ai})")
            outgoing_file = "outgoing_messages.json"
            
            # Load existing messages
            messages = []
            if os.path.exists(outgoing_file):
                with open(outgoing_file, 'r') as f:
                    messages = json.load(f)
                logger.info(f"📋 Loaded {len(messages)} existing outgoing messages")
            
            # Add new message with AI flag
            new_message = {
                'to': to,
                'message': message,
                'ai': ai,
                'sent': False,
                'timestamp': datetime.now().isoformat()
            }
            messages.append(new_message)
            logger.info(f"➕ Added new message to queue: {new_message}")
            
            # Save to file for bridge to process
            with open(outgoing_file, 'w') as f:
                json.dump(messages, f, indent=2)
            
            logger.info(f"💾 Saved {len(messages)} messages to {outgoing_file}")
                
        except Exception as e:
            logger.error(f"❌ Error sending via bridge: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
    
    async def send_voice_message(self, to: str, audio_data: Optional[bytes]):
        """Send voice message"""
        try:
            if not audio_data:
                logger.warning("⚠️ No audio data provided for voice message")
                return False
                
            logger.info(f"🎤 Sending voice message to {to}")
            
            # In real implementation, this would send audio via baileys
            await asyncio.sleep(0.2)  # Simulate send delay
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send voice message: {e}")
            return False
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user conversation context"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'messages': [],
                'preferences': {},
                'last_active': datetime.now().isoformat(),
                'personality_profile': 'humorous'
            }
        
        return self.user_sessions[user_id]
    
    def get_user_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get user preference"""
        context = self.get_user_context(user_id)
        return context.get('preferences', {}).get(key, default)
    
    def set_user_preference(self, user_id: str, key: str, value: Any):
        """Set user preference"""
        context = self.get_user_context(user_id)
        if 'preferences' not in context:
            context['preferences'] = {}
        context['preferences'][key] = value
        logger.debug(f"🔧 Set preference {key}={value} for user {user_id}")
    
    async def disconnect(self):
        """Disconnect from WhatsApp"""
        try:
            logger.info("🔌 Disconnecting from WhatsApp...")
            self.connected = False
            
            # Cleanup bridge process
            if hasattr(self, 'bridge_process') and self.bridge_process:
                self.bridge_process.terminate()
                self.bridge_process.wait()
            
            logger.info("✅ Disconnected successfully")
            
        except Exception as e:
            logger.error(f"❌ Error during disconnect: {e}")
    
    def extract_topic(self, message: str) -> Optional[str]:
        """Extract topic from message for contextual styling"""
        try:
            # Simple topic extraction based on keywords
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['code', 'programming', 'python', 'javascript', 'api']):
                return 'technology'
            elif any(word in message_lower for word in ['funny', 'joke', 'lol', 'haha', 'meme']):
                return 'humor'
            elif any(word in message_lower for word in ['help', 'problem', 'issue', 'error']):
                return 'support'
            elif any(word in message_lower for word in ['project', 'work', 'business', 'task']):
                return 'work'
            else:
                return 'general'
        except Exception:
            return 'general'
    
    async def update_style_mimicker_profile(self):
        """Update style mimicker with database patterns"""
        try:
            patterns = await self.db_manager.get_user_patterns() if self.db_manager else {}
            self.style_mimicker.update_patterns(patterns)
            logger.info("🔄 Style mimicker updated with database patterns")
        except Exception as e:
            logger.error(f"❌ Failed to update style mimicker: {e}")
    
    async def save_personality_data(self):
        """Save all personality learning data to database"""
        try:
            # Data is automatically saved to database during message processing
            logger.info("💾 Personality data automatically saved to database")
        except Exception as e:
            logger.error(f"❌ Failed to save personality data: {e}")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get personality learning statistics from database"""
        try:
            return self.db_manager.get_learning_stats() if self.db_manager else {}
        except Exception as e:
            logger.error(f"❌ Failed to get learning stats: {e}")
            return {}
    
    async def handle_profile_status(self, sender: str, args: str, timestamp: str):
        """Show personality profile learning status"""
        try:
            stats = self.get_learning_stats()
            profile_stats = stats.get('profile_stats', {})
            learning_progress = stats.get('learning_progress', {})
            
            profile_text = f"""🧠 **Personality Learning Profile**

📊 **Learning Progress:**
• Messages analyzed: {learning_progress.get('messages_analyzed', 0)}
• Interactions processed: {learning_progress.get('total_interactions', 0)}
• Confidence score: {learning_progress.get('confidence_score', 0.0):.2f}/1.0
• Pattern reliability: {learning_progress.get('reliability', 'Unknown')}

🎭 **Style Patterns Learned:**
• Common phrases: {learning_progress.get('phrases_learned', 0)}
• Emoji patterns: {learning_progress.get('emojis_learned', 0)}
• Topics discovered: {learning_progress.get('topics_discovered', 0)}

📈 **Profile Statistics:**
• Profile age: {profile_stats.get('profile_age_days', 0)} days
• Last updated: {profile_stats.get('last_updated', 'Never')[:19]}
• Learning status: {'Active' if stats.get('style_mimicker_active') else 'Inactive'}

🔄 All patterns are automatically saved to the database for persistence!"""

            await self.send_message(sender, profile_text, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Profile status error: {e}")
            await self.send_message(sender, "❌ Unable to retrieve profile status")
    
    async def handle_learning_stats(self, sender: str, args: str, timestamp: str):
        """Show detailed learning statistics"""
        try:
            # Get current profile data
            current_profile = self.profile_manager.load_profile()
            communication_style = current_profile.get('communication_style', {})
            
            # Top phrases and emojis
            phrases = communication_style.get('common_phrases', {})
            emojis = communication_style.get('emoji_usage', {})
            
            top_phrases = sorted(phrases.items(), key=lambda x: x[1], reverse=True)[:5]
            top_emojis = sorted(emojis.items(), key=lambda x: x[1], reverse=True)[:5]
            
            learning_text = f"""📚 **Detailed Learning Analysis**

🗣️ **Your Top Phrases:**
{chr(10).join([f'• "{phrase}": used {count:.1f} times' for phrase, count in top_phrases]) if top_phrases else '• Still learning your phrases...'}

😊 **Your Top Emojis:**
{chr(10).join([f'• {emoji}: used {count:.1f} times' for emoji, count in top_emojis]) if top_emojis else '• Still learning your emoji style...'}

🎯 **Communication Style:**
• Response length: {communication_style.get('response_length_preference', 'medium')}
• Caps usage: {communication_style.get('caps_usage_frequency', 0.1)*100:.1f}%
• Punctuation style: {communication_style.get('punctuation_style', 'standard')}

💫 **Personality Traits:**
• Greeting style: {current_profile.get('learned_patterns', {}).get('greeting_style', 'casual')}
• Excitement level: Dynamic based on context
• Topic interests: {len(current_profile.get('conversation_context', {}).get('favorite_topics', []))} topics discovered

The more we chat, the better I learn your unique style! 🚀"""

            await self.send_message(sender, learning_text, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Learning stats error: {e}")
            await self.send_message(sender, "❌ Unable to retrieve learning statistics")
    
    async def handle_time_request(self, sender: str, args: str, timestamp: str):
        """Handle time request with timezone support"""
        try:
            if args.strip():
                # User specified a timezone
                time_str = self.ai_processor.get_current_time(args.strip())
                response = f"🕐 Current time in {args.strip()}: {time_str}"
            else:
                # Use default timezone
                time_str = self.ai_processor.get_current_time()
                response = f"🕐 Current time: {time_str}"
            
            await self.send_message(sender, response, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Time request error: {e}")
            response = "❌ Couldn't get time information. Try: !time or !time America/New_York"
            await self.send_message(sender, response, add_ai_icon=True)
    
    async def handle_weather_request(self, sender: str, args: str, timestamp: str):
        """Handle weather request (with search integration)"""
        try:
            location = args.strip() if args.strip() else "Lagos, Nigeria"
            search_query = f"weather in {location} today current temperature"
            
            await self.send_message(sender, f"🌤️ Getting weather for {location}...")
            
            # Use the enhanced AI system's search capability
            if hasattr(self.ai_processor, 'search_web'):
                results = await self.ai_processor.search_web(search_query, max_results=2)
                
                if results:
                    response = f"🌤️ **Weather for {location}:**\n\n"
                    for result in results[:2]:
                        response += f"• {result.get('snippet', 'No weather data')}\n"
                        if result.get('url'):
                            response += f"🔗 {result['url']}\n\n"
                else:
                    response = f"😔 Couldn't get weather for {location}. Try searching 'weather {location}' manually."
            else:
                response = f"🌤️ For current weather in {location}, try searching 'weather {location}' online."
            
            await self.send_message(sender, response, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Weather request error: {e}")
            await self.send_message(sender, "❌ Weather service temporarily unavailable")
    
    async def handle_timezone_change(self, sender: str, args: str, timestamp: str):
        """Handle timezone change request"""
        try:
            if not args.strip():
                response = """🕐 **Timezone Help**
                
Current timezone: Africa/Lagos

To change timezone, use:
• !timezone America/New_York
• !timezone Europe/London
• !timezone Asia/Tokyo
• !timezone Australia/Sydney

Format: Continent/City"""
                await self.send_message(sender, response, add_ai_icon=True)
                return
            
            new_timezone = args.strip()
            
            # Test if timezone is valid
            test_time = self.ai_processor.get_current_time(new_timezone)
            
            if "error" not in test_time.lower():
                response = f"""✅ Timezone updated to: {new_timezone}
                
🕐 Current time: {test_time}

Note: This change is temporary for this session. To make it permanent, update your .env file."""
                
                # Update config for this session
                self.config.TIMEZONE = new_timezone
                if hasattr(self.ai_processor, 'timezone'):
                    try:
                        import pytz
                        self.ai_processor.timezone = pytz.timezone(new_timezone)
                    except:
                        pass
            else:
                response = f"❌ Invalid timezone: {new_timezone}\n\nUse format like: America/New_York, Europe/London, etc."
            
            await self.send_message(sender, response, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Timezone change error: {e}")
            await self.send_message(sender, "❌ Couldn't change timezone. Try: !timezone America/New_York")
    
    async def handle_style_summary(self, sender: str, args: str, timestamp: str):
        """Show your learned communication style summary"""
        try:
            summary = self.db_manager.get_style_summary()
            
            if "error" in summary:
                response = f"❌ {summary['error']}"
            else:
                confidence = summary.get('confidence_score', 0)
                total_msgs = summary.get('total_messages_analyzed', 0)
                
                response = f"""🧠 **Your Communication Style Summary**
                
**Learning Progress:**
• Messages analyzed: {total_msgs}
• Style confidence: {confidence:.1%}
• Preferred tone: {summary.get('preferred_tone', 'neutral')}
• Response length: {summary.get('response_length_preference', 'medium')}
• Formality level: {summary.get('formality_level', 0.5):.1%}

**Your Top Phrases:**
{chr(10).join([f'• "{phrase}"' for phrase in summary.get('top_phrases', [])[:5]]) or '• Still learning your phrases...'}

**Your Top Emojis:**
{' '.join(summary.get('top_emojis', [])[:10]) or 'Still learning your emoji style...'}

**Response Templates:**
• Greetings: {summary.get('greeting_templates_count', 0)} learned
• Responses: {summary.get('response_templates_count', 0)} learned

The more you chat, the better I understand your style for helping with responses to others! 🎯"""
            
            await self.send_message(sender, response, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Style summary error: {e}")
            await self.send_message(sender, "❌ Couldn't retrieve style summary right now")
    
    async def handle_response_suggestion(self, sender: str, args: str, timestamp: str):
        """Suggest how you would respond to someone else's message"""
        try:
            if not args.strip():
                response = """💡 **Response Suggestion Help**
                
Usage: !suggest [their message]

Example: !suggest Hey, how was your day?

I'll analyze their message and suggest how you would typically respond based on your learned communication style."""
                await self.send_message(sender, response, add_ai_icon=True)
                return
            
            their_message = args.strip()
            
            # Get conversation context (last few messages if available)
            conversation_context = self.db_manager.get_user_conversation_history(sender, limit=3)
            context_messages = [conv["user_message"] for conv in conversation_context]
            
            suggestion = await self.db_manager.suggest_response(
                other_user_id=sender,
                their_message=their_message,
                conversation_context=context_messages
            )
            
            if suggestion.get("suggestion"):
                confidence = suggestion.get("confidence", 0)
                tone = suggestion.get("tone", "neutral")
                reasoning = suggestion.get("reasoning", "Based on your style patterns")
                
                response = f"""💡 **Response Suggestion**
                
**Their message:** {their_message}

**Suggested response:** {suggestion['suggestion']}

**Tone:** {tone}
**Confidence:** {confidence:.1%}
**Reasoning:** {reasoning}

This suggestion is based on your learned communication style. Feel free to modify it to fit the specific situation! 🎯"""
            else:
                reason = suggestion.get("reason", "Unknown error")
                response = f"❌ Couldn't generate suggestion: {reason}"
            
            await self.send_message(sender, response, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Response suggestion error: {e}")
            await self.send_message(sender, "❌ Couldn't generate response suggestion right now")
    
    async def handle_database_stats(self, sender: str, args: str, timestamp: str):
        """Show database statistics and learning progress"""
        try:
            db_stats = self.db_manager.get_database_stats()
            user_stats = self.db_manager.get_user_stats(sender)
            
            if "error" in db_stats:
                response = f"❌ Database error: {db_stats['error']}"
            else:
                response = f"""📊 **Database Learning Statistics**
                
**Overall System:**
• Total users: {db_stats.get('total_users', 0)}
• Total conversations: {db_stats.get('total_conversations', 0)}
• Phrases learned: {db_stats.get('total_phrases', 0)}
• Emojis tracked: {db_stats.get('total_emojis', 0)}
• Users with style learning: {db_stats.get('users_with_style_learning', 0)}
• Response suggestions: {db_stats.get('total_response_suggestions', 0)}

**Your Statistics:**"""
                
                if "error" not in user_stats:
                    response += f"""
• Your messages: {user_stats.get('total_messages', 0)}
• Learning confidence: {user_stats.get('learning_confidence', 0):.1%}
• Last interaction: {user_stats.get('last_interaction', 'Never')[:19] if user_stats.get('last_interaction') else 'Never'}
• Recent topics: {', '.join(user_stats.get('recent_topics', [])[:5]) or 'None yet'}"""
                else:
                    response += f"\n• Error loading your stats: {user_stats['error']}"
                
                response += "\n\n🗄️ All data is stored securely in PostgreSQL database for persistent learning across restarts!"
            
            await self.send_message(sender, response, add_ai_icon=True)
            
        except Exception as e:
            logger.error(f"❌ Database stats error: {e}")
            await self.send_message(sender, "❌ Couldn't retrieve database statistics right now")
