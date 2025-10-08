#!/usr/bin/env python3
"""
Auto Request Accept Bot - Koyeb Ready Version
Based on MrMKN/Auto-ReqAccept-Bot
"""

import os
import logging
from telethon import TelegramClient, events

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("AutoReqBot")

# Read env vars
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_OR_GROUP_ID = os.getenv("CHANNEL_OR_GROUP_ID")  # e.g. -1001234567890 or @channelusername
SESSION_NAME = os.getenv("SESSION_NAME", "autoaccept_session")

if not all([API_ID, API_HASH, BOT_TOKEN, CHANNEL_OR_GROUP_ID]):
    log.error("Missing environment variables! Please set API_ID, API_HASH, BOT_TOKEN, CHANNEL_OR_GROUP_ID.")
    exit(1)

# Initialize Telethon bot client
bot = TelegramClient(SESSION_NAME, API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.reply("🤖 **Auto Request Accept Bot is Online!**\n\n"
                      "Add me to your private group or channel as **Admin** "
                      "with `Approve Join Requests` permission, and I’ll automatically approve all join requests!")

@bot.on(events.NewMessage(pattern='/ping'))
async def ping_handler(event):
    await event.reply("🏓 Pong! Bot is alive.")

@bot.on(events.ChatAction())
async def chat_action_handler(event):
    # Log joins/leaves (optional)
    pass

@bot.on(events.Raw())
async def raw_handler(event):
    # Auto approve join requests
    try:
        if event._event.__class__.__name__ == "UpdateBotChatInviteRequester":
            req = event._event
            user_id = req.user_id
            chat_id = req.peer.channel_id if hasattr(req.peer, 'channel_id') else CHANNEL_OR_GROUP_ID

            log.info(f"Approving join request: user={user_id}, chat={chat_id}")
            await bot(functions.messages.HideChatJoinRequestRequest(
                peer=CHANNEL_OR_GROUP_ID,
                user_id=user_id,
                approved=True
            ))
    except Exception as e:
        log.error(f"Failed to auto approve join request: {e}")

async def main():
    log.info("🤖 Auto Request Accept Bot is running...")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
