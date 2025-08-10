#!/usr/bin/env python3
"""Test message flow timing"""

import asyncio
import json
import sys
sys.path.append('.')

from config import Config
from bot.whatsapp_client import WhatsAppClient

async def test_message_timing():
    """Test message processing with timing checks"""
    print("🧪 Testing message flow timing...")
    
    config = Config()
    client = WhatsAppClient(config)
    
    # Clear outgoing messages first
    with open('outgoing_messages.json', 'w') as f:
        json.dump([], f)
    
    print("📝 Cleared outgoing messages file")
    
    # Send a message
    message_data = {
        'from': 'timing_test@c.us',
        'body': 'Test timing message',
        'type': 'text',
        'timestamp': 1754785300
    }
    
    print("📨 Processing message...")
    await client.handle_incoming_message(message_data)
    
    # Check at different intervals
    for i in range(10):
        with open('outgoing_messages.json', 'r') as f:
            messages = json.load(f)
        print(f"⏱️  After {i/10:.1f}s: {len(messages)} messages in queue")
        if messages:
            print(f"   First message: {messages[0].get('message', 'no message')[:50]}")
        await asyncio.sleep(0.1)
    
    print("✅ Timing test complete")

if __name__ == "__main__":
    asyncio.run(test_message_timing())