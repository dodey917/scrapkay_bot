from telethon.sync import TelegramClient, events
from telethon.tl.functions.channels import InviteToChannelRequest
import asyncio

# Your credentials
API_ID = 17752898
API_HASH = '899d5b7bb6c1a3672d822256bffac2a3'
BOT_TOKEN = '7621816424:AAE3m2GDw6drXN4d-o8QNHv4cgpHr0L9YG0'

# User session storage
user_sessions = {}

# Initialize client
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Send welcome message and instructions"""
    await event.respond(
        "🤖 **Telegram Member Manager Bot**\n\n"
        "Send me:\n"
        "1. First send the SOURCE group link (where to scrape members from)\n"
        "2. Then send the TARGET group link (where to add members)\n\n"
        "Example:\n"
        "`https://t.me/source_group`\n"
        "`https://t.me/target_group`\n\n"
        "Note: I must be admin in both groups!"
    )
    user_sessions[event.sender_id] = {'step': 'waiting_source'}

@bot.on(events.NewMessage)
async def handle_messages(event):
    user_id = event.sender_id
    text = event.text
    
    # Skip if not in a session
    if user_id not in user_sessions:
        return
    
    # Handle source link
    if user_sessions[user_id]['step'] == 'waiting_source':
        if not text.startswith('https://t.me/'):
            await event.respond("❌ Please send a valid Telegram group link (starting with https://t.me/)")
            return
            
        user_sessions[user_id] = {
            'source': text,
            'step': 'waiting_target'
        }
        await event.respond("✅ Source group saved! Now send the TARGET group link:")
    
    # Handle target link
    elif user_sessions[user_id]['step'] == 'waiting_target':
        if not text.startswith('https://t.me/'):
            await event.respond("❌ Please send a valid Telegram group link (starting with https://t.me/)")
            return
            
        user_sessions[user_id]['target'] = text
        user_sessions[user_id]['step'] = 'ready'
        
        # Confirm before starting
        await event.respond(
            f"🔍 Will scrape members from:\n{user_sessions[user_id]['source']}\n\n"
            f"➡️ And add them to:\n{user_sessions[user_id]['target']}\n\n"
            "Type /confirm to start or /cancel to abort"
        )
    
    # Handle confirmation
    elif text == '/confirm' and user_sessions[user_id]['step'] == 'ready':
        await event.respond("⏳ Starting the process... (This may take a while)")
        
        try:
            async with bot:
                # Get entities
                source_entity = await bot.get_entity(user_sessions[user_id]['source'])
                target_entity = await bot.get_entity(user_sessions[user_id]['target'])
                
                # Scrape members
                members = await bot.get_participants(source_entity, limit=50)
                
                # Process members
                success = 0
                failed = 0
                total = len(members)
                
                for i, user in enumerate(members):
                    try:
                        await bot(InviteToChannelRequest(target_entity, [user]))
                        success += 1
                        if i % 5 == 0:  # Update progress every 5 users
                            await event.respond(f"🔄 Processed {i+1}/{total} users...")
                        await asyncio.sleep(15)  # Important delay
                    except Exception as e:
                        failed += 1
                        
                # Final report
                await event.respond(
                    f"✅ Process completed!\n\n"
                    f"• Total members: {total}\n"
                    f"• Successfully added: {success}\n"
                    f"• Failed: {failed}\n\n"
                    f"Type /start to begin again"
                )
                
        except Exception as e:
            await event.respond(f"❌ Error: {str(e)}")
        
        # Clear session
        del user_sessions[user_id]
    
    elif text == '/cancel':
        await event.respond("🚫 Operation cancelled")
        del user_sessions[user_id]

print("Bot is running...")
bot.run_until_disconnected()
