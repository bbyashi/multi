import asyncio
import os
import json
from pyrogram import Client, errors
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === CONFIG ===
API_ID = 123456  # apna API_ID daal
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"
ADMIN_ID = 123456789  # sirf admin ID ko access milega

STRINGS_FILE = "strings.json"

# === Load/Save System ===
def load_strings_from_file():
    if os.path.exists(STRINGS_FILE):
        try:
            with open(STRINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            strings = data.get("strings", [])
            print(f"Loaded {len(strings)} session(s).")
            return strings
        except Exception as e:
            print("❌ Error loading strings:", e)
            return []
    return []

def save_strings_to_file(strings_list):
    try:
        with open(STRINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"strings": strings_list}, f, indent=2)
        return True
    except Exception as e:
        print("❌ Error saving strings:", e)
        return False


STRINGS = load_strings_from_file()

clients = []

# === Start all sessions at launch ===
async def start_all_clients():
    for i, string in enumerate(STRINGS):
        try:
            c = Client(f"acc{i+1}", api_id=API_ID, api_hash=API_HASH, session_string=string, no_updates=True)
            await c.start()
            me = await c.get_me()
            clients.append(c)
            print(f"✅ Started: {me.first_name} (@{me.username})")
        except Exception as e:
            print(f"❌ Failed to start session {i+1}: {e}")


# === BOT COMMANDS ===
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌸 **Welcome to Multi Session Bot** 🌸\n\n"
        "Use the following commands:\n"
        "• `/group <msg>` - send to all groups\n"
        "• `/user <msg>` - send to all personal chats\n"
        "• `/join <link>` - join link with all accounts\n"
        "• `/leave` - leave all joined groups\n"
        "• `/status` - check active sessions\n"
        "• `/add_session <string>` - add new session\n"
        "• `/list_sessions` - list all connected IDs"
    )
    await update.message.reply_markdown(text)


async def group_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("⚠️ Usage: /group <message>")

    await update.message.reply_text("🚀 Sending to all groups...")
    for c in clients:
        try:
            async for dialog in c.get_dialogs():
                if dialog.chat.type in ["supergroup", "group"]:
                    await c.send_message(dialog.chat.id, msg)
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"Group send error: {e}")
    await update.message.reply_text("✅ Message sent to all groups.")


async def user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("⚠️ Usage: /user <message>")

    await update.message.reply_text("💬 Sending to all users...")
    for c in clients:
        try:
            async for dialog in c.get_dialogs():
                if dialog.chat.type == "private":
                    await c.send_message(dialog.chat.id, msg)
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"User send error: {e}")
    await update.message.reply_text("✅ Message sent to all users.")


async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
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
    await update.message.reply_text("✅ All joined successfully.")


async def leave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /leave <group_link>")

    link = context.args[0]
    await update.message.reply_text(f"🚪 Leaving {link} from all sessions...")

    success, failed = 0, 0
    for c in clients:
        try:
            await c.leave_chat(link)
            await asyncio.sleep(5)
            success += 1
        except errors.FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Leave error: {e}")
            failed += 1

    await update.message.reply_text(
        f"✅ Left {success} sessions successfully.\n❌ Failed: {failed}"
    )



async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = f"📊 Total Sessions: {len(clients)}\n\n"
    for i, c in enumerate(clients, start=1):
        try:
            me = await c.get_me()
            text += f"{i}. {me.first_name} (@{me.username or 'no_username'})\n"
        except:
            text += f"{i}. ❌ Error fetching\n"
    await update.message.reply_text(text)


# === ADD SESSION Command ===
async def add_session_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Unauthorized.")
    session_str = " ".join(context.args).strip()
    if not session_str:
        return await update.message.reply_text("Usage: /add_session <string_session>")

    msg = await update.message.reply_text("🔐 Adding session... please wait.")
    idx = len(clients) + 1
    session_name = f"acc{idx}"
    try:
        new_client = Client(session_name, api_id=API_ID, api_hash=API_HASH, session_string=session_str, no_updates=True)
        await new_client.start()
        me = await new_client.get_me()
        clients.append(new_client)
        STRINGS.append(session_str)
        save_strings_to_file(STRINGS)
        await msg.edit_text(f"✅ Added new session:\n• {me.first_name} (@{me.username or 'no_username'})")
    except Exception as e:
        await msg.edit_text(f"❌ Error adding session:\n`{e}`")


async def list_sessions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Unauthorized.")
    lines = []
    for i, c in enumerate(clients, start=1):
        try:
            me = await c.get_me()
            lines.append(f"{i}. {me.first_name} (@{me.username or 'no_username'}) — `{me.id}`")
        except Exception:
            lines.append(f"{i}. ❌ Failed to fetch info")
    total_persisted = len(STRINGS)
    header = f"🔎 Connected: {len(clients)} | Saved: {total_persisted}\n\n"
    await update.message.reply_markdown(header + "\n".join(lines) if lines else header + "No active sessions.")


# === Main Runner ===
async def main():
    print("🚀 Starting all clients...")
    await start_all_clients()
    print("✅ All clients started.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("group", group_cmd))
    app.add_handler(CommandHandler("user", user_cmd))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CommandHandler("leave", leave_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("add_session", add_session_cmd))
    app.add_handler(CommandHandler("list_sessions", list_sessions_cmd))

    print("🤖 Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
