import os
import time
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import InputPeerUser, InputPeerChannel

# Configuration - Replace these with your actual credentials
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
banned_users = {}
verified_users = set()

class BotCommands:
    START = '/start'
    SCRAPE = '/scrape'
    VERIFY = '/verify'
    STATUS = '/status'
    CANCEL = '/cancel'

async def send_message(event, text):
    """Safe message sending with error handling"""
    try:
        await event.respond(text)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

@bot.on(events.NewMessage(pattern=f'^{BotCommands.START}'))
async def start_handler(event):
    """Handle /start command"""
    help_text = (
        "🤖 **Member Manager Bot**\n\n"
        f"👤 Owner: @{OWNER_USERNAME}\n"
        "🔒 Verified users only\n\n"
        "Available commands:\n"
        "/start - Show this message\n"
        "/verify - Verify your phone\n"
        "/scrape - Start scraping\n"
        "/status - Check bot status\n"
        "/cancel - Cancel current operation"
    )
    await send_message(event, help_text)

@bot.on(events.NewMessage(pattern=f'^{BotCommands.VERIFY}'))
async def verify_handler(event):
    """Handle phone verification"""
    user_id = event.sender_id
    user_sessions[user_id] = {'step': 'awaiting_phone'}
    await send_message(event, "📱 Please send your phone number in international format (e.g., +1234567890):")

@bot.on(events.NewMessage(pattern=f'^{BotCommands.SCRAPE}'))
async def scrape_handler(event):
    """Handle scraping initiation"""
    user_id = event.sender_id
    
    if user_id not in verified_users:
        await send_message(event, "🔒 Please verify your phone first using /verify")
        return
    
    user_sessions[user_id] = {'step': 'awaiting_source'}
    await send_message(event, "🔍 Please send the SOURCE group username or link:")

@bot.on(events.NewMessage(pattern=f'^{BotCommands.STATUS}'))
async def status_handler(event):
    """Handle status request"""
    status_msg = (
        "🤖 **Bot Status**\n\n"
        f"👥 Active sessions: {len(user_sessions)}\n"
        f"✅ Verified users: {len(verified_users)}\n"
        f"⛔ Banned users: {len(banned_users)}\n"
        f"🔄 Last restart: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await send_message(event, status_msg)

@bot.on(events.NewMessage(pattern=f'^{BotCommands.CANCEL}'))
async def cancel_handler(event):
    """Handle operation cancellation"""
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await send_message(event, "❌ Operation cancelled")

@bot.on(events.NewMessage)
async def message_handler(event):
    """Handle all other messages"""
    user_id = event.sender_id
    text = event.text.strip()
    
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    
    if session.get('step') == 'awaiting_phone':
        if text.startswith('+') and text[1:].isdigit() and len(text) > 5:
            verified_users.add(user_id)
            del user_sessions[user_id]
            await send_message(event, "✅ Verification successful! You can now use /scrape")
        else:
            await send_message(event, "❌ Invalid format. Please use international format (e.g., +1234567890)")
    
    elif session.get('step') == 'awaiting_source':
        session['source'] = text
        session['step'] = 'awaiting_target'
        await send_message(event, "🎯 Please send the TARGET group username or link:")
    
    elif session.get('step') == 'awaiting_target':
        session['target'] = text
        del user_sessions[user_id]
        
        # Here you would add your actual scraping logic
        await send_message(
            event,
            f"🚀 Starting scraping process...\n"
            f"Source: {session['source']}\n"
            f"Target: {session['target']}\n\n"
            "This may take several minutes..."
        )

async def main():
    """Main application entry point"""
    try:
        await bot.start(bot_token=BOT_TOKEN)
        logger.info(f"Bot started as @{(await bot.get_me()).username}")
        await bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
    finally:
        await bot.disconnect()

if __name__ == '__main__':
    bot = TelegramClient('member_manager', API_ID, API_HASH)
    asyncio.run(main())
