from telethon.sync import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import asyncio

API_ID = 17752898
API_HASH = '899d5b7bb6c1a3672d822256bffac2a3'
BOT_TOKEN = '7621816424:AAE3m2GDw6drXN4d-o8QNHv4cgpHr0L9YG0'

bot = TelegramClient('scraper_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_sessions = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "⚠️ Warning: This bot may violate Telegram's ToS\n\n"
        "Commands:\n"
        "/scrape - Begin member scraping\n"
        "/add_members - Add scraped members to target group"
    )

@bot.on(events.NewMessage(pattern='/scrape'))
async def scrape_members(event):
    user_id = event.sender_id
    user_sessions[user_id] = {'step': 'waiting_source'}
    await event.respond("Send the source group username or link:")

@bot.on(events.NewMessage)
async def handle_messages(event):
    user_id = event.sender_id
    text = event.text
    
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    
    if session['step'] == 'waiting_source':
        try:
            entity = await bot.get_entity(text)
            if not hasattr(entity, 'participants_count'):
                await event.respond("❌ Not a group/channel or access denied")
                return
                
            members = []
            async for user in bot.iter_participants(entity):
                members.append(f"{user.id} - {user.first_name}")
                
            session['members'] = members
            session['source'] = text
            session['step'] = 'waiting_target'
            
            await event.respond(
                f"Found {len(members)} members:\n\n" +
                "\n".join(members[:10]) +  # Show first 10 as sample
                f"\n\n...and {len(members)-10} more\n\n"
                "Send target group username or link:"
            )
            
        except Exception as e:
            await event.respond(f"Error: {str(e)}")

    elif session['step'] == 'waiting_target':
        try:
            target = await bot.get_entity(text)
            session['target'] = text
            session['step'] = 'ready'
            
            await event.respond(
                f"Ready to add {len(session['members'])} members to {text}\n"
                "Type /add_members to proceed or /cancel to abort"
            )
            
        except Exception as e:
            await event.respond(f"Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/add_members'))
async def add_members(event):
    user_id = event.sender_id
    if user_id not in user_sessions or user_sessions[user_id]['step'] != 'ready':
        return
    
    session = user_sessions[user_id]
    await event.respond("⚠️ Starting member addition (this may take a while)...")
    
    try:
        target = await bot.get_entity(session['target'])
        added = 0
        failed = 0
        
        for member_info in session['members']:
            try:
                user_id = int(member_info.split(' - ')[0])
                await bot(InviteToChannelRequest(
                    channel=target,
                    users=[user_id]
                ))
                added += 1
                await asyncio.sleep(15)  # Avoid rate limits
            except Exception as e:
                failed += 1
                
        await event.respond(
            f"Operation complete:\n"
            f"Added: {added}\n"
            f"Failed: {failed}"
        )
        
    except Exception as e:
        await event.respond(f"Critical error: {str(e)}")
    
    del user_sessions[user_id]

print("Bot running...")
bot.run_until_disconnected()
