"""
Deployment Logger for WhatsApp AI Bot
Provides comprehensive logging for deployment monitoring and health checks
"""

import os
import sys
import time
import logging
import psutil
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

class DeploymentLogger:
    """Enhanced logger for deployment monitoring"""
    
    def __init__(self, log_level: str = "INFO"):
        self.start_time = time.time()
        self.setup_logging(log_level)
        self.deployment_info = self.gather_deployment_info()
        
    def setup_logging(self, log_level: str):
        """Setup enhanced logging with deployment context"""
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='🚀 %(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger("DeploymentMonitor")
        
    def gather_deployment_info(self) -> Dict[str, Any]:
        """Gather comprehensive deployment environment information"""
        info = {
            "deployment_time": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version,
            "platform": sys.platform,
            "environment": self._detect_environment(),
            "system_resources": self._get_system_resources(),
            "environment_variables": self._check_environment_variables(),
            "file_system": self._check_file_system(),
            "network": self._check_network_connectivity()
        }
        return info
    
    def _detect_environment(self) -> str:
        """Detect deployment environment"""
        if os.getenv('DOCKER_CONTAINER'):
            return 'docker'
        elif os.getenv('REPL_ID'):
            return 'replit'
        elif os.getenv('RAILWAY_ENVIRONMENT'):
            return 'railway'
        elif os.getenv('HEROKU_APP_NAME'):
            return 'heroku'
        elif os.getenv('VERCEL'):
            return 'vercel'
        else:
            return 'unknown'
    
    def _get_system_resources(self) -> Dict[str, Any]:
        """Get system resource information"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_percent": memory.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent": round((disk.used / disk.total) * 100, 2),
                "cpu_count": psutil.cpu_count()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _check_environment_variables(self) -> Dict[str, Any]:
        """Check critical environment variables"""
        critical_vars = [
            'DATABASE_URL', 'WHOOGLE_URL', 
            'USE_STREAMING', 'STREAM_MODELS', 'MODEL_DOWNLOAD_ON_DEMAND',
            'WHOOGLE_INSTANCE_ACTIVE', 'LOW_MEMORY_MODE'
        ]
        
        status = {}
        for var in critical_vars:
            value = os.getenv(var)
            if var in ['DATABASE_URL']:
                # Don't log sensitive values, just check presence
                status[var] = "SET" if value else "NOT_SET"
            else:
                status[var] = value or "NOT_SET"
        
        return status
    
    def _check_file_system(self) -> Dict[str, Any]:
        """Check file system and required directories"""
        dirs_to_check = ['model_cache', 'data', 'logs', 'wa-auth']
        files_to_check = ['main.py', 'whatsapp_bridge.js', 'package.json', 'pyproject.toml']
        
        status = {
            "directories": {},
            "files": {}
        }
        
        for dir_name in dirs_to_check:
            path = Path(dir_name)
            status["directories"][dir_name] = {
                "exists": path.exists(),
                "is_directory": path.is_dir() if path.exists() else False,
                "writable": os.access(str(path), os.W_OK) if path.exists() else False
            }
        
        for file_name in files_to_check:
            path = Path(file_name)
            status["files"][file_name] = {
                "exists": path.exists(),
                "size_kb": round(path.stat().st_size / 1024, 2) if path.exists() else 0,
                "readable": os.access(str(path), os.R_OK) if path.exists() else False
            }
        
        return status
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity to key services"""
        urls_to_check = [
            'https://huggingface.co',
            'https://search.benbusby.com',
            'https://whoogle.hectabit.co'
        ]
        
        status = {}
        for url in urls_to_check:
            try:
                import requests
                response = requests.get(url, timeout=5)
                status[url] = {
                    "reachable": True,
                    "status_code": response.status_code,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
                }
            except Exception as e:
                status[url] = {
                    "reachable": False,
                    "error": str(e)
                }
        
        return status
    
    def log_startup_summary(self):
        """Log comprehensive startup summary"""
        self.logger.info("=" * 80)
        self.logger.info("🚀 WHATSAPP AI BOT DEPLOYMENT STATUS")
        self.logger.info("=" * 80)
        
        # Environment Info
        env = self.deployment_info["environment"]
        self.logger.info(f"📍 Environment: {env.upper()}")
        self.logger.info(f"🐍 Python: {sys.version.split()[0]}")
        self.logger.info(f"⏰ Deployment Time: {self.deployment_info['deployment_time']}")
        
        # System Resources
        resources = self.deployment_info["system_resources"]
        if "error" not in resources:
            self.logger.info(f"💾 Memory: {resources['memory_available_gb']}GB/{resources['memory_total_gb']}GB available ({resources['memory_percent']}% used)")
            self.logger.info(f"💿 Disk: {resources['disk_free_gb']}GB/{resources['disk_total_gb']}GB available ({resources['disk_percent']}% used)")
            self.logger.info(f"⚡ CPU Cores: {resources['cpu_count']}")
        
        # Environment Variables
        env_vars = self.deployment_info["environment_variables"]
        self.logger.info("🔧 Environment Variables:")
        for var, status in env_vars.items():
            icon = "✅" if status != "NOT_SET" else "❌"
            self.logger.info(f"   {icon} {var}: {status}")
        
        # File System
        fs = self.deployment_info["file_system"]
        self.logger.info("📁 File System Status:")
        
        for dir_name, status in fs["directories"].items():
            icon = "✅" if status["exists"] and status["writable"] else "❌"
            self.logger.info(f"   {icon} {dir_name}/: {'EXISTS & WRITABLE' if status['exists'] and status['writable'] else 'MISSING OR READ-ONLY'}")
        
        for file_name, status in fs["files"].items():
            icon = "✅" if status["exists"] else "❌"
            size_info = f" ({status['size_kb']}KB)" if status["exists"] else ""
            self.logger.info(f"   {icon} {file_name}: {'EXISTS' if status['exists'] else 'MISSING'}{size_info}")
        
        # Network Connectivity
        network = self.deployment_info["network"]
        self.logger.info("🌐 Network Connectivity:")
        for url, status in network.items():
            if status["reachable"]:
                icon = "✅"
                info = f"HTTP {status['status_code']} ({status['response_time_ms']}ms)"
            else:
                icon = "❌"
                info = f"FAILED - {status['error']}"
            self.logger.info(f"   {icon} {url}: {info}")
        
        self.logger.info("=" * 80)
    
    def log_database_status(self):
        """Log database connectivity and status"""
        self.logger.info("🗄️  DATABASE CONNECTION TEST")
        self.logger.info("-" * 40)
        
        try:
            # Try to import database modules
            from database.models import get_database_engine, get_db, init_database
            
            # Test database engine creation
            engine = get_database_engine()
            if engine is None:
                self.logger.error("❌ Database engine creation failed - DATABASE_URL not set")
                return False
            
            self.logger.info("✅ Database engine created successfully")
            
            # Test database connection
            db = get_db()
            if db is None:
                self.logger.error("❌ Database session creation failed")
                return False
            
            self.logger.info("✅ Database session created successfully")
            
            # Test database initialization
            if init_database():
                self.logger.info("✅ Database tables initialized/verified")
                
                # Test basic query
                try:
                    from database.models import UserProfile
                    count = db.query(UserProfile).count()
                    self.logger.info(f"✅ Database query test passed - {count} user profiles found")
                except Exception as e:
                    self.logger.warning(f"⚠️ Database query test failed: {e}")
                
                db.close()
                return True
            else:
                self.logger.error("❌ Database initialization failed")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Database test failed: {e}")
            return False
    
    def log_model_manager_status(self):
        """Log AI model manager status"""
        self.logger.info("🧠 AI MODEL MANAGER STATUS")
        self.logger.info("-" * 40)
        
        try:
            from bot.model_manager import SmartModelManager
            from config import Config
            
            config = Config()
            model_manager = SmartModelManager(config)
            
            self.logger.info(f"✅ Model Manager initialized for {model_manager.environment} environment")
            self.logger.info(f"📁 Cache directory: {model_manager.cache_dir}")
            
            # Check streaming configuration
            use_streaming = os.getenv('USE_STREAMING', 'false').lower() == 'true'
            stream_models = os.getenv('STREAM_MODELS', 'false').lower() == 'true'
            on_demand = os.getenv('MODEL_DOWNLOAD_ON_DEMAND', 'false').lower() == 'true'
            low_memory = os.getenv('LOW_MEMORY_MODE', 'false').lower() == 'true'
            
            self.logger.info(f"⚙️ Streaming enabled: {use_streaming}")
            self.logger.info(f"⚙️ Model streaming: {stream_models}")
            self.logger.info(f"⚙️ On-demand loading: {on_demand}")
            self.logger.info(f"⚙️ Low memory mode: {low_memory}")
            
            # Check model configurations
            available_functions = list(model_manager.model_configs.keys())
            self.logger.info(f"🎯 Available AI functions: {', '.join(available_functions)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Model Manager test failed: {e}")
            return False
    
    def log_whatsapp_bridge_status(self):
        """Log WhatsApp bridge readiness"""
        self.logger.info("📱 WHATSAPP BRIDGE STATUS")
        self.logger.info("-" * 40)
        
        # Check Node.js files
        required_files = ['whatsapp_bridge.js', 'package.json', 'node_modules']
        for file_name in required_files:
            path = Path(file_name)
            if path.exists():
                self.logger.info(f"✅ {file_name}: EXISTS")
            else:
                self.logger.error(f"❌ {file_name}: MISSING")
        
        # Check wa-auth directory
        wa_auth_path = Path('wa-auth')
        if wa_auth_path.exists():
            auth_files = list(wa_auth_path.glob('*.json'))
            self.logger.info(f"✅ WhatsApp auth directory: {len(auth_files)} credential files")
        else:
            self.logger.warning("⚠️ WhatsApp auth directory: NOT FOUND (will be created on first run)")
        
        return True
    
    def log_health_check_server_status(self):
        """Log health check server configuration"""
        self.logger.info("🏥 HEALTH CHECK SERVER")
        self.logger.info("-" * 40)
        
        try:
            import socket
            
            # Test if port 8080 is available
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8080))
            sock.close()
            
            if result == 0:
                self.logger.info("✅ Health check port 8080: AVAILABLE")
            else:
                self.logger.info("⚠️ Health check port 8080: NOT YET BOUND (will start with application)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Health check test failed: {e}")
            return False
    
    def log_deployment_readiness(self):
        """Log overall deployment readiness assessment"""
        self.logger.info("=" * 80)
        self.logger.info("🎯 DEPLOYMENT READINESS ASSESSMENT")
        self.logger.info("=" * 80)
        
        checks = [
            ("Database Connection", self.log_database_status),
            ("AI Model Manager", self.log_model_manager_status),
            ("WhatsApp Bridge", self.log_whatsapp_bridge_status),
            ("Health Check Server", self.log_health_check_server_status)
        ]
        
        results = {}
        for check_name, check_func in checks:
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.logger.error(f"❌ {check_name} check failed: {e}")
                results[check_name] = False
        
        # Overall assessment
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        self.logger.info("-" * 80)
        self.logger.info(f"📊 SUMMARY: {passed}/{total} checks passed")
        
        for check_name, result in results.items():
            icon = "✅" if result else "❌"
            self.logger.info(f"   {icon} {check_name}")
        
        if passed == total:
            self.logger.info("🎉 DEPLOYMENT READY! All systems operational.")
        elif passed >= total * 0.75:
            self.logger.warning("⚠️ DEPLOYMENT PARTIAL: Some non-critical issues detected.")
        else:
            self.logger.error("❌ DEPLOYMENT ISSUES: Critical problems detected!")
        
        elapsed = time.time() - self.start_time
        self.logger.info(f"⏱️ Total startup check time: {elapsed:.2f} seconds")
        self.logger.info("=" * 80)
        
        return passed == total
    
    def create_deployment_report(self):
        """Create a JSON report of deployment status"""
        report = {
            "deployment_time": datetime.now(timezone.utc).isoformat(),
            "deployment_info": self.deployment_info,
            "startup_duration_seconds": time.time() - self.start_time,
            "status": "completed"
        }
        
        try:
            report_path = Path("logs/deployment_report.json")
            report_path.parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"📄 Deployment report saved to {report_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save deployment report: {e}")
        
        return report

# Singleton instance
deployment_logger = None

def get_deployment_logger(log_level: str = "INFO") -> DeploymentLogger:
    """Get or create deployment logger singleton"""
    global deployment_logger
    if deployment_logger is None:
        deployment_logger = DeploymentLogger(log_level)
    return deployment_logger