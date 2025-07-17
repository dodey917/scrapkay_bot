import os
import time
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InputPeerUser,
    InputPeerChannel
)

# Configuration
API_ID = int(os.getenv('API_ID', 17752898))
API_HASH = os.getenv('API_HASH', '899d5b7bb6c1a3672d822256bffac2a3')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7621816424:AAE3m2GDw6drXN4d-o8QNHv4cgpHr0L9YG0')
OWNER_USERNAME = os.getenv('OWNER_USERNAME', 'freeblezzy')

# User management
user_sessions = {}
user_limits = {}
banned_users = {}
verified_numbers = set()

# Menu system - FIXED: Properly structured for Telethon
def create_main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton(text='🚀 Start Scraping'), KeyboardButton(text='📞 Contact Owner')],
        [KeyboardButton(text='🔐 Verify Phone'), KeyboardButton(text='ℹ️ Bot Status')]
    ])

def create_cancel_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton(text='❌ Cancel')]
    ])

# Initialize bot
bot = TelegramClient('member_manager', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Welcome message with main menu"""
    await event.respond(
        f"🤖 **Advanced Member Manager Bot**\n\n"
        f"Owner: @{OWNER_USERNAME}\n"
        "🔒 Verified users only\n"
        "⏳ Rate limited for safety\n\n"
        "Please verify your phone number to begin:",
        buttons=create_main_menu()
    )

@bot.on(events.NewMessage(pattern='🔐 Verify Phone'))
async def verify_phone(event):
    """Phone verification initiation"""
    user_sessions[event.sender_id] = {'step': 'awaiting_phone'}
    await event.respond(
        "📱 Please send your phone number in international format:\n"
        "Example: +12345678900\n\n"
        "This verification helps prevent abuse.",
        buttons=create_cancel_menu()
    )

@bot.on(events.NewMessage(pattern='📞 Contact Owner'))
async def contact_owner(event):
    """Contact information"""
    await event.respond(
        f"👨‍💻 Bot Owner: @{OWNER_USERNAME}\n"
        "For support or questions, please contact the owner directly.",
        buttons=create_main_menu()
    )

@bot.on(events.NewMessage(pattern='ℹ️ Bot Status'))
async def bot_status(event):
    """System status information"""
    user_id = event.sender_id
    status = []
    
    if user_id in banned_users:
        ban_time = banned_users[user_id]['unban_time'] - time.time()
        status.append(f"⛔ Currently banned: {int(ban_time/60)} minutes remaining")
    
    if user_id in user_limits:
        status.append(f"🔄 Used {user_limits[user_id]['count']}/50 adds this hour")
    
    status_msg = "\n".join(status) if status else "✅ Account in good standing"
    
    await event.respond(
        f"📊 Your Account Status:\n{status_msg}\n\n"
        f"🌍 Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        buttons=create_main_menu()
    )

@bot.on(events.NewMessage(pattern='🚀 Start Scraping'))
async def start_scraping(event):
    """Begin the scraping process"""
    user_id = event.sender_id
    
    # Check verification
    if user_id not in verified_numbers:
        await event.respond("Please verify your phone number first", buttons=create_main_menu())
        return
    
    # Check ban status
    if user_id in banned_users:
        if time.time() < banned_users[user_id]['unban_time']:
            remaining = int((banned_users[user_id]['unban_time'] - time.time())/60)
            await event.respond(f"⏳ Ban expires in {remaining} minutes", buttons=create_main_menu())
            return
        del banned_users[user_id]
    
    user_sessions[user_id] = {'step': 'awaiting_source'}
    await event.respond(
        "🔍 Please send the SOURCE group username or link:\n"
        "(Must be public group or channel)",
        buttons=create_cancel_menu()
    )

@bot.on(events.NewMessage)
async def handle_messages(event):
    """Main message handler"""
    user_id = event.sender_id
    text = event.text.strip()
    
    # Cancel handler
    if text == '❌ Cancel':
        if user_id in user_sessions:
            del user_sessions[user_id]
        await event.respond("Operation cancelled", buttons=create_main_menu())
        return
    
    # Phone verification flow
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'awaiting_phone':
        if text.startswith('+') and text[1:].isdigit() and len(text) > 8:
            verified_numbers.add(user_id)
            user_sessions[user_id] = {'verified': True}
            await event.respond(
                f"✅ Verified: {text}\n"
                "You can now use all bot features",
                buttons=create_main_menu()
            )
        else:
            await event.respond("Invalid phone format. Please use +[countrycode][number]")
        return
    
    # Scraping flow
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'awaiting_source':
        try:
            entity = await bot.get_entity(text)
            if not hasattr(entity, 'participants_count'):
                await event.respond("This doesn't appear to be a group/channel")
                return
            
            user_sessions[user_id].update({
                'source': entity,
                'step': 'awaiting_target'
            })
            await event.respond(
                f"✅ Source set: {entity.title}\n"
                "Now please send the TARGET group username or link:",
                buttons=create_cancel_menu()
            )
        except Exception as e:
            await event.respond(f"Error: {str(e)}")
            return
    
    elif user_id in user_sessions and user_sessions[user_id].get('step') == 'awaiting_target':
        try:
            entity = await bot.get_entity(text)
            if not hasattr(entity, 'participants_count'):
                await event.respond("This doesn't appear to be a group/channel")
                return
            
            user_sessions[user_id].update({
                'target': entity,
                'step': 'awaiting_count'
            })
            await event.respond(
                f"✅ Target set: {entity.title}\n"
                "How many members would you like to process? (Max 50):",
                buttons=create_cancel_menu()
            )
        except Exception as e:
            await event.respond(f"Error: {str(e)}")
            return
    
    elif user_id in user_sessions and user_sessions[user_id].get('step') == 'awaiting_count':
        if not text.isdigit() or not (1 <= int(text) <= 50):
            await event.respond("Please enter a number between 1-50")
            return
        
        count = int(text)
        session = user_sessions[user_id]
        
        # Check rate limits
        if user_id in user_limits:
            if user_limits[user_id]['count'] >= 50:
                banned_users[user_id] = {'unban_time': time.time() + 3600}  # 1 hour ban
                await event.respond(
                    "⛔ You've reached the hourly limit (50 adds)\n"
                    "Please try again in 1 hour",
                    buttons=create_main_menu()
                )
                return
            if time.time() - user_limits[user_id]['last_add'] < 300:  # 5 minute delay
                await event.respond("Please wait 5 minutes between operations")
                return
        
        # Begin processing
        await event.respond(f"⏳ Processing {count} members...")
        
        try:
            added = 0
            async for user in bot.iter_participants(session['source'], limit=count):
                try:
                    # Check if we need to update rate limits
                    if user_id not in user_limits:
                        user_limits[user_id] = {'count': 0, 'last_add': time.time()}
                    elif time.time() - user_limits[user_id]['last_add'] > 3600:
                        user_limits[user_id] = {'count': 0, 'last_add': time.time()}
                    
                    # Skip if we hit limits
                    if user_limits[user_id]['count'] >= 50:
                        break
                    
                    # Attempt to add user
                    await bot(InviteToChannelRequest(
                        channel=session['target'],
                        users=[user]
                    ))
                    
                    added += 1
                    user_limits[user_id]['count'] += 1
                    user_limits[user_id]['last_add'] = time.time()
                    
                    # Respect rate limits
                    if added < count:
                        await asyncio.sleep(300)  # 5 minute delay
                    
                except Exception as e:
                    continue
            
            await event.respond(
                f"✅ Completed!\n"
                f"Successfully added {added} members\n"
                f"Hourly usage: {user_limits[user_id]['count']}/50\n\n"
                "Thank you for using our service!",
                buttons=create_main_menu()
            )
            
        except Exception as e:
            await event.respond(f"Critical error: {str(e)}", buttons=create_main_menu())
        
        finally:
            if user_id in user_sessions:
                del user_sessions[user_id]

if __name__ == '__main__':
    print("Bot started successfully!")
    bot.run_until_disconnected()
