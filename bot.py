import os
import asyncio
from flask import Flask, request, jsonify
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest

app = Flask(__name__)

# Configuration with your credentials
api_id = 17752898
api_hash = '899d5b7bb6c1a3672d822256bffac2a3'
bot_token = '7621816424:AAE3m2GDw6drXN4d-o8QNHv4cgpHr0L9YG0'
port = 50  # Changed from 5000 to 50 as per your request

# Initialize client
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

@app.route('/')
def home():
    return "Telegram Member Manager Bot is Running!"

@app.route('/scrape', methods=['POST'])
async def scrape_members():
    try:
        data = request.json
        source = data.get('source')
        target = data.get('target')
        
        if not source or not target:
            return jsonify({"error": "Both source and target parameters are required"}), 400
        
        async with client:
            # Get entities
            source_entity = await client.get_entity(source)
            target_entity = await client.get_entity(target)
            
            # Scrape members (limited to 10 for testing)
            members = await client.get_participants(source_entity, limit=10)
            
            # Add members with rate limiting
            results = []
            for user in members:
                try:
                    await client(InviteToChannelRequest(target_entity, [user]))
                    results.append(f"Successfully added {user.id}")
                    await asyncio.sleep(10)  # Rate limiting
                except Exception as e:
                    results.append(f"Failed to add {user.id}: {str(e)}")
            
            return jsonify({
                "status": "completed",
                "results": results,
                "total_attempted": len(members),
                "successful": len([r for r in results if "Successfully" in r])
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
