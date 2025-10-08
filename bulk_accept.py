#!/usr/bin/env python3
"""
Bulk accept chat join requests using Telethon (one-off)
Env:
 - TELETHON_API_ID
 - TELETHON_API_HASH
 - BOT_TOKEN           (can use bot token to start a bot session)
 - TARGET_CHAT_ID      (chat id or username, e.g. -1001234567890 or '@mygroup')
"""
import os
import asyncio
from telethon import TelegramClient

API_ID = int(os.getenv("26829892") or 0)
API_HASH = os.getenv("fcbc942ecc37b61a81d052a4b71de265")
BOT_TOKEN = os.getenv("8147350098:AAEFIvEvRXUTQEZvy9zC9sqQS2mfRRJGmAU")
TARGET_CHAT = os.getenv("8257649811")  # required

if not (API_ID and API_HASH and BOT_TOKEN and TARGET_CHAT):
    raise RuntimeError("Set TELETHON_API_ID, TELETHON_API_HASH, BOT_TOKEN, TARGET_CHAT_ID")

client = TelegramClient("bulk_accept", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


async def main():
    print("Fetching join requests for", TARGET_CHAT)
    async for req in client.iter_participants(TARGET_CHAT, filter= None):
        # iter_participants won't show join requests. Instead use get_chat_join_requests (telethon method)
        break

    # Telethon provides get_chat_join_requests via client.get_chat_join_requests
    requests = await client.get_chat_join_requests(TARGET_CHAT)
    print(f"Found {len(requests)} pending join requests")
    for r in requests:
        try:
            await client.approve_chat_join_request(TARGET_CHAT, r.user_id)
            print("Approved", r.user_id)
        except Exception as e:
            print("Failed to approve", r.user_id, e)


if __name__ == "__main__":
    asyncio.run(main())

