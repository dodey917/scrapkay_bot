import os
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from flask import Flask, request, jsonify
import asyncio
import time

app = Flask(__name__)

# Load from environment variables
api_id = int(os.getenv('17752898'))
api_hash = os.getenv('899d5b7bb6c1a3672d822256bffac2a3')
bot_token = os.getenv('7621816424:AAE3m2GDw6drXN4d-o8QNHv4cgpHr0L9YG0')
phone = os.getenv('08131082557')

client = TelegramClient('session_name', api_id, api_hash).start(bot_token=bot_token)

@app.route('/scrape', methods=['POST'])
async def scrape_members():
    data = request.json
    
    source_link = data.get('https://t.me/cryptpmedia')
    target_link = data.get('https://t.me/growandhelp')
    
    if not source_link or not target_link:
        return jsonify({"error": "Missing source or target link"}), 400
    
    try:
        # Get entity objects
        source_entity = await client.get_entity(source_link)
        target_entity = await client.get_entity(target_link)
        
        # Scrape members
        members = await client.get_participants(source_entity)
        
        # Add members with rate limiting
        added = []
        failed = []
        
        for user in members:
            try:
                await client(InviteToChannelRequest(
                    channel=target_entity,
                    users=[user]
                ))
                added.append(user.id)
                await asyncio.sleep(10)  # Important rate limit
            except Exception as e:
                failed.append({"user_id": user.id, "error": str(e)})
                
        return jsonify({
            "status": "completed",
            "added_count": len(added),
            "failed_count": len(failed),
            "failed_users": failed
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
