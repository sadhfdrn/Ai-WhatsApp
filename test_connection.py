#!/usr/bin/env python3
"""
Test script to debug WhatsApp connection issues
"""

import asyncio
import json
import os
import time
from datetime import datetime

async def test_message_flow():
    """Test the message flow between Python and Node.js bridge"""
    print("🧪 Testing WhatsApp message flow...")
    
    # Create a test incoming message
    test_message = {
        "id": "test_message_001",
        "from": "1234567890@c.us",
        "body": "Hello bot, this is a test!",
        "type": "text",
        "timestamp": int(time.time()),
        "processed": False,
        "received_at": datetime.now().isoformat()
    }
    
    # Write to incoming messages file
    messages_file = "incoming_messages.json"
    with open(messages_file, 'w') as f:
        json.dump([test_message], f, indent=2)
    
    print(f"✅ Created test message in {messages_file}")
    print(f"📨 Test message: {test_message['body']}")
    
    # Wait a bit for processing
    await asyncio.sleep(5)
    
    # Check if it was processed
    if os.path.exists(messages_file):
        with open(messages_file, 'r') as f:
            messages = json.load(f)
        
        if messages and messages[0].get('processed'):
            print("✅ Message was processed by the bot")
        else:
            print("❌ Message was not processed")
    
    # Check for outgoing messages
    outgoing_file = "outgoing_messages.json"
    if os.path.exists(outgoing_file):
        with open(outgoing_file, 'r') as f:
            outgoing = json.load(f)
        
        if outgoing:
            print(f"📤 Found {len(outgoing)} outgoing messages:")
            for msg in outgoing:
                print(f"   To: {msg['to']}")
                print(f"   Message: {msg['message'][:100]}...")
        else:
            print("❌ No outgoing messages found")
    else:
        print("❌ No outgoing messages file found")

async def check_bridge_status():
    """Check if the baileys bridge is running"""
    print("\n🌉 Checking baileys bridge status...")
    
    # Check if Node.js bridge files exist
    bridge_files = ["whatsapp_bridge.js", "package.json"]
    for file in bridge_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
    
    # Check for auth directory
    if os.path.exists("wa-auth"):
        print("✅ wa-auth directory exists")
    else:
        print("❌ wa-auth directory not found")

async def main():
    """Main test function"""
    print("🔍 WhatsApp Bot Connection Test")
    print("=" * 40)
    
    await check_bridge_status()
    await test_message_flow()
    
    print("\n💡 Tips:")
    print("1. Make sure you've scanned the QR code in the Node.js bridge")
    print("2. Check that your phone is connected to the internet")
    print("3. Try sending a message to your WhatsApp from another device")
    print("4. Check the bot logs for any error messages")

if __name__ == "__main__":
    asyncio.run(main())