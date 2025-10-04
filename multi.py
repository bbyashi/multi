import os
import json
import asyncio
from pyrogram import Client, errors
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === CONFIG ===
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
STRINGS_FILE = "strings.json"

# === Load/Save Sessions ===
def load_strings():
    if os.path.exists(STRINGS_FILE):
        with open(STRINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("strings", [])
    return []

def save_strings(strings):
    with open(STRINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"strings": strings}, f, indent=2)

STRINGS = load_strings()
clients = []

# === Start Pyrogram clients (async-safe) ===
async def start_clients():
    for i, s in enumerate(STRINGS):
        try:
            c = Client(f"acc{i+1}", api_id=API_ID, api_hash=API_HASH, session_string=s, no_updates=True)
            await c.start()
            clients.append(c)
            me = await c.get_me()
            print(f"✅ Started: {me.first_name} (@{me.username})")
        except Exception as e:
            print(f"❌ Failed session {i+1}: {e}")

# === Admin decorator ===
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            return await update.message.reply_text("🚫 You are not authorized!")
        return await func(update, context)
    return wrapper

# === Telegram Commands ===
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌸 Welcome to Multi Session Bot 🌸\n\n"
        "/group <msg> - send to all groups\n"
        "/user <msg> - send to all personal chats\n"
        "/join <link> - join link with all accounts\n"
        "/leave <link> - leave specific group/channel\n"
        "/status - check active sessions\n"
        "/add_session <string> - add new session\n"
        "/list_sessions - list all connected IDs"
    )
    await update.message.reply_text(text)

@admin_only
async def group_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("⚠️ Usage: /group <message>")
    await update.message.reply_text("🚀 Sending to all groups...")
    for c in clients:
        try:
            async for d in c.get_dialogs():
                if d.chat.type in ["group", "supergroup"]:
                    await c.send_message(d.chat.id, msg)
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"Group send error: {e}")
    await update.message.reply_text("✅ Done sending to groups.")

@admin_only
async def user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("⚠️ Usage: /user <message>")
    await update.message.reply_text("💬 Sending to all users...")
    for c in clients:
        try:
            async for d in c.get_dialogs():
                if d.chat.type=="private":
                    await c.send_message(d.chat.id, msg)
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"User send error: {e}")
    await update.message.reply_text("✅ Done sending to users.")

@admin_only
async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /join <link>")
    link = context.args[0]
    await update.message.reply_text(f"🔗 Joining {link} ...")
    for c in clients:
        try:
            await c.join_chat(link)
            await asyncio.sleep(3)
        except errors.FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Join error: {e}")
    await update.message.reply_text("✅ All joined.")

@admin_only
async def leave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /leave <link>")
    link = context.args[0]
    await update.message.reply_text(f"🚪 Leaving {link} ...")
    success, failed = 0,0
    for c in clients:
        try:
            await c.leave_chat(link)
            await asyncio.sleep(5)
            success+=1
        except errors.FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Leave error: {e}")
            failed+=1
    await update.message.reply_text(f"✅ Left {success} sessions\n❌ Failed: {failed}")

@admin_only
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"📊 Total Sessions: {len(clients)}\n\n"
    for i,c in enumerate(clients,start=1):
        try:
            me = await c.get_me()
            text += f"{i}. {me.first_name} (@{me.username or 'no_username'})\n"
        except: text += f"{i}. ❌ Error\n"
    await update.message.reply_text(text)

@admin_only
async def add_session_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = " ".join(context.args).strip()
    if not s:
        return await update.message.reply_text("Usage: /add_session <string_session>")
    msg = await update.message.reply_text("🔐 Adding session...")
    try:
        c = Client(f"acc{len(clients)+1}", api_id=API_ID, api_hash=API_HASH, session_string=s, no_updates=True)
        await c.start()
        clients.append(c)
        STRINGS.append(s)
        save_strings(STRINGS)
        me = await c.get_me()
        await msg.edit_text(f"✅ Added: {me.first_name} (@{me.username or 'no_username'})")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

@admin_only
async def list_sessions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines=[]
    for i,c in enumerate(clients,start=1):
        try:
            me=await c.get_me()
            lines.append(f"{i}. {me.first_name} (@{me.username or 'no_username'}) — `{me.id}`")
        except:
            lines.append(f"{i}. ❌ Error")
    header=f"🔎 Connected: {len(clients)} | Saved: {len(STRINGS)}\n\n"
    await update.message.reply_markdown(header + "\n".join(lines) if lines else header + "No sessions.")

# === RUN BOT (Heroku-safe) ===
if __name__=="__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_clients())  # start Pyrogram clients first

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("group", group_cmd))
    app.add_handler(CommandHandler("user", user_cmd))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CommandHandler("leave", leave_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("add_session", add_session_cmd))
    app.add_handler(CommandHandler("list_sessions", list_sessions_cmd))

    app.run_polling()  # synchronous, Heroku-safe
