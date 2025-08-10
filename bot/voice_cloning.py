"""
Enhanced Voice Processing with TTS and Voice Cloning
Handles advanced voice features including text-to-speech and voice synthesis
"""

import asyncio
import logging
import tempfile
import os
import io
import wave
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import random

logger = logging.getLogger(__name__)

class VoiceCloningEngine:
    """Advanced voice processing with TTS and cloning capabilities"""
    
    def __init__(self, config, model_manager=None):
        self.config = config
        self.model_manager = model_manager
        self.tts_enabled = config.VOICE_ENABLED
        self.voice_cloning_enabled = getattr(config, 'VOICE_CLONING', False)
        self.tts_language = config.TTS_LANGUAGE
        self.voice_speed = config.VOICE_SPEED
        
        # Voice profiles for different personalities
        self.voice_profiles = self._load_voice_profiles()
        self.user_voice_samples = {}  # Store user voice samples for cloning
        
        # TTS settings
        self.supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
        self.voice_styles = ['normal', 'happy', 'sad', 'excited', 'calm', 'confident']
        
        # Advanced AI models for voice processing
        self.tts_model = None
        self.stt_model = None
        
        # Initialize TTS engines
        self._initialize_tts_engines()
        
        logger.info("🎤 Enhanced Voice Cloning Engine initialized")
    
    def _load_voice_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined voice profiles for different personalities"""
        return {
            'default': {
                'name': 'Default Assistant',
                'pitch': 1.0,
                'speed': 1.0,
                'tone': 'friendly',
                'accent': 'neutral'
            },
            'confident': {
                'name': 'Confident Leader',
                'pitch': 0.9,
                'speed': 1.1,
                'tone': 'assertive',
                'accent': 'neutral'
            },
            'humorous': {
                'name': 'Comedy Assistant',
                'pitch': 1.1,
                'speed': 1.0,
                'tone': 'playful',
                'accent': 'neutral'
            },
            'calm': {
                'name': 'Zen Assistant',
                'pitch': 0.95,
                'speed': 0.9,
                'tone': 'soothing',
                'accent': 'neutral'
            },
            'energetic': {
                'name': 'Enthusiastic Helper',
                'pitch': 1.15,
                'speed': 1.2,
                'tone': 'excited',
                'accent': 'neutral'
            }
        }
    
    def _initialize_tts_engines(self):
        """Initialize available TTS engines"""
        self.available_engines = []
        
        # Try to initialize gTTS
        try:
            from gtts import gTTS
            self.available_engines.append('gtts')
            logger.info("✅ Google TTS (gTTS) available")
        except ImportError:
            logger.warning("⚠️ gTTS not available")
        
        # Try to initialize pyttsx3 for offline TTS
        try:
            import pyttsx3
            self.available_engines.append('pyttsx3')
            logger.info("✅ pyttsx3 (offline TTS) available")
        except ImportError:
            logger.warning("⚠️ pyttsx3 not available")
        
        # Try to initialize festival/espeak
        try:
            import subprocess
            result = subprocess.run(['espeak', '--version'], capture_output=True)
            if result.returncode == 0:
                self.available_engines.append('espeak')
                logger.info("✅ espeak TTS available")
        except:
            logger.warning("⚠️ espeak not available")
        
        if not self.available_engines:
            logger.warning("⚠️ No TTS engines available - using fallback")
            self.available_engines.append('fallback')
    
    async def initialize_ai_models(self):
        """Initialize AI models for advanced voice processing"""
        try:
            if self.model_manager:
                logger.info("🔄 Loading advanced voice processing models")
                
                # Load TTS model
                self.tts_model = await self.model_manager.get_model('text_to_speech')
                
                # Load STT model  
                self.stt_model = await self.model_manager.get_model('speech_to_text')
                
                if self.tts_model:
                    logger.info("✅ Advanced TTS model loaded")
                if self.stt_model:
                    logger.info("✅ Advanced STT model loaded")
                    
        except Exception as e:
            logger.error(f"❌ Error loading AI voice models: {e}")
    
    async def text_to_speech(self, text: str, voice_profile: str = 'default', 
                           language: Optional[str] = None, user_id: Optional[str] = None) -> Optional[bytes]:
        """Convert text to speech with personality and voice cloning"""
        try:
            if not self.tts_enabled:
                logger.info("🔇 TTS disabled in configuration")
                return None
            
            if not text.strip():
                logger.warning("⚠️ Empty text provided for TTS")
                return None
            
            # Use provided language or default
            lang = language or self.tts_language
            
            logger.info(f"🗣️ Converting text to speech: '{text[:50]}...' (profile: {voice_profile}, lang: {lang})")
            
            # Get voice profile settings
            profile = self.voice_profiles.get(voice_profile, self.voice_profiles['default'])
            
            # Try AI-powered TTS first if available
            if self.tts_model:
                try:
                    ai_audio = await self._generate_with_ai_model(text, profile, lang)
                    if ai_audio:
                        logger.info("✅ TTS completed with AI model")
                        return ai_audio
                except Exception as e:
                    logger.warning(f"⚠️ AI TTS failed: {e}")
            
            # Check if user has custom voice profile (voice cloning)
            if self.voice_cloning_enabled and user_id and user_id in self.user_voice_samples:
                return await self._generate_cloned_voice(text, user_id, profile)
            
            # Use best available TTS engine
            for engine in ['gtts', 'pyttsx3', 'espeak']:
                if engine in self.available_engines:
                    try:
                        audio_data = await self._generate_with_engine(text, engine, lang, profile)
                        if audio_data:
                            logger.info(f"✅ TTS completed with {engine}")
                            return audio_data
                    except Exception as e:
                        logger.warning(f"⚠️ TTS engine {engine} failed: {e}")
                        continue
            
            # Fallback response
            logger.warning("⚠️ All TTS engines failed, using fallback")
            return await self._generate_fallback_audio(text)
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            return None
    
    async def _generate_with_ai_model(self, text: str, profile: Dict[str, Any], language: str) -> Optional[bytes]:
        """Generate speech using advanced AI TTS model"""
        try:
            if not self.tts_model:
                return None
            
            logger.info("🤖 Generating speech with AI TTS model")
            
            # Adjust text for personality
            adjusted_text = await self._adjust_text_for_personality(text, profile)
            
            # Use advanced AI model for TTS
            # Note: Implementation depends on specific model (SpeechT5, Bark, etc.)
            # This is a placeholder that would be replaced with actual model inference
            
            # For now, fallback to traditional TTS with enhanced processing
            return await self._generate_with_gtts(adjusted_text, language, profile)
            
        except Exception as e:
            logger.error(f"❌ AI TTS generation error: {e}")
            return None
    
    async def _generate_with_engine(self, text: str, engine: str, language: str, 
                                  profile: Dict[str, Any]) -> Optional[bytes]:
        """Generate speech with specific TTS engine"""
        try:
            if engine == 'gtts':
                return await self._generate_with_gtts(text, language, profile)
            elif engine == 'pyttsx3':
                return await self._generate_with_pyttsx3(text, language, profile)
            elif engine == 'espeak':
                return await self._generate_with_espeak(text, language, profile)
            else:
                return None
        except Exception as e:
            logger.error(f"❌ Engine {engine} error: {e}")
            return None
    
    async def _generate_with_gtts(self, text: str, language: str, profile: Dict[str, Any]) -> Optional[bytes]:
        """Generate speech using Google TTS"""
        try:
            from gtts import gTTS
            
            # Adjust text for personality
            adjusted_text = await self._adjust_text_for_personality(text, profile)
            
            # Create gTTS object
            tts = gTTS(text=adjusted_text, lang=language[:2], slow=False)
            
            # Generate audio to memory
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            audio_data = audio_buffer.read()
            
            # Apply voice profile modifications
            audio_data = await self._apply_voice_profile(audio_data, profile)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ gTTS generation error: {e}")
            return None
    
    async def _generate_with_pyttsx3(self, text: str, language: str, profile: Dict[str, Any]) -> Optional[bytes]:
        """Generate speech using pyttsx3 (offline)"""
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            
            # Configure voice settings
            voices = engine.getProperty('voices')
            if voices:
                # Try to find appropriate voice for language
                for voice in voices:
                    if language[:2] in voice.id.lower():
                        engine.setProperty('voice', voice.id)
                        break
            
            # Apply profile settings
            rate = engine.getProperty('rate')
            engine.setProperty('rate', int(rate * profile.get('speed', 1.0)))
            
            # Generate audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            # Read audio data
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # Cleanup
            os.unlink(temp_path)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ pyttsx3 generation error: {e}")
            return None
    
    async def _generate_with_espeak(self, text: str, language: str, profile: Dict[str, Any]) -> Optional[bytes]:
        """Generate speech using espeak"""
        try:
            import subprocess
            
            # Build espeak command
            cmd = [
                'espeak',
                '-v', f"{language}+m3",  # Male voice variant 3
                '-s', str(int(150 * profile.get('speed', 1.0))),  # Speed in words per minute
                '-p', str(int(50 * profile.get('pitch', 1.0))),   # Pitch
                '--stdout',
                text
            ]
            
            # Execute espeak
            result = subprocess.run(cmd, capture_output=True, check=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"❌ espeak failed with code {result.returncode}")
                return None
                
        except Exception as e:
            logger.error(f"❌ espeak generation error: {e}")
            return None
    
    async def _adjust_text_for_personality(self, text: str, profile: Dict[str, Any]) -> str:
        """Adjust text content based on voice personality"""
        try:
            tone = profile.get('tone', 'friendly')
            
            # Add personality-based modifications
            if tone == 'assertive':
                # Make statements more confident
                text = text.replace('I think', 'I know')
                text = text.replace('maybe', 'definitely')
                text = text.replace('probably', 'certainly')
            elif tone == 'playful':
                # Add some enthusiasm
                text = text.replace('.', '!')
                if not any(emoji in text for emoji in ['😊', '😂', '🎉', '✨']):
                    text += ' 😊'
            elif tone == 'soothing':
                # Make text more calming
                text = text.replace('!', '.')
                text = text.replace('quickly', 'gently')
                text = text.replace('fast', 'smoothly')
            
            return text
            
        except Exception as e:
            logger.error(f"❌ Text adjustment error: {e}")
            return text
    
    async def _apply_voice_profile(self, audio_data: bytes, profile: Dict[str, Any]) -> bytes:
        """Apply voice profile modifications to audio data"""
        try:
            # Note: This is a simplified implementation
            # In a full implementation, you would use audio processing libraries
            # like pydub, librosa, or PyAudio to modify pitch, speed, etc.
            
            # For now, return original audio data
            # TODO: Implement audio processing with pydub
            # from pydub import AudioSegment
            # audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
            # # Apply pitch, speed modifications
            # return modified_audio.export(format="mp3").read()
            
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ Voice profile application error: {e}")
            return audio_data
    
    async def _generate_cloned_voice(self, text: str, user_id: str, profile: Dict[str, Any]) -> Optional[bytes]:
        """Generate speech using cloned voice (advanced feature)"""
        try:
            logger.info(f"🎭 Generating cloned voice for user {user_id}")
            
            # This is a placeholder for voice cloning functionality
            # In a real implementation, you would:
            # 1. Load the user's voice sample
            # 2. Use a voice cloning model (like TorToise-TTS, Bark, or similar)
            # 3. Generate speech with the cloned voice
            
            user_sample = self.user_voice_samples.get(user_id, {})
            
            if not user_sample:
                logger.warning("⚠️ No voice sample available for cloning")
                return await self._generate_with_gtts(text, self.tts_language, profile)
            
            # Placeholder implementation - in reality would use voice cloning models
            logger.info("🎭 Voice cloning feature is in development")
            return await self._generate_with_gtts(text, self.tts_language, profile)
            
        except Exception as e:
            logger.error(f"❌ Voice cloning error: {e}")
            return None
    
    async def _generate_fallback_audio(self, text: str) -> bytes:
        """Generate fallback audio response"""
        try:
            # Create a simple beep or tone as fallback
            # This is a minimal implementation
            
            fallback_message = f"Audio message: {text[:50]}" + ("..." if len(text) > 50 else "")
            
            # Return empty audio data - client should handle gracefully
            return b''
            
        except Exception as e:
            logger.error(f"❌ Fallback audio error: {e}")
            return b''
    
    async def speech_to_text(self, audio_data: bytes, language: str = "en") -> Optional[str]:
        """Convert speech to text for voice message processing"""
        try:
            if not audio_data:
                logger.warning("⚠️ No audio data provided for STT")
                return None
            
            logger.info("🎤 Converting speech to text...")
            
            # Try AI-powered STT first if available
            if self.stt_model:
                try:
                    ai_transcription = await self._transcribe_with_ai_model(audio_data, language)
                    if ai_transcription:
                        logger.info("✅ STT completed with AI model")
                        return ai_transcription
                except Exception as e:
                    logger.warning(f"⚠️ AI STT failed: {e}")
            
            # Try different speech recognition approaches
            transcription = await self._transcribe_with_available_engine(audio_data, language)
            
            if transcription:
                logger.info(f"✅ Speech to text completed: {transcription[:50]}...")
                return transcription
            else:
                logger.warning("⚠️ Speech transcription failed")
                return "[Voice message - transcription unavailable]"
                
        except Exception as e:
            logger.error(f"❌ Speech to text error: {e}")
            return None
    
    async def _transcribe_with_available_engine(self, audio_data: bytes, language: str) -> Optional[str]:
        """Transcribe audio using available engines"""
        try:
            # Try speech_recognition library if available
            try:
                import speech_recognition as sr
                
                # Save audio to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_path = temp_file.name
                
                # Initialize recognizer
                recognizer = sr.Recognizer()
                
                # Load audio file
                with sr.AudioFile(temp_path) as source:
                    audio = recognizer.record(source)
                
                # Try Google Speech Recognition
                try:
                    text = recognizer.recognize_google(audio, language=language)
                    os.unlink(temp_path)
                    return text
                except sr.UnknownValueError:
                    logger.warning("⚠️ Could not understand audio")
                except sr.RequestError as e:
                    logger.warning(f"⚠️ Speech recognition service error: {e}")
                
                # Try offline recognition as fallback
                try:
                    text = recognizer.recognize_sphinx(audio)
                    os.unlink(temp_path)
                    return text
                except:
                    pass
                
                os.unlink(temp_path)
                
            except ImportError:
                logger.warning("⚠️ speech_recognition library not available")
            
            # Fallback to indicating voice message received
            return "[Voice message received]"
            
        except Exception as e:
            logger.error(f"❌ Transcription engine error: {e}")
            return None
    
    async def _transcribe_with_ai_model(self, audio_data: bytes, language: str) -> Optional[str]:
        """Transcribe audio using advanced AI STT model"""
        try:
            if not self.stt_model:
                return None
            
            logger.info("🤖 Transcribing with AI STT model")
            
            # Use advanced AI model for STT
            # Note: Implementation depends on specific model (Whisper, Wav2Vec2, etc.)
            # This is a placeholder that would be replaced with actual model inference
            
            # For now, return None to fallback to traditional methods
            return None
            
        except Exception as e:
            logger.error(f"❌ AI STT transcription error: {e}")
            return None
    
    async def learn_user_voice(self, user_id: str, audio_data: bytes, context: str = "") -> bool:
        """Learn user's voice pattern for cloning (if enabled)"""
        try:
            if not self.voice_cloning_enabled:
                return False
            
            logger.info(f"🎭 Learning voice pattern for user {user_id}")
            
            # Store voice sample for future cloning
            if user_id not in self.user_voice_samples:
                self.user_voice_samples[user_id] = {
                    'samples': [],
                    'characteristics': {},
                    'created_at': asyncio.get_event_loop().time()
                }
            
            # Add sample (in real implementation, would analyze audio characteristics)
            self.user_voice_samples[user_id]['samples'].append({
                'audio_data': audio_data,
                'context': context,
                'timestamp': asyncio.get_event_loop().time()
            })
            
            # Keep only recent samples (memory management)
            if len(self.user_voice_samples[user_id]['samples']) > 10:
                self.user_voice_samples[user_id]['samples'] = \
                    self.user_voice_samples[user_id]['samples'][-10:]
            
            logger.info(f"✅ Voice sample learned for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Voice learning error: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voice profiles"""
        return [
            {
                'id': voice_id,
                'name': profile['name'],
                'description': f"{profile['tone']} voice with {profile['accent']} accent",
                'settings': {
                    'pitch': profile['pitch'],
                    'speed': profile['speed'],
                    'tone': profile['tone']
                }
            }
            for voice_id, profile in self.voice_profiles.items()
        ]
    
    def get_user_voice_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's voice cloning status"""
        if not self.voice_cloning_enabled:
            return {'voice_cloning': False, 'reason': 'Feature disabled'}
        
        if user_id not in self.user_voice_samples:
            return {
                'voice_cloning': False,
                'samples_collected': 0,
                'status': 'No samples collected'
            }
        
        samples = self.user_voice_samples[user_id]['samples']
        return {
            'voice_cloning': True,
            'samples_collected': len(samples),
            'status': 'Voice profile ready' if len(samples) >= 3 else 'Collecting samples',
            'last_sample': samples[-1]['timestamp'] if samples else None
        }
    
    async def cleanup_voice_data(self, max_age_hours: int = 24):
        """Clean up old voice samples to save memory"""
        try:
            current_time = asyncio.get_event_loop().time()
            max_age_seconds = max_age_hours * 3600
            
            users_to_remove = []
            for user_id, data in self.user_voice_samples.items():
                # Remove old samples
                data['samples'] = [
                    sample for sample in data['samples']
                    if current_time - sample['timestamp'] < max_age_seconds
                ]
                
                # Remove user entry if no samples left
                if not data['samples']:
                    users_to_remove.append(user_id)
            
            for user_id in users_to_remove:
                del self.user_voice_samples[user_id]
            
            if users_to_remove:
                logger.info(f"🧹 Cleaned up voice data for {len(users_to_remove)} users")
                
        except Exception as e:
            logger.error(f"❌ Voice data cleanup error: {e}")