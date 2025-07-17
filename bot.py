import os
import time
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardHide
)

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
verified_users = set()

class BotStates:
    MAIN_MENU = 0
    AWAITING_SOURCE = 1
    AWAITING_TARGET = 2
    AWAITING_PHONE = 3

async def create_keyboard(buttons):
    """Create a reply keyboard markup"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text=button)] for button in buttons],
        resize=True,
        selective=True
    )

async def show_main_menu(event):
    """Display the main menu"""
    buttons = ['🚀 Start Scraping', '📞 Contact Owner', '🔐 Verify Phone', 'ℹ️ Bot Status']
    await event.respond(
        "🤖 **Member Manager Bot**\n\n"
        "Select an option:",
        buttons=await create_keyboard(buttons)
    )

async def show_cancel_menu(event, message):
    """Display a message with cancel option"""
    await event.respond(
        message,
        buttons=await create_keyboard(['❌ Cancel'])
    )

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command"""
    await show_main_menu(event)

@bot.on(events.NewMessage(pattern='🚀 Start Scraping'))
async def start_scraping_handler(event):
    """Handle scraping initiation"""
    user_id = event.sender_id
    
    if user_id not in verified_users:
        await event.respond("🔒 Please verify your phone first")
        return
    
    user_sessions[user_id] = {'state': BotStates.AWAITING_SOURCE}
    await show_cancel_menu(event, "🔍 Please send the SOURCE group username or link:")

@bot.on(events.NewMessage(pattern='🔐 Verify Phone'))
async def verify_phone_handler(event):
    """Handle phone verification"""
    user_id = event.sender_id
    user_sessions[user_id] = {'state': BotStates.AWAITING_PHONE}
    await show_cancel_menu(event, "📱 Please send your phone number in international format (e.g., +1234567890):")

@bot.on(events.NewMessage(pattern='ℹ️ Bot Status'))
async def status_handler(event):
    """Handle status request"""
    status_msg = (
        "🤖 **Bot Status**\n\n"
        f"👥 Active sessions: {len(user_sessions)}\n"
        f"✅ Verified users: {len(verified_users)}\n"
        f"🔄 Last restart: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await event.respond(status_msg)

@bot.on(events.NewMessage(pattern='📞 Contact Owner'))
async def contact_handler(event):
    """Handle contact request"""
    await event.respond(f"📩 Contact the owner @{OWNER_USERNAME} for support")

@bot.on(events.NewMessage(pattern='❌ Cancel'))
async def cancel_handler(event):
    """Handle operation cancellation"""
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await show_main_menu(event)
    await event.respond("❌ Operation cancelled")

@bot.on(events.NewMessage)
async def message_handler(event):
    """Handle all other messages"""
    user_id = event.sender_id
    text = event.text.strip()
    
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    
    if session['state'] == BotStates.AWAITING_PHONE:
        if text.startswith('+') and text[1:].isdigit() and len(text) > 5:
            verified_users.add(user_id)
            del user_sessions[user_id]
            await show_main_menu(event)
            await event.respond("✅ Verification successful! You can now start scraping")
        else:
            await event.respond("❌ Invalid format. Please use international format (e.g., +1234567890)")
    
    elif session['state'] == BotStates.AWAITING_SOURCE:
        session['source'] = text
        session['state'] = BotStates.AWAITING_TARGET
        await show_cancel_menu(event, "🎯 Please send the TARGET group username or link:")
    
    elif session['state'] == BotStates.AWAITING_TARGET:
        session['target'] = text
        del user_sessions[user_id]
        
        # Here you would add your actual scraping logic
        await show_main_menu(event)
        await event.respond(
            f"🚀 Starting scraping process...\n"
            f"Source: {session['source']}\n"
            f"Target: {session['target']}\n\n"
            "This may take several minutes..."
        )
        
        # Example scraping implementation (replace with your actual code)
        try:
            # Simulate scraping
            await asyncio.sleep(2)
            await event.respond("🔄 Scraping members...")
            await asyncio.sleep(3)
            await event.respond("✅ Successfully scraped 150 members")
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            await event.respond("❌ Scraping failed. Please try again later")

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
