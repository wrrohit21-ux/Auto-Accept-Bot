# Telegram Auto-Request-Accept Bot

Features:
- Auto-approve join requests for bound group(s).
- Bind group with `/setgroup` (run inside the group as admin).
- Enable/disable with `/enable` and `/disable`.
- One-off bulk accept script included.

## Setup

1. Create a bot with @BotFather and get `BOT_TOKEN`.
2. (Optional) Get `TELETHON_API_ID` and `TELETHON_API_HASH` from my.telegram.org for bulk accept script.
3. Set environment variables:
   - `BOT_TOKEN` (required)
   - `DB_PATH` (optional, default `./bot.db`)
   - `TELETHON_API_ID`, `TELETHON_API_HASH`, `TARGET_CHAT_ID` for `bulk_accept.py`.
4. Run locally:
   ```bash
   pip install -r requirements.txt
   export BOT_TOKEN="123:ABC..."
   python main.py
