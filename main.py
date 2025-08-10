#!/usr/bin/env python3
"""
WhatsApp AI Bot - Main Entry Point
A comprehensive AI-powered WhatsApp bot with personality, voice processing, and web search capabilities.
Enhanced with comprehensive deployment monitoring and logging.
"""

import asyncio
import os
import sys
import signal
import logging
from datetime import datetime
from dotenv import load_dotenv
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import Config
from bot.whatsapp_client import WhatsAppClient
from utils.logger import setup_logger
from utils.deployment_logger import get_deployment_logger

# Load environment variables
load_dotenv()

# Setup enhanced logging with deployment monitoring
logger = setup_logger(__name__)
deployment_logger = get_deployment_logger(os.getenv('LOG_LEVEL', 'INFO'))

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints"""
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": getattr(self.server, 'uptime', 0),
                "deployment_checks_passed": getattr(self.server, 'deployment_ready', False)
            }
            
            self.wfile.write(json.dumps(health_status, indent=2).encode())
            
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Get detailed status from deployment logger
            status_info = {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "deployment_ready": getattr(self.server, 'deployment_ready', False),
                "whatsapp_connected": getattr(self.server, 'whatsapp_connected', False),
                "database_available": getattr(self.server, 'database_available', False),
                "ai_models_ready": getattr(self.server, 'ai_models_ready', False)
            }
            
            self.wfile.write(json.dumps(status_info, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default HTTP server logging
        pass

class WhatsAppAIBot:
    """Main bot orchestrator class with health monitoring"""
    
    def __init__(self):
        self.config = Config()
        self.whatsapp_client = None
        self.running = False
        self.health_server = None
        self.start_time = datetime.now()
        
        # Status tracking for health endpoint
        self.deployment_ready = False
        self.whatsapp_connected = False
        self.database_available = False
        self.ai_models_ready = False
        
    async def start(self):
        """Start the WhatsApp AI bot with comprehensive deployment monitoring"""
        # Log deployment startup summary
        deployment_logger.log_startup_summary()
        
        # Run deployment readiness checks
        deployment_ready = deployment_logger.log_deployment_readiness()
        
        logger.info("🤖 Starting WhatsApp AI Bot...")
        logger.info(f"⚡ Bot starting at {datetime.now()}")
        
        if not deployment_ready:
            logger.warning("⚠️ Some deployment checks failed, but continuing startup...")
        
        try:
            # Start health check server
            self._start_health_server()
            
            # Update status tracking
            self.deployment_ready = deployment_ready
            
            # Initialize WhatsApp client
            logger.info("📱 Initializing WhatsApp client...")
            self.whatsapp_client = WhatsAppClient(self.config)
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Connect to WhatsApp
            logger.info("🔗 Connecting to WhatsApp Web...")
            await self.whatsapp_client.connect()
            self.whatsapp_connected = True
            
            # Check database availability
            try:
                from database.models import get_db
                db = get_db()
                self.database_available = db is not None
                if db:
                    db.close()
            except:
                self.database_available = False
            
            # Check AI models readiness
            try:
                from bot.model_manager import SmartModelManager
                model_manager = SmartModelManager(self.config)
                self.ai_models_ready = True
            except:
                self.ai_models_ready = False
            
            # Update health server status
            self._update_health_server_status()
            
            self.running = True
            logger.info("✅ Bot is now running and ready to receive messages!")
            logger.info("🏥 Health check server running on port 8080")
            
            # Create deployment report
            deployment_logger.create_deployment_report()
            
            # Keep the bot running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            sys.exit(1)
    
    def _start_health_server(self):
        """Start HTTP health check server in background thread"""
        try:
            self.health_server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
            self.health_server.deployment_ready = False
            self.health_server.whatsapp_connected = False
            self.health_server.database_available = False
            self.health_server.ai_models_ready = False
            self.health_server.uptime = 0
            
            # Start server in daemon thread
            health_thread = threading.Thread(target=self.health_server.serve_forever, daemon=True)
            health_thread.start()
            
            logger.info("🏥 Health check server started on port 8080")
        except Exception as e:
            logger.error(f"❌ Failed to start health check server: {e}")
    
    def _update_health_server_status(self):
        """Update health server with current status"""
        if self.health_server:
            self.health_server.deployment_ready = self.deployment_ready
            self.health_server.whatsapp_connected = self.whatsapp_connected
            self.health_server.database_available = self.database_available
            self.health_server.ai_models_ready = self.ai_models_ready
            self.health_server.uptime = (datetime.now() - self.start_time).total_seconds()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📨 Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("🛑 Stopping WhatsApp AI Bot...")
        self.running = False
        
        if self.health_server:
            logger.info("🏥 Stopping health check server...")
            self.health_server.shutdown()
        
        if self.whatsapp_client:
            await self.whatsapp_client.disconnect()
            
        logger.info("✅ Bot stopped successfully!")

async def main():
    """Main function"""
    bot = WhatsAppAIBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("⌨️ Keyboard interrupt received")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    # Run the bot
    asyncio.run(main())
