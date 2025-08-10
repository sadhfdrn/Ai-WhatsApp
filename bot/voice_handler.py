"""
Voice Processing Handler
Handles speech-to-text, text-to-speech, and voice message processing
"""

import asyncio
import logging
import tempfile
import os
from typing import Optional, Dict, Any
import io

logger = logging.getLogger(__name__)

class VoiceHandler:
    """Voice processing handler for WhatsApp bot"""
    
    def __init__(self, config):
        self.config = config
        self.tts_enabled = config.VOICE_ENABLED
        self.tts_language = config.TTS_LANGUAGE
        self.voice_speed = config.VOICE_SPEED
        
        # Voice processing settings
        self.supported_formats = ['ogg', 'mp3', 'wav', 'm4a']
        self.max_audio_duration = 300  # 5 minutes
        
        # Initialize TTS engine simulation
        self.tts_initialized = False
        
        logger.info("🎤 Voice handler initialized")
    
    async def speech_to_text(self, audio_data: bytes, language: str = "en") -> Optional[str]:
        """Convert speech to text"""
        try:
            if not audio_data:
                logger.warning("⚠️ No audio data provided")
                return None
            
            logger.info("🎤 Converting speech to text...")
            
            # Simulate speech recognition processing
            await asyncio.sleep(1)  # Simulate processing time
            
            # In real implementation, use speech_recognition library:
            # import speech_recognition as sr
            # recognizer = sr.Recognizer()
            # with sr.AudioFile(audio_file) as source:
            #     audio = recognizer.record(source)
            #     text = recognizer.recognize_google(audio, language=language)
            
            # For simulation, return a placeholder
            # In production, this would return the actual transcribed text
            simulated_transcription = "[Voice message received - transcription would appear here]"
            
            logger.info(f"✅ Speech to text completed: {simulated_transcription[:50]}...")
            return simulated_transcription
            
        except Exception as e:
            logger.error(f"❌ Speech to text error: {e}")
            return None
    
    async def text_to_speech(self, text: str, language: Optional[str] = None) -> Optional[bytes]:
        """Convert text to speech"""
        try:
            if not text.strip():
                logger.warning("⚠️ No text provided for TTS")
                return None
            
            # Use configured language if not specified
            lang = language or self.tts_language
            
            logger.info(f"🔊 Converting text to speech: {text[:50]}...")
            
            # Initialize TTS if needed
            if not self.tts_initialized:
                await self.initialize_tts()
            
            # Simulate TTS processing
            await asyncio.sleep(0.5)  # Simulate processing time
            
            # In real implementation, use gtts or similar:
            # from gtts import gTTS
            # tts = gTTS(text=text, lang=lang, slow=False)
            # 
            # with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            #     tts.save(temp_file.name)
            #     with open(temp_file.name, 'rb') as audio_file:
            #         audio_data = audio_file.read()
            #     os.unlink(temp_file.name)
            #     return audio_data
            
            # For simulation, return placeholder audio data
            simulated_audio = b"[Simulated audio data would be here]"
            
            logger.info("✅ Text to speech completed")
            return simulated_audio
            
        except Exception as e:
            logger.error(f"❌ Text to speech error: {e}")
            return None
    
    async def initialize_tts(self):
        """Initialize text-to-speech engine"""
        try:
            logger.info("🔧 Initializing TTS engine...")
            
            # Simulate initialization
            await asyncio.sleep(0.3)
            
            self.tts_initialized = True
            logger.info("✅ TTS engine initialized")
            
        except Exception as e:
            logger.error(f"❌ TTS initialization error: {e}")
            self.tts_initialized = False
    
    async def process_voice_message(self, voice_data: Dict[str, Any]) -> Optional[str]:
        """Process incoming voice message"""
        try:
            # Extract audio data from WhatsApp voice message
            audio_bytes = voice_data.get('audioData')
            duration = voice_data.get('duration', 0)
            
            if not audio_bytes:
                logger.warning("⚠️ No audio data in voice message")
                return None
            
            # Check duration limits
            if duration > self.max_audio_duration:
                logger.warning(f"⚠️ Voice message too long: {duration}s (max: {self.max_audio_duration}s)")
                return "Voice message is too long. Please keep it under 5 minutes."
            
            # Convert to text
            transcription = await self.speech_to_text(audio_bytes)
            
            if transcription:
                logger.info(f"🎤 Voice message processed: {transcription[:100]}...")
                return transcription
            else:
                return "Sorry, I couldn't understand your voice message. Could you try again?"
            
        except Exception as e:
            logger.error(f"❌ Voice message processing error: {e}")
            return "There was an error processing your voice message."
    
    async def create_voice_response(self, text: str, user_preferences: Optional[Dict[str, Any]] = None) -> Optional[bytes]:
        """Create voice response with user preferences"""
        try:
            if not self.tts_enabled:
                logger.info("🔇 TTS is disabled")
                return None
            
            # Apply user preferences
            language = user_preferences.get('voice_language', self.tts_language) if user_preferences else self.tts_language
            speed = user_preferences.get('voice_speed', self.voice_speed) if user_preferences else self.voice_speed
            
            # Clean text for speech
            clean_text = await self.prepare_text_for_speech(text)
            
            # Generate audio
            audio_data = await self.text_to_speech(clean_text, language)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ Voice response creation error: {e}")
            return None
    
    async def prepare_text_for_speech(self, text: str) -> str:
        """Prepare text for better speech synthesis"""
        try:
            # Remove or replace elements that don't work well with TTS
            clean_text = text
            
            # Remove emoji and special characters that don't speak well
            import re
            clean_text = re.sub(r'[🤖😄😅😂🎉⚡💪👏🔥🚀⭐🌟💡🎯📈🔍]', '', clean_text)
            
            # Replace common abbreviations
            replacements = {
                'AI': 'Artificial Intelligence',
                'BTW': 'by the way',
                'FYI': 'for your information',
                'ASAP': 'as soon as possible',
                'LOL': 'laugh out loud',
                'OMG': 'oh my god',
                'TBH': 'to be honest',
                'IRL': 'in real life',
                'IMHO': 'in my humble opinion'
            }
            
            for abbrev, full_form in replacements.items():
                clean_text = clean_text.replace(abbrev, full_form)
            
            # Handle URLs
            clean_text = re.sub(r'https?://[^\s]+', 'link', clean_text)
            
            # Handle markdown-like formatting
            clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)  # Bold
            clean_text = re.sub(r'_(.*?)_', r'\1', clean_text)  # Italic
            
            # Clean up extra whitespace
            clean_text = ' '.join(clean_text.split())
            
            # Limit length for TTS
            if len(clean_text) > 500:
                clean_text = clean_text[:497] + "..."
            
            return clean_text
            
        except Exception as e:
            logger.error(f"❌ Text preparation error: {e}")
            return text  # Return original if cleaning fails
    
    async def get_voice_settings_for_user(self, user_id: str) -> Dict[str, Any]:
        """Get voice settings for specific user"""
        # In real implementation, this would load from user preferences database
        default_settings = {
            'enabled': self.tts_enabled,
            'language': self.tts_language,
            'speed': self.voice_speed,
            'auto_voice_replies': False,
            'voice_only_mode': False
        }
        
        return default_settings
    
    async def detect_audio_format(self, audio_data: bytes) -> str:
        """Detect audio format from data"""
        try:
            # Simple format detection based on file headers
            if audio_data.startswith(b'OggS'):
                return 'ogg'
            elif audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb'):
                return 'mp3'
            elif audio_data.startswith(b'RIFF'):
                return 'wav'
            elif audio_data.startswith(b'\x00\x00\x00 ftypM4A'):
                return 'm4a'
            else:
                return 'unknown'
                
        except Exception as e:
            logger.error(f"❌ Audio format detection error: {e}")
            return 'unknown'
    
    def is_voice_enabled_for_user(self, user_id: str) -> bool:
        """Check if voice is enabled for specific user"""
        # In real implementation, check user preferences
        return self.tts_enabled
    
    async def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        try:
            # Clean up any temporary files created during processing
            temp_dir = tempfile.gettempdir()
            for filename in os.listdir(temp_dir):
                if filename.startswith('tts_') and filename.endswith(('.mp3', '.wav', '.ogg')):
                    filepath = os.path.join(temp_dir, filename)
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass  # File might be in use
                        
        except Exception as e:
            logger.error(f"❌ Temp file cleanup error: {e}")
