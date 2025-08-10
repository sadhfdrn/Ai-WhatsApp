#!/usr/bin/env python3
"""Direct test of bot components without the bridge"""

import asyncio
import sys
sys.path.append('.')

from config import Config
from bot.whatsapp_client import WhatsAppClient

async def direct_test():
    """Test the bot directly"""
    config = Config()
    client = WhatsAppClient(config)
    
    print("🧪 Testing direct message processing...")
    
    # Test AI processor first
    print("🤖 Testing AI processor directly...")
    response = await client.ai_processor.generate_response("Hello", "test@c.us", {})
    print(f"✅ AI Response: {response}")
    
    # Test message data
    message_data = {
        'from': 'test@c.us',
        'body': 'Hello bot, are you working?',
        'type': 'text',
        'timestamp': 1754785200
    }
    
    print("📨 Processing message through client...")
    print(f"Message data: {message_data}")
    
    # Process the message directly
    try:
        print("🔄 Calling handle_incoming_message...")
        await client.handle_incoming_message(message_data)
        print("✅ handle_incoming_message completed")
    except Exception as e:
        print(f"❌ Exception in handle_incoming_message: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if message was processed
    import time
    time.sleep(2)
    
    print("🔍 Checking outgoing messages...")
    try:
        with open('outgoing_messages.json', 'r') as f:
            import json
            messages = json.load(f)
            print(f"📤 Outgoing messages: {len(messages)}")
            for msg in messages:
                print(f"  - To: {msg.get('to', 'unknown')}")
                print(f"    Message: {msg.get('message', 'no message')[:100]}")
    except FileNotFoundError:
        print("📝 No outgoing messages file found")
    except Exception as e:
        print(f"❌ Error reading outgoing messages: {e}")
    
    print("✅ Direct test completed.")

if __name__ == "__main__":
    asyncio.run(direct_test())