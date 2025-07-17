import os
import time
import asyncio
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import KeyboardButton, ReplyKeyboardMarkup

# Configuration
API_ID = 17752898
API_HASH = '899d5b7bb6c1a3672d822256bffac2a3'
BOT_TOKEN = '7621816424:AAE3m2GDw6drXN4d-o8QNHv4cgpHr0L9YG0'
OWNER_USERNAME = 'freeblezzy'

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# User management
user_sessions = {}
user_limits = {}
banned_users = {}
verified_numbers = set()

# Rate limiting
RATE_LIMIT = {
    'scraping': {'count': 5, 'window': 3600},  # 5 scrapes/hour
    'messages': {'count': 20, 'window': 300}   # 20 messages/5 minutes
}

bot = TelegramClient('member_manager', API_ID, API_HASH)

async def safe_respond(event, message, parse_mode='md'):
    """Safe message responder"""
    try:
        await event.respond(message, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Error sending message: {e}")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Start command handler"""
    user_id = event.sender_id
    
    if user_id in banned_users and time.time() < banned_users[user_id]['unban_time']:
        remaining = int((banned_users[user_id]['unban_time'] - time.time()) / 60)
        await safe_respond(event, f"⛔ Banned. Try again in {remaining:.0f} minutes.")
        return
    
    await safe_respond(
        event,
        f"🤖 **Member Manager Bot**\n\n"
        f"Owner: @{OWNER_USERNAME}\n"
        "🔒 Verified users only\n"
        "⏳ Rate limited for safety\n\n"
        "Available commands:\n"
        "/start - Show this message\n"
        "/scrape - Start scraping\n"
        "/verify - Verify your phone\n"
        "/status - Bot status"
    )

@bot.on(events.NewMessage(pattern='/scrape'))
async def start_scraping(event):
    """Scraping handler"""
    user_id = event.sender_id
    
    if user_id not in verified_numbers:
        await safe_respond(event, "🔒 Please verify your phone first using /verify")
        return
    
    if await is_rate_limited(user_id, 'scraping'):
        await safe_respond(event, "⚠️ Rate limit exceeded. Try again later.")
        return
    
    user_sessions[user_id] = {'step': 'awaiting_source'}
    await safe_respond(event, "🔍 Send SOURCE group username or link:")

@bot.on(events.NewMessage(pattern='/verify'))
async def verify_phone(event):
    """Phone verification handler"""
    user_id = event.sender_id
    user_sessions[user_id] = {'step': 'awaiting_phone'}
    await safe_respond(event, "📱 Send your phone number in international format (e.g., +1234567890):")

@bot.on(events.NewMessage(pattern='/status'))
async def bot_status(event):
    """Bot status handler"""
    status_msg = (
        "🤖 **Bot Status**\n\n"
        f"👥 Users in session: {len(user_sessions)}\n"
        f"✅ Verified users: {len(verified_numbers)}\n"
        f"⛔ Banned users: {len(banned_users)}\n\n"
        f"🔄 Last restart: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await safe_respond(event, status_msg)

@bot.on(events.NewMessage(pattern='/cancel'))
async def cancel(event):
    """Cancel handler"""
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await safe_respond(event, "❌ Operation cancelled")

@bot.on(events.NewMessage)
async def handle_messages(event):
    """Main message handler"""
    user_id = event.sender_id
    text = event.text.strip()
    
    if user_id in user_sessions:
        session = user_sessions[user_id]
        
        if session.get('step') == 'awaiting_phone':
            if text.startswith('+') and text[1:].isdigit():
                verified_numbers.add(user_id)
                del user_sessions[user_id]
                await safe_respond(event, "✅ Phone number verified! You can now use /scrape")
            else:
                await safe_respond(event, "❌ Invalid format. Please use international format (e.g., +1234567890)")
        
        elif session.get('step') == 'awaiting_source':
            session['source'] = text
            session['step'] = 'awaiting_target'
            await safe_respond(event, "🎯 Send TARGET group username or link:")
        
        elif session.get('step') == 'awaiting_target':
            session['target'] = text
            del user_sessions[user_id]
            await safe_respond(
                event,
                f"🔍 Starting scrape...\nSource: {session['source']}\nTarget: {session['target']}\n\n"
                "This might take a while..."
            )
            # Add your scraping logic here

async def is_rate_limited(user_id, action_type):
    """Check rate limits"""
    now = time.time()
    if user_id not in user_limits:
        user_limits[user_id] = {}
    
    if action_type not in user_limits[user_id]:
        user_limits[user_id][action_type] = {'count': 0, 'window_start': now}
    
    limit = user_limits[user_id][action_type]
    config = RATE_LIMIT[action_type]
    
    if now - limit['window_start'] > config['window']:
        limit['count'] = 0
        limit['window_start'] = now
    
    if limit['count'] >= config['count']:
        return True
    
    limit['count'] += 1
    return False

async def main():
    """Main function"""
    try:
        await bot.start(bot_token=BOT_TOKEN)
        logger.info(f"Bot started as @{(await bot.get_me()).username}")
        await bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"Bot failed: {e}")
    finally:
        await bot.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
