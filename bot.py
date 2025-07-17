from telethon.sync import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import asyncio

API_ID = 17752898
API_HASH = '899d5b7bb6c1a3672d822256bffac2a3'
BOT_TOKEN = '7621816424:AAE3m2GDw6drXN4d-o8QNHv4cgpHr0L9YG0'

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_sessions = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "📊 Group Member Lister Bot\n\n"
        "1. Send /list to begin\n"
        "2. I'll show available members\n"
        "3. You can export the list\n\n"
        "Note: I can only list members from groups where I'm added"
    )

@bot.on(events.NewMessage(pattern='/list'))
async def list_members(event):
    user_id = event.sender_id
    user_sessions[user_id] = {'step': 'waiting_group'}
    await event.respond("Please send me the group link you want to list members from:")

@bot.on(events.NewMessage)
async def handle_messages(event):
    user_id = event.sender_id
    text = event.text
    
    if user_id not in user_sessions:
        return
    
    if user_sessions[user_id]['step'] == 'waiting_group':
        if not text.startswith('https://t.me/'):
            await event.respond("❌ Please send a valid Telegram group link")
            return
            
        try:
            entity = await bot.get_entity(text)
            user_sessions[user_id]['group'] = entity
            user_sessions[user_id]['step'] = 'waiting_count'
            await event.respond("How many members do you want to list? (Max 200)")
        except Exception as e:
            await event.respond(f"❌ Error: {str(e)}")
            del user_sessions[user_id]
    
    elif user_sessions[user_id]['step'] == 'waiting_count':
        if not text.isdigit():
            await event.respond("Please enter a valid number")
            return
            
        count = min(int(text), 200)  # Telegram limitation
        try:
            group = user_sessions[user_id]['group']
            participants = await bot(GetParticipantsRequest(
                channel=group,
                filter=ChannelParticipantsSearch(''),
                offset=0,
                limit=count,
                hash=0
            ))
            
            member_list = "\n".join([f"{user.id}" for user in participants.users])
            user_sessions[user_id]['members'] = participants.users
            user_sessions[user_id]['step'] = 'ready'
            
            await event.respond(
                f"📋 Found {len(participants.users)} members:\n\n"
                f"{member_list}\n\n"
                "You can manually add these members to your group."
            )
            
        except Exception as e:
            await event.respond(f"❌ Failed to list members: {str(e)}")
        finally:
            del user_sessions[user_id]

print("Bot is running...")
bot.run_until_disconnected()
