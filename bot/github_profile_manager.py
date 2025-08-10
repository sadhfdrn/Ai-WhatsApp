"""
GitHub Profile Manager
Handles persistent personality learning system that saves data directly to GitHub repository
"""

import os
import json
import logging
import subprocess
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)

class GitHubProfileManager:
    """Manages personality profiles with GitHub repository persistence"""
    
    def __init__(self, repo_path=".", branch="main"):
        self.repo_path = Path(repo_path)
        self.branch = branch
        self.data_dir = self.repo_path / "data"
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        # Profile file paths
        self.profile_file = self.data_dir / "my_profile.json"
        self.conversation_file = self.data_dir / "conversation_memory.json"
        self.patterns_file = self.data_dir / "learned_patterns.json"
        self.voice_file = self.data_dir / "voice_characteristics.json"
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)
        
        # Configure git
        self._configure_git()
        
        logger.info("🗂️ GitHub Profile Manager initialized")
    
    def _configure_git(self):
        """Configure git credentials using GitHub token"""
        try:
            # Set git configuration
            subprocess.run(['git', 'config', '--global', 'user.name', 'WhatsApp AI Bot'], 
                          cwd=self.repo_path, check=True)
            subprocess.run(['git', 'config', '--global', 'user.email', 'bot@github.com'], 
                          cwd=self.repo_path, check=True)
            
            # Set up authentication if token is available
            if self.github_token:
                repo_url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], 
                                                  cwd=self.repo_path, text=True).strip()
                if repo_url.startswith('https://'):
                    # Update remote URL to include token
                    auth_url = repo_url.replace('https://', f'https://{self.github_token}@')
                    subprocess.run(['git', 'remote', 'set-url', 'origin', auth_url], 
                                  cwd=self.repo_path, check=True)
                
            logger.info("✅ Git configured successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to configure git: {e}")
        except Exception as e:
            logger.error(f"❌ Git configuration error: {e}")
    
    def load_profile(self) -> Dict[str, Any]:
        """Load existing personality profile from repository"""
        try:
            if self.profile_file.exists():
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    logger.info("✅ Loaded existing personality profile")
                    return profile
            else:
                logger.info("📝 No existing profile found, creating default")
                return self.create_default_profile()
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Profile file corrupted, creating new: {e}")
            return self.create_default_profile()
        except Exception as e:
            logger.error(f"❌ Error loading profile: {e}")
            return self.create_default_profile()
    
    def save_profile(self, profile_data: Dict[str, Any]):
        """Save updated personality profile and commit to repository"""
        try:
            # Update timestamp
            profile_data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
            
            # Save to file
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            # Commit changes
            self.commit_changes(f"Update personality profile - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            logger.info("✅ Personality profile saved and committed")
            
        except Exception as e:
            logger.error(f"❌ Failed to save profile: {e}")
    
    def save_conversation_memory(self, conversations: List[Dict[str, Any]]):
        """Save recent conversation history (limit to last 100)"""
        try:
            # Limit to last 100 conversations for file size management
            limited_conversations = conversations[-100:] if len(conversations) > 100 else conversations
            
            memory_data = {
                "last_updated": datetime.utcnow().isoformat() + 'Z',
                "conversation_count": len(limited_conversations),
                "conversations": limited_conversations
            }
            
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            
            self.commit_changes(f"Update conversation memory - {len(limited_conversations)} conversations")
            
            logger.info(f"✅ Saved {len(limited_conversations)} conversations to memory")
            
        except Exception as e:
            logger.error(f"❌ Failed to save conversation memory: {e}")
    
    def save_learned_patterns(self, patterns_data: Dict[str, Any]):
        """Save learned communication patterns"""
        try:
            patterns_data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
            
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False)
            
            self.commit_changes(f"Update learned patterns - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            logger.info("✅ Learned patterns saved and committed")
            
        except Exception as e:
            logger.error(f"❌ Failed to save learned patterns: {e}")
    
    def load_conversation_memory(self) -> List[Dict[str, Any]]:
        """Load conversation memory from repository"""
        try:
            if self.conversation_file.exists():
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                    return memory_data.get('conversations', [])
            return []
        except Exception as e:
            logger.error(f"❌ Failed to load conversation memory: {e}")
            return []
    
    def commit_changes(self, message: str):
        """Add, commit, and push changes to repository"""
        try:
            # Add all files in data directory
            subprocess.run(['git', 'add', 'data/'], cwd=self.repo_path, check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                                  cwd=self.repo_path, capture_output=True)
            
            if result.returncode != 0:  # There are changes
                # Commit changes
                subprocess.run(['git', 'commit', '-m', message], 
                              cwd=self.repo_path, check=True)
                
                # Push to repository
                subprocess.run(['git', 'push', 'origin', self.branch], 
                              cwd=self.repo_path, check=True)
                
                logger.info(f"✅ Committed and pushed: {message}")
            else:
                logger.info("ℹ️ No changes to commit")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git operation failed: {e}")
        except Exception as e:
            logger.error(f"❌ Commit error: {e}")
    
    def create_default_profile(self) -> Dict[str, Any]:
        """Generate initial personality profile structure"""
        default_profile = {
            "user_id": "owner",
            "created": datetime.utcnow().isoformat() + 'Z',
            "last_updated": datetime.utcnow().isoformat() + 'Z',
            "communication_style": {
                "tone": "casual, tech-savvy, direct",
                "common_phrases": {},
                "emoji_usage": {},
                "response_length_preference": "medium",
                "punctuation_style": "standard",
                "caps_usage_frequency": 0.1
            },
            "learned_patterns": {
                "greeting_style": "hey there",
                "goodbye_style": "see you later",
                "agreement_phrases": ["yes", "absolutely", "definitely", "for sure"],
                "disagreement_style": "not really",
                "excitement_indicators": ["wow", "amazing", "awesome"],
                "question_patterns": "direct_questions",
                "topic_transitions": "smooth_transitions"
            },
            "conversation_context": {
                "favorite_topics": [],
                "preferred_times": [],
                "mood_patterns": {
                    "excited": "enthusiastic_responses",
                    "casual": "relaxed_tone",
                    "focused": "professional_language"
                },
                "response_triggers": {}
            },
            "voice_characteristics": {
                "pace": "medium",
                "tone_preference": "friendly",
                "accent_notes": "neutral",
                "pause_patterns": "natural_pauses"
            },
            "learning_metadata": {
                "total_messages_analyzed": 0,
                "last_learning_session": datetime.utcnow().isoformat() + 'Z',
                "confidence_score": 0.0,
                "pattern_reliability": "initializing"
            }
        }
        
        # Save the default profile
        self.save_profile(default_profile)
        
        return default_profile
    
    def backup_profile(self):
        """Create a backup of current profile"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.data_dir / f"profile_backup_{timestamp}.json"
            
            if self.profile_file.exists():
                with open(self.profile_file, 'r', encoding='utf-8') as src:
                    profile_data = json.load(src)
                
                with open(backup_file, 'w', encoding='utf-8') as dst:
                    json.dump(profile_data, dst, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ Profile backed up to {backup_file}")
                
        except Exception as e:
            logger.error(f"❌ Failed to backup profile: {e}")
    
    def get_profile_stats(self) -> Dict[str, Any]:
        """Get statistics about the current profile"""
        try:
            profile = self.load_profile()
            metadata = profile.get('learning_metadata', {})
            
            return {
                "total_messages": metadata.get('total_messages_analyzed', 0),
                "confidence_score": metadata.get('confidence_score', 0.0),
                "last_updated": profile.get('last_updated', 'Never'),
                "learning_reliability": metadata.get('pattern_reliability', 'Unknown'),
                "profile_age_days": self._calculate_profile_age(profile.get('created')),
                "common_phrases_count": len(profile.get('communication_style', {}).get('common_phrases', {})),
                "emoji_count": len(profile.get('communication_style', {}).get('emoji_usage', {}))
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get profile stats: {e}")
            return {}
    
    def _calculate_profile_age(self, created_timestamp: str) -> int:
        """Calculate profile age in days"""
        try:
            if created_timestamp:
                created_date = datetime.fromisoformat(created_timestamp.replace('Z', '+00:00'))
                age = datetime.now() - created_date.replace(tzinfo=None)
                return age.days
            return 0
        except Exception:
            return 0