from telethon.sync import TelegramClient, events
import asyncio

API_ID = 17752898
API_HASH = '899d5b7bb6c1a3672d822256bffac2a3'
BOT_TOKEN = '7621816424:AAE3m2GDw6drXN4d-o8QNHv4cgpHr0L9YG0'

bot = TelegramClient('member_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "🔹 Legal Member Management Bot 🔹\n\n"
        "I can help with PUBLIC group member management when:\n"
        "1. You're admin in the target group\n"
        "2. Users have allowed group invites\n\n"
        "Commands:\n"
        "/list_members - View public group members\n"
        "/generate_invite - Create invite links\n"
        "/help - More info"
    )

@bot.on(events.NewMessage(pattern='/list_members'))
async def list_members(event):
    """List members from groups where bot has access"""
    await event.respond("Please send the public group username (e.g. @publicgroup):")

    @bot.on(events.NewMessage)
    async def handle_group_input(event):
        try:
            group = await bot.get_entity(event.text)
            if not hasattr(group, 'participants_count'):
                await event.respond("This doesn't appear to be a group")
                return

            members = []
            async for user in bot.iter_participants(group, limit=50):  # Small limit for demo
                if user.username:
                    members.append(f"@{user.username}")
                else:
                    members.append(f"user{user.id}")

            await event.respond(
                f"First 50 members in {event.text}:\n" + 
                "\n".join(members) +
                "\n\nNote: I can only display public information. " +
                "To add members, you must be a group admin."
            )
            
        except Exception as e:
            await event.respond(f"Error: {str(e)}")

        # Remove this handler after use
        bot.remove_event_handler(handle_group_input)

@bot.on(events.NewMessage(pattern='/generate_invite'))
async def create_invite(event):
    """For groups where user is admin"""
    await event.respond(
        "To create an invite link for your group:\n"
        "1. Make me an admin in your group\n"
        "2. Use Telegram's native 'Generate Invite Link' feature\n\n"
        "I cannot generate invites without admin rights."
    )

print("Bot running (legal version)...")
bot.run_until_disconnected()
