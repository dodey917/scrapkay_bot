import os
import asyncio
from flask import Flask, request, jsonify
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import InviteToChannelRequest

app = Flask(__name__)

# Configuration - REPLACE WITH YOUR CREDS
API_ID = 17752898
API_HASH = '899d5b7bb6c1a3672d822256bffac2a3'
BOT_TOKEN = '7621816424:AAE3m2GDw6drXN4d-o8QNHv4cgpHr0L9YG0'
PORT = 50

# Initialize client
client = TelegramClient('bot_session', API_ID, API_HASH)

async def start_client():
    await client.start(bot_token=BOT_TOKEN)
    print("Client Created")

# Start the client when app starts
asyncio.run(start_client())

@app.route('/')
def home():
    return "Telegram Scraper Bot is Running!"

@app.route('/scrape', methods=['POST'])
async def scrape_members():
    try:
        data = request.json
        source = data.get('https://t.me/cryptpmedia')
        target = data.get('https://t.me/growandhelp')
        
        if not source or not target:
            return jsonify({"error": "Both source and target parameters are required"}), 400
        
        async with client:
            try:
                # Get entities
                source_entity = await client.get_entity(source)
                target_entity = await client.get_entity(target)
                
                # Scrape members (limited to 5 for testing)
                members = await client.get_participants(source_entity, limit=5)
                
                # Add members with rate limiting
                results = []
                for user in members:
                    try:
                        await client(InviteToChannelRequest(target_entity, [user]))
                        results.append(f"Added {user.id}")
                        await asyncio.sleep(15)  # Increased delay to avoid limits
                    except errors.UserPrivacyRestrictedError:
                        results.append(f"Failed {user.id}: Privacy restricted")
                    except errors.FloodWaitError as e:
                        results.append(f"Failed {user.id}: Flood wait {e.seconds} seconds")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        results.append(f"Failed {user.id}: {str(e)}")
                
                return jsonify({
                    "status": "completed",
                    "results": results,
                    "stats": {
                        "total": len(members),
                        "success": len([r for r in results if "Added" in r]),
                        "failed": len([r for r in results if "Failed" in r])
                    }
                })
                
            except Exception as e:
                return jsonify({"error": f"Entity resolution failed: {str(e)}"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
