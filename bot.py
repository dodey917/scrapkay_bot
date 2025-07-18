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

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# User management
user_sessions = {}
verified_users = set()
scraped_data = {}

class BotStates:
    MAIN_MENU = 0
    AWAITING_SOURCE = 1
    SCRAPING_OPTIONS = 2
    AWAITING_PHONE = 3
    LISTING_DATA = 4

async def create_keyboard(buttons):
    """Create a reply keyboard markup"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text=button)] for button in buttons],
        resize=True,
        selective=True
    )

async def show_main_menu(event):
    """Display the main menu"""
    buttons = ['🚀 Start Scraping', '📋 List Scraped Data', '🔐 Verify Phone', 'ℹ️ Bot Status']
    await event.respond(
        "🤖 **Advanced Member Scraper Bot**\n\n"
        "Select an option:",
        buttons=await create_keyboard(buttons)
    )

async def show_cancel_menu(event, message):
    """Display a message with cancel option"""
    await event.respond(
        message,
        buttons=await create_keyboard(['❌ Cancel'])
    )

async def scrape_members(client, entity):
    """Powerful scraping function that doesn't require bot to join group"""
    try:
        participants = []
        async for user in client.iter_participants(entity):
            if user.username:
                participants.append(f"@{user.username}")
            elif user.phone:
                participants.append(f"Phone: {user.phone}")
            else:
                participants.append(f"User ID: {user.id}")
        return participants
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return None

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
    await show_cancel_menu(event, "🔍 Please send the group username or link you want to scrape:")

@bot.on(events.NewMessage(pattern='📋 List Scraped Data'))
async def list_data_handler(event):
    """Handle listing scraped data"""
    user_id = event.sender_id
    if user_id in scraped_data:
        user_sessions[user_id] = {'state': BotStates.LISTING_DATA}
        buttons = list(scraped_data[user_id].keys()) + ['❌ Cancel']
        await event.respond(
            "📁 Your scraped data:\nSelect an item to view:",
            buttons=await create_keyboard(buttons)
        )
    else:
        await event.respond("You haven't scraped any data yet")

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
        f"📊 Data collected: {sum(len(v) for v in scraped_data.values())} records\n"
        f"🔄 Last restart: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await event.respond(status_msg)

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
        try:
            await event.respond("🔄 Starting scraping process...")
            entity = await bot.get_entity(text)
            members = await scrape_members(bot, entity)
            
            if members:
                if user_id not in scraped_data:
                    scraped_data[user_id] = {}
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                scraped_data[user_id][f"Scraped {timestamp}"] = members
                
                await show_main_menu(event)
                await event.respond(
                    f"✅ Successfully scraped {len(members)} members!\n"
                    f"Use '📋 List Scraped Data' to view your results"
                )
            else:
                await event.respond("❌ Failed to scrape members. Please try again")
            
            del user_sessions[user_id]
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            await event.respond("❌ Error scraping group. Please check the link/username and try again")
            del user_sessions[user_id]
    
    elif session['state'] == BotStates.LISTING_DATA:
        if text in scraped_data[user_id]:
            data = scraped_data[user_id][text]
            chunk_size = 50
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                await event.respond("\n".join(chunk))
            await show_main_menu(event)
            del user_sessions[user_id]
        elif text != '❌ Cancel':
            await event.respond("Please select a valid option from the list")

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
