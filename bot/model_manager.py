"""
Smart Model Manager for Environment-Optimized AI Model Loading
Handles progressive download/caching for GitHub Actions and streaming for cloud deployment
"""

import os
import json
import logging
import asyncio
import hashlib
import time
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import gc
import psutil

logger = logging.getLogger(__name__)

class SmartModelManager:
    """Environment-aware model management with progressive loading and streaming"""
    
    def __init__(self, config):
        self.config = config
        self.environment = self._detect_environment()
        self.models = {}
        self.model_configs = self._load_model_configs()
        self.cache_dir = self._setup_cache_directory()
        
        # Performance tracking
        self.load_times = {}
        self.memory_usage = {}
        
        logger.info(f"🧠 Smart Model Manager initialized for {self.environment} environment")
    
    def _detect_environment(self) -> str:
        """Detect deployment environment (GitHub Actions, Replit, etc.)"""
        if os.getenv('GITHUB_ACTIONS'):
            return 'github_actions'
        elif os.getenv('REPL_ID'):
            return 'replit'
        elif os.getenv('RAILWAY_ENVIRONMENT'):
            return 'railway'
        elif os.getenv('HEROKU_APP_NAME'):
            return 'heroku'
        elif os.getenv('VERCEL'):
            return 'vercel'
        else:
            return 'local'
    
    def _load_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load configurations for best models by function"""
        return {
            'conversation': {
                'github_actions': {
                    'model_name': 'microsoft/DialoGPT-large',
                    'fallback': 'microsoft/DialoGPT-medium',
                    'cache_strategy': 'progressive',
                    'max_memory': '2GB',
                    'optimization': 'quantized'
                },
                'cloud': {
                    'model_name': 'microsoft/DialoGPT-large',
                    'cache_strategy': 'streaming',
                    'optimization': 'fp16'
                }
            },
            'text_generation': {
                'github_actions': {
                    'model_name': 'gpt2-large',
                    'fallback': 'gpt2-medium',
                    'cache_strategy': 'progressive',
                    'max_memory': '1.5GB'
                },
                'cloud': {
                    'model_name': 'EleutherAI/gpt-neo-1.3B',
                    'cache_strategy': 'streaming'
                }
            },
            'sentiment_analysis': {
                'github_actions': {
                    'model_name': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
                    'cache_strategy': 'full_cache',
                    'max_memory': '500MB'
                },
                'cloud': {
                    'model_name': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
                    'cache_strategy': 'streaming'
                }
            },
            'translation': {
                'github_actions': {
                    'model_name': 'Helsinki-NLP/opus-mt-en-mul',
                    'cache_strategy': 'progressive',
                    'max_memory': '800MB'
                },
                'cloud': {
                    'model_name': 'facebook/mbart-large-50-many-to-many-mmt',
                    'cache_strategy': 'streaming'
                }
            },
            'text_to_speech': {
                'github_actions': {
                    'model_name': 'microsoft/speecht5_tts',
                    'cache_strategy': 'progressive',
                    'max_memory': '1GB'
                },
                'cloud': {
                    'model_name': 'suno/bark',
                    'cache_strategy': 'streaming'
                }
            },
            'speech_to_text': {
                'github_actions': {
                    'model_name': 'openai/whisper-base',
                    'cache_strategy': 'full_cache',
                    'max_memory': '600MB'
                },
                'cloud': {
                    'model_name': 'openai/whisper-large-v3',
                    'cache_strategy': 'streaming'
                }
            },
            'code_generation': {
                'github_actions': {
                    'model_name': 'Salesforce/codegen-350M-mono',
                    'cache_strategy': 'progressive',
                    'max_memory': '700MB'
                },
                'cloud': {
                    'model_name': 'Salesforce/codegen-6B-mono',
                    'cache_strategy': 'streaming'
                }
            },
            'summarization': {
                'github_actions': {
                    'model_name': 'facebook/bart-large-cnn',
                    'cache_strategy': 'progressive',
                    'max_memory': '1.2GB'
                },
                'cloud': {
                    'model_name': 'google/pegasus-xsum',
                    'cache_strategy': 'streaming'
                }
            }
        }
    
    def _setup_cache_directory(self) -> Optional[Path]:
        """Setup cache directory based on environment"""
        if self.environment == 'github_actions':
            # Use temporary directory that persists during workflow
            cache_dir = Path('/tmp/model_cache')
            cache_dir.mkdir(exist_ok=True)
            return cache_dir
        elif self.environment in ['replit', 'local']:
            # Use persistent cache directory
            cache_dir = Path('./model_cache')
            cache_dir.mkdir(exist_ok=True)
            return cache_dir
        else:
            # Cloud environments - no persistent cache
            return None
    
    async def load_model(self, function: str, priority: str = 'normal') -> Optional[Any]:
        """Load model optimized for environment and function"""
        try:
            start_time = time.time()
            
            # Get model config for function and environment
            function_config = self.model_configs.get(function, {})
            env_key = 'github_actions' if self.environment == 'github_actions' else 'cloud'
            model_config = function_config.get(env_key, {})
            
            if not model_config:
                logger.warning(f"⚠️ No model config for {function} in {self.environment}")
                return None
            
            model_name = model_config['model_name']
            cache_strategy = model_config.get('cache_strategy', 'streaming')
            
            logger.info(f"🔄 Loading {function} model: {model_name} ({cache_strategy})")
            
            # Load based on cache strategy
            if cache_strategy == 'progressive':
                model = await self._load_progressive(model_name, model_config, function)
            elif cache_strategy == 'full_cache':
                model = await self._load_cached(model_name, model_config, function)
            elif cache_strategy == 'streaming':
                model = await self._load_streaming(model_name, model_config, function)
            else:
                logger.error(f"❌ Unknown cache strategy: {cache_strategy}")
                return None
            
            # Track performance
            load_time = time.time() - start_time
            self.load_times[function] = load_time
            self.memory_usage[function] = self._get_memory_usage()
            
            if model:
                self.models[function] = {
                    'model': model,
                    'tokenizer': getattr(model, 'tokenizer', None),
                    'config': model_config,
                    'loaded_at': time.time()
                }
                logger.info(f"✅ {function} model loaded in {load_time:.2f}s")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Error loading {function} model: {e}")
            # Try fallback model if available
            fallback = model_config.get('fallback')
            if fallback and fallback != model_name:
                logger.info(f"🔄 Trying fallback model: {fallback}")
                model_config['model_name'] = fallback
                return await self.load_model(function, priority)
            return None
    
    async def _load_progressive(self, model_name: str, config: Dict[str, Any], function: str) -> Optional[Any]:
        """Progressive loading for GitHub Actions - download and cache incrementally"""
        try:
            from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM
            import torch
            
            # Check if already cached
            cache_path = self.cache_dir / function if self.cache_dir else None
            
            if cache_path and cache_path.exists():
                logger.info(f"📁 Loading {function} model from cache")
                try:
                    tokenizer = AutoTokenizer.from_pretrained(str(cache_path))
                    if function in ['conversation', 'text_generation']:
                        model = AutoModelForCausalLM.from_pretrained(
                            str(cache_path),
                            torch_dtype=torch.float16 if config.get('optimization') == 'fp16' else torch.float32,
                            device_map='cpu',
                            low_cpu_mem_usage=True
                        )
                    else:
                        model = AutoModel.from_pretrained(
                            str(cache_path),
                            torch_dtype=torch.float16 if config.get('optimization') == 'fp16' else torch.float32,
                            device_map='cpu'
                        )
                    model.tokenizer = tokenizer
                    return model
                except Exception as e:
                    logger.warning(f"⚠️ Cache loading failed: {e}")
            
            # Progressive download - download in chunks
            logger.info(f"📥 Progressive download of {model_name}")
            
            # Download tokenizer first (small)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Check memory before downloading model
            available_memory = self._get_available_memory()
            max_memory = self._parse_memory(config.get('max_memory', '1GB'))
            
            if available_memory < max_memory * 1.2:  # 20% buffer
                logger.warning(f"⚠️ Insufficient memory for {model_name}, using smaller variant")
                return await self._load_streaming(model_name, config, function)
            
            # Download model with optimization
            if function in ['conversation', 'text_generation']:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if config.get('optimization') == 'fp16' else torch.float32,
                    device_map='cpu',
                    low_cpu_mem_usage=True,
                    cache_dir=str(cache_path.parent) if cache_path else None
                )
            else:
                model = AutoModel.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if config.get('optimization') == 'fp16' else torch.float32,
                    device_map='cpu',
                    cache_dir=str(cache_path.parent) if cache_path else None
                )
            
            # Cache for future use
            if cache_path:
                try:
                    cache_path.mkdir(exist_ok=True)
                    tokenizer.save_pretrained(str(cache_path))
                    model.save_pretrained(str(cache_path))
                    logger.info(f"💾 Model cached to {cache_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Caching failed: {e}")
            
            model.tokenizer = tokenizer
            return model
            
        except Exception as e:
            logger.error(f"❌ Progressive loading failed: {e}")
            return None
    
    async def _load_cached(self, model_name: str, config: Dict[str, Any], function: str) -> Optional[Any]:
        """Full caching strategy for frequently used small models"""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            cache_path = self.cache_dir / function if self.cache_dir else None
            
            # Try cache first
            if cache_path and cache_path.exists():
                logger.info(f"📁 Loading {function} model from cache")
                tokenizer = AutoTokenizer.from_pretrained(str(cache_path))
                model = AutoModel.from_pretrained(str(cache_path))
                model.tokenizer = tokenizer
                return model
            
            # Download and cache
            logger.info(f"📥 Downloading and caching {model_name}")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(
                model_name,
                torch_dtype=torch.float32,  # Full precision for small models
                device_map='cpu'
            )
            
            # Save to cache
            if cache_path:
                cache_path.mkdir(exist_ok=True)
                tokenizer.save_pretrained(str(cache_path))
                model.save_pretrained(str(cache_path))
                logger.info(f"💾 Model fully cached")
            
            model.tokenizer = tokenizer
            return model
            
        except Exception as e:
            logger.error(f"❌ Full caching failed: {e}")
            return None
    
    async def _load_streaming(self, model_name: str, config: Dict[str, Any], function: str) -> Optional[Any]:
        """Enhanced streaming strategy for cloud deployment with on-demand loading"""
        try:
            from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM, pipeline
            import torch
            
            logger.info(f"🌊 Streaming {model_name} with on-demand loading")
            
            # Check if streaming is explicitly enabled
            stream_enabled = os.getenv('STREAM_MODELS', 'false').lower() == 'true'
            use_on_demand = os.getenv('MODEL_DOWNLOAD_ON_DEMAND', 'false').lower() == 'true'
            
            if use_on_demand:
                logger.info(f"⚡ Using on-demand streaming for {function}")
                # Create a lightweight wrapper that loads on first use
                return self._create_lazy_model_wrapper(model_name, config, function)
            
            # Standard streaming load
            # Load tokenizer first (lightweight)
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                use_fast=True,
                trust_remote_code=True
            )
            
            # Optimized model loading based on function
            if function in ['conversation', 'text_generation']:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map='auto' if torch.cuda.is_available() else 'cpu',
                    low_cpu_mem_usage=True,
                    trust_remote_code=True,
                    use_cache=True,
                    load_in_8bit=True if os.getenv('LOW_MEMORY_MODE') == 'true' else False
                )
            elif function in ['sentiment_analysis', 'translation', 'text_to_speech', 'speech_to_text']:
                # Use pipeline for these functions (more efficient streaming)
                if function == 'sentiment_analysis':
                    model = pipeline('sentiment-analysis', model=model_name, tokenizer=tokenizer)
                elif function == 'translation':
                    model = pipeline('translation', model=model_name, tokenizer=tokenizer)
                elif function == 'text_to_speech':
                    model = pipeline('text-to-speech', model=model_name, tokenizer=tokenizer)
                elif function == 'speech_to_text':
                    model = pipeline('automatic-speech-recognition', model=model_name, tokenizer=tokenizer)
                else:
                    model = AutoModel.from_pretrained(
                        model_name,
                        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                        device_map='auto' if torch.cuda.is_available() else 'cpu',
                        trust_remote_code=True
                    )
            else:
                model = AutoModel.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map='auto' if torch.cuda.is_available() else 'cpu',
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
            
            # Attach tokenizer if not a pipeline
            if not hasattr(model, '__call__') or not hasattr(model, 'tokenizer'):
                model.tokenizer = tokenizer
            
            logger.info(f"✅ Streaming model {model_name} loaded successfully")
            return model
            
        except Exception as e:
            logger.error(f"❌ Streaming load failed for {model_name}: {e}")
            # Try a fallback with a smaller model
            fallback_models = {
                'conversation': 'microsoft/DialoGPT-small',
                'text_generation': 'gpt2',
                'sentiment_analysis': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
                'translation': 'Helsinki-NLP/opus-mt-en-mul'
            }
            
            if function in fallback_models and fallback_models[function] != model_name:
                logger.info(f"🔄 Trying fallback model for {function}: {fallback_models[function]}")
                return await self._load_streaming(fallback_models[function], config, function)
            
            return None
    
    def _parse_memory(self, memory_str: str) -> float:
        """Parse memory string to bytes"""
        if memory_str.endswith('GB'):
            return float(memory_str[:-2]) * 1024 * 1024 * 1024
        elif memory_str.endswith('MB'):
            return float(memory_str[:-2]) * 1024 * 1024
        else:
            return float(memory_str)
    
    def _get_available_memory(self) -> float:
        """Get available system memory in bytes"""
        return psutil.virtual_memory().available
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used
        }
    
    def _create_lazy_model_wrapper(self, model_name: str, config: Dict[str, Any], function: str):
        """Create a lazy loading wrapper for on-demand model streaming"""
        class LazyModel:
            def __init__(self, manager, model_name, config, function):
                self._manager = manager
                self._model_name = model_name
                self._config = config
                self._function = function
                self._model = None
                self._loading = False
                
            async def _ensure_loaded(self):
                if self._model is None and not self._loading:
                    self._loading = True
                    logger.info(f"🔄 On-demand loading {self._function} model: {self._model_name}")
                    try:
                        # Load the actual model using standard streaming
                        old_on_demand = os.environ.get('MODEL_DOWNLOAD_ON_DEMAND', 'false')
                        os.environ['MODEL_DOWNLOAD_ON_DEMAND'] = 'false'  # Prevent infinite recursion
                        self._model = await self._manager._load_streaming(self._model_name, self._config, self._function)
                        os.environ['MODEL_DOWNLOAD_ON_DEMAND'] = old_on_demand
                        logger.info(f"✅ On-demand model loaded: {self._function}")
                    except Exception as e:
                        logger.error(f"❌ On-demand loading failed: {e}")
                        self._model = None
                    finally:
                        self._loading = False
                return self._model
                
            async def __call__(self, *args, **kwargs):
                model = await self._ensure_loaded()
                if model and hasattr(model, '__call__'):
                    return model(*args, **kwargs)
                return None
                
            def __getattr__(self, name):
                if name.startswith('_'):
                    return object.__getattribute__(self, name)
                # For non-private attributes, ensure model is loaded
                async def get_attr():
                    model = await self._ensure_loaded()
                    if model:
                        return getattr(model, name)
                    return None
                return get_attr()
        
        return LazyModel(self, model_name, config, function)
    
    async def get_model(self, function: str) -> Optional[Any]:
        """Get loaded model for function"""
        if function in self.models:
            return self.models[function]['model']
        
        # Auto-load if not present
        logger.info(f"🔄 Auto-loading {function} model")
        return await self.load_model(function)
    
    async def preload_priority_models(self, priority_functions: List[str]):
        """Preload high-priority models based on environment capacity"""
        try:
            logger.info(f"🚀 Preloading priority models: {priority_functions}")
            
            available_memory = self._get_available_memory()
            logger.info(f"💾 Available memory: {available_memory / (1024**3):.2f} GB")
            
            # Load models in priority order
            for function in priority_functions:
                try:
                    function_config = self.model_configs.get(function, {})
                    env_key = 'github_actions' if self.environment == 'github_actions' else 'cloud'
                    model_config = function_config.get(env_key, {})
                    
                    if model_config:
                        max_memory = self._parse_memory(model_config.get('max_memory', '1GB'))
                        current_available = self._get_available_memory()
                        
                        if current_available > max_memory * 1.5:  # 50% buffer
                            await self.load_model(function, 'high')
                        else:
                            logger.warning(f"⚠️ Skipping {function} due to memory constraints")
                            break
                    
                except Exception as e:
                    logger.error(f"❌ Error preloading {function}: {e}")
                    continue
            
            logger.info("✅ Priority model preloading completed")
            
        except Exception as e:
            logger.error(f"❌ Preloading failed: {e}")
    
    async def cleanup_unused_models(self, keep_functions: List[str] = None):
        """Clean up models not in keep list to free memory"""
        try:
            keep_functions = keep_functions or ['conversation']
            
            models_to_remove = []
            for function in self.models:
                if function not in keep_functions:
                    models_to_remove.append(function)
            
            for function in models_to_remove:
                model_data = self.models.pop(function, None)
                if model_data:
                    del model_data['model']
                    if model_data.get('tokenizer'):
                        del model_data['tokenizer']
                    logger.info(f"🧹 Cleaned up {function} model")
            
            # Force garbage collection
            gc.collect()
            
            if models_to_remove:
                logger.info(f"🧹 Memory cleanup completed: removed {len(models_to_remove)} models")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get model loading and performance statistics"""
        current_memory = self._get_memory_usage()
        
        return {
            'environment': self.environment,
            'loaded_models': list(self.models.keys()),
            'load_times': self.load_times.copy(),
            'memory_usage': current_memory,
            'cache_directory': str(self.cache_dir) if self.cache_dir else None,
            'model_count': len(self.models)
        }
    
    async def optimize_for_environment(self):
        """Optimize model loading strategy for current environment"""
        try:
            if self.environment == 'github_actions':
                # GitHub Actions optimization
                logger.info("🔧 Optimizing for GitHub Actions environment")
                
                # Preload essential models
                priority_models = ['conversation', 'sentiment_analysis']
                await self.preload_priority_models(priority_models)
                
                # Set up aggressive memory management
                asyncio.create_task(self._periodic_cleanup())
                
            elif self.environment in ['replit', 'local']:
                # Development environment optimization
                logger.info("🔧 Optimizing for development environment")
                
                # Load lightweight models for development
                priority_models = ['conversation']
                await self.preload_priority_models(priority_models)
                
            else:
                # Cloud environment optimization
                logger.info("🔧 Optimizing for cloud environment")
                
                # Use streaming for all models
                logger.info("🌊 Using streaming strategy for all models")
            
        except Exception as e:
            logger.error(f"❌ Environment optimization failed: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic memory cleanup for long-running processes"""
        try:
            while True:
                await asyncio.sleep(300)  # Every 5 minutes
                
                memory = psutil.virtual_memory()
                if memory.percent > 80:
                    logger.info("🧹 High memory usage detected, cleaning up")
                    await self.cleanup_unused_models(['conversation'])
                
        except asyncio.CancelledError:
            logger.info("🛑 Periodic cleanup stopped")
        except Exception as e:
            logger.error(f"❌ Periodic cleanup error: {e}")