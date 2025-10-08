#!/usr/bin/env python3
"""
Telegram Auto Request Accept Bot (Koyeb Ready)
"""

import os
import logging
from telethon import TelegramClient, events
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("AutoReqBot")

# Environment Variables
API_ID = int(os.getenv("26829892", "0"))
API_HASH = os.getenv("fcbc942ecc37b61a81d052a4b71de265")
BOT_TOKEN = os.getenv("8147350098:AAEFIvEvRXUTQEZvy9zC9sqQS2mfRRJGmAU")
ADMINS = [int(x) for x in os.getenv("ADMINS", "8257649811").split(",") if x]
DB_URL = os.getenv("mongodb+srv://yaxow33436_db_user:Q9buxBrK7ygR0lam@cluster11.80e2ait.mongodb.net/?retryWrites=true&w=majority&appName=Cluster11")  # MongoDB URI

if not all([API_ID, API_HASH, BOT_TOKEN, DB_URL]):
    log.error("Missing environment variables! Please set API_ID, API_HASH, BOT_TOKEN, DB_URL")
    exit(1)

# MongoDB client
mongo = MongoClient(DB_URL)
db = mongo["AutoReqAcceptBot"]
users_col = db["users"]

# Initialize Telegram bot
bot = TelegramClient("autoaccept_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.reply(
        "🤖 Auto Request Accept Bot is Online!\n"
        "Add me as admin with @wrrohit02'Approve Join Requests' permission."
    )

@bot.on(events.NewMessage(pattern='/ping'))
async def ping_handler(event):
    await event.reply("🏓 Pong! Bot is alive.")

@bot.on(events.Raw())
async def raw_handler(event):
    # Auto approve join requests
    try:
        if event._event.__class__.__name__ == "UpdateBotChatInviteRequester":
            req = event._event
            user_id = req.user_id
            chat_id = req.peer.channel_id if hasattr(req.peer, "channel_id") else None
            log.info(f"Approving join request: user={user_id}, chat={chat_id}")
            await bot(functions.messages.HideChatJoinRequestRequest(
                peer=chat_id,
                user_id=user_id,
                approved=True
            ))
            # Save user to MongoDB
            users_col.update_one({"user_id": user_id}, {"$set": {"chat_id": chat_id}}, upsert=True)
    except Exception as e:
        log.error(f"Failed to approve join request: {e}")

async def main():
    log.info("🤖 Bot is running...")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
