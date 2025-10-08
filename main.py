#!/usr/bin/env python3
"""
Auto Request Accept Bot
Requirements:
 - python-telegram-bot v21+
 - sqlite3 (builtin)
Env:
 - BOT_TOKEN         (required) Telegram bot token from @BotFather
 - DB_PATH           (optional) path to sqlite db (default: ./bot.db)
"""

import os
import sqlite3
import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    CommandHandler,
    ContextTypes,
)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")

DB_PATH = os.getenv("DB_PATH", "./bot.db")


# ---- Simple SQLite storage ----
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS groups (
        chat_id INTEGER PRIMARY KEY,
        enabled INTEGER DEFAULT 1,
        title TEXT
    )
    """
    )
    conn.commit()
    conn.close()


def enable_group(chat_id: int, title: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO groups (chat_id, enabled, title) VALUES (?, 1, ?)",
        (chat_id, title),
    )
    conn.commit()
    conn.close()


def disable_group(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE groups SET enabled = 0 WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def is_group_enabled(chat_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT enabled FROM groups WHERE chat_id = ?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row and row[0] == 1)


def remove_group(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM groups WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def list_groups():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT chat_id, enabled, title FROM groups")
    rows = cur.fetchall()
    conn.close()
    return rows


# ---- Bot handlers ----
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message(
        "Hello! I'm an Auto-Request-Accept bot.\n"
        "Use me by adding as admin to your private group and run /setgroup in the group (admin only). "
        "Admins can enable/disable with /enable or /disable. /help for more."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "/setgroup - bind this bot to this group (must run in the target group and be admin)\n"
        "/enable - enable auto-approve for this group (must be group admin)\n"
        "/disable - disable auto-approve for this group (must be group admin)\n"
        "/remove - unbind this group from the bot (must be group admin)\n"
        "/status - show allowed groups and status (bot owner or group admin)\n"
    )
    await update.effective_chat.send_message(txt)


def user_is_admin(update: Update, user_id: int) -> bool:
    """Check if user is admin in the chat (for commands executed in groups)."""
    try:
        chat = update.effective_chat
        member = chat.get_member(user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def setgroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # must be in group & invoked by admin
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ("group", "supergroup"):
        await update.effective_message.reply_text("Please run /setgroup inside the group you want to bind.")
        return

    if not user_is_admin(update, user.id):
        await update.effective_message.reply_text("You must be a group admin to run /setgroup.")
        return

    enable_group(chat.id, chat.title)
    await update.effective_message.reply_text(f"Group bound and enabled for auto-approve: {chat.title} ({chat.id})")


async def enable_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ("group", "supergroup"):
        await update.effective_message.reply_text("Use this command inside the bound group.")
        return
    if not user_is_admin(update, user.id):
        await update.effective_message.reply_text("Only group admin can enable.")
        return
    enable_group(chat.id, chat.title)
    await update.effective_message.reply_text("Auto-approve ENABLED for this group.")


async def disable_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ("group", "supergroup"):
        await update.effective_message.reply_text("Use this command inside the bound group.")
        return
    if not user_is_admin(update, user.id):
        await update.effective_message.reply_text("Only group admin can disable.")
        return
    disable_group(chat.id)
    await update.effective_message.reply_text("Auto-approve DISABLED for this group.")


async def remove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ("group", "supergroup"):
        await update.effective_message.reply_text("Use this command inside the bound group.")
        return
    if not user_is_admin(update, user.id):
        await update.effective_message.reply_text("Only group admin can remove binding.")
        return
    remove_group(chat.id)
    await update.effective_message.reply_text("This group is unbound from the bot.")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = list_groups()
    if not rows:
        await update.effective_message.reply_text("No groups are bound to this bot yet.")
        return
    lines = []
    for chat_id, enabled, title in rows:
        lines.append(f"- {title or 'unknown'} ({chat_id}) — {'ENABLED' if enabled else 'DISABLED'}")
    await update.effective_message.reply_text("Bound groups:\n" + "\n".join(lines))


async def handle_chat_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    chat_id = req.chat.id
    requester = req.from_user

    logger.info("Join request in %s from %s (%s)", req.chat.title, requester.full_name, requester.id)

    # Only handle if group is enabled
    if not is_group_enabled(chat_id):
        logger.info("Group %s (%s) is not enabled — ignoring", req.chat.title, chat_id)
        return

    # Approve
    try:
        await req.approve()
        logger.info("Approved %s (%s) for chat %s", requester.full_name, requester.id, chat_id)
        # Optional: welcome message in the group (requires bot send messages permission)
        try:
            await context.bot.send_message(chat_id, f"Welcome, {requester.mention_html()}!", parse_mode="HTML")
        except Exception:
            # ignore if cannot send message
            pass
    except Exception as e:
        logger.exception("Failed to approve join request: %s", e)


def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setgroup", setgroup_cmd))
    app.add_handler(CommandHandler("enable", enable_cmd))
    app.add_handler(CommandHandler("disable", disable_cmd))
    app.add_handler(CommandHandler("remove", remove_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    # Chat join requests
    app.add_handler(ChatJoinRequestHandler(handle_chat_join_request))

    logger.info("Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()

