#!/usr/bin/env python3
"""
WhatsApp AI Bot - Main Entry Point
A comprehensive AI-powered WhatsApp bot with personality, voice processing, and web search capabilities.
"""

import asyncio
import os
import sys
import signal
import logging
from datetime import datetime
from dotenv import load_dotenv

from config import Config
from bot.whatsapp_client import WhatsAppClient
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger(__name__)

class WhatsAppAIBot:
    """Main bot orchestrator class"""
    
    def __init__(self):
        self.config = Config()
        self.whatsapp_client = None
        self.running = False
        
    async def start(self):
        """Start the WhatsApp AI bot"""
        logger.info("🤖 Starting WhatsApp AI Bot...")
        logger.info(f"⚡ Bot starting at {datetime.now()}")
        
        try:
            # Initialize WhatsApp client
            self.whatsapp_client = WhatsAppClient(self.config)
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Connect to WhatsApp
            await self.whatsapp_client.connect()
            
            self.running = True
            logger.info("✅ Bot is now running and ready to receive messages!")
            
            # Keep the bot running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📨 Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("🛑 Stopping WhatsApp AI Bot...")
        self.running = False
        
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
