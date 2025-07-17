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
        "Here's how to use me:\n\n"
        "1. Send /scrape to begin\n"
        "2. I'll ask for the SOURCE group\n"
        "3. Then the TARGET group\n"
        "4. Tell me how many members to move\n\n"
        "Note: I must be admin in both groups!"
    )

@bot.on(events.NewMessage(pattern='/scrape'))
async def begin_scraping(event):
    user_id = event.sender_id
    user_sessions[user_id] = {'step': 'waiting_source'}
    await event.respond("Please send the SOURCE group link (where to get members from):")

@bot.on(events.NewMessage)
async def handle_messages(event):
    user_id = event.sender_id
    text = event.text
    
    if user_id not in user_sessions:
        return
    
    current_step = user_sessions[user_id]['step']
    
    # Handle source link
    if current_step == 'waiting_source':
        if not text.startswith('https://t.me/'):
            await event.respond("❌ Please send a valid Telegram group link (starting with https://t.me/)")
            return
            
        user_sessions[user_id] = {
            'source': text,
            'step': 'waiting_target'
        }
        await event.respond("✅ Source group saved! Now send the TARGET group link:")
    
    # Handle target link
    elif current_step == 'waiting_target':
        if not text.startswith('https://t.me/'):
            await event.respond("❌ Please send a valid Telegram group link (starting with https://t.me/)")
            return
            
        user_sessions[user_id]['target'] = text
        user_sessions[user_id]['step'] = 'waiting_count'
        await event.respond("🔢 How many members do you want to scrape? (Enter a number):")
    
    # Handle member count
    elif current_step == 'waiting_count':
        if not text.isdigit():
            await event.respond("❌ Please enter a valid number (e.g. 50)")
            return
            
        count = int(text)
        if count > 1000:  # Safety limit
            await event.respond("⚠️ Maximum allowed is 1000 members. Setting to 1000.")
            count = 1000
            
        user_sessions[user_id]['count'] = count
        user_sessions[user_id]['step'] = 'ready'
        
        # Start processing immediately (no confirmation)
        await process_members(event)

async def process_members(event):
    user_id = event.sender_id
    session = user_sessions[user_id]
    
    await event.respond(f"⏳ Starting to process {session['count']} members...")
    
    try:
        async with bot:
            # Get entities
            source_entity = await bot.get_entity(session['source'])
            target_entity = await bot.get_entity(session['target'])
            
            # Scrape members
            members = await bot.get_participants(source_entity, limit=session['count'])
            
            # Process members
            success = 0
            failed = 0
            total = len(members)
            
            for i, user in enumerate(members, 1):
                try:
                    await bot(InviteToChannelRequest(target_entity, [user]))
                    success += 1
                    if i % 10 == 0:  # Update every 10 users
                        await event.respond(f"🔄 Processed {i}/{total} users...")
                    await asyncio.sleep(10)  # Important delay
                except Exception as e:
                    failed += 1
                    
            # Final report
            await event.respond(
                f"✅ Process completed!\n\n"
                f"• Total members processed: {total}\n"
                f"• Successfully added: {success}\n"
                f"• Failed: {failed}\n\n"
                f"Type /scrape to start again"
            )
            
    except Exception as e:
        await event.respond(f"❌ Error occurred: {str(e)}")
    
    # Clear session
    del user_sessions[user_id]

print("Bot is running and waiting for commands...")
bot.run_until_disconnected()
