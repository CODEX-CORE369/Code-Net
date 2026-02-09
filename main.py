import os
import re
import asyncio
import time
import io
import threading
import requests
import logging
from flask import Flask
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from motor.motor_asyncio import AsyncIOMotorClient

# --- CONFIGURATION ---
API_ID = 20579940
API_HASH = "6fc0ea1c8dacae05751591adedc177d7"
BOT_TOKEN = "8270046107:AAHA3k62htFOPitlivuyDgx4aS7gjcqu0bo"

# Owner IDs
OWNER_IDS_STR = "6703335929, 5136260272"
OWNER_IDS = [int(x.strip()) for x in OWNER_IDS_STR.split(",") if x.strip().isdigit()]

# MongoDB
MONGO_URL = "mongodb+srv://dxsimu:mnbvcxzdx@dxsimu.0qrxmsr.mongodb.net/?appName=dxsimu"
DB_NAME = "DX-REMOVE"

# Keep Alive URL
PING_URL = "https://code-net-v6n8.onrender.com"

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FLASK SERVER (KEEP ALIVE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🔥 DX Bot Service is Online & High Performance! 🔥"

def run_flask():
    # Render assigns PORT env var, default to 8080 if not found
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    """Pings the Render URL every 5 minutes"""
    while True:
        time.sleep(300) # 5 Minutes
        try:
            logger.info(f"Pinging server: {PING_URL}")
            requests.get(PING_URL)
        except Exception as e:
            logger.error(f"Ping Failed: {e}")

# Start Background Threads
t1 = threading.Thread(target=run_flask)
t1.start()
t2 = threading.Thread(target=keep_alive)
t2.start()

# --- DATABASE LOGIC (OPTIMIZED) ---
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo[DB_NAME]
users_col = db["users"]
chats_col = db["chats"]

async def add_user(user_id):
    """Upsert user to DB (Faster & Safer)"""
    try:
        await users_col.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"DB Error (User): {e}")

async def add_chat(chat_id):
    """Upsert group to DB"""
    try:
        await chats_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"DB Error (Chat): {e}")

async def remove_user(user_id):
    await users_col.delete_one({"user_id": user_id})

async def get_all_ids(collection):
    return [doc["user_id"] if "user_id" in doc else doc["chat_id"] async for doc in collection.find()]

# --- FANCY FONT ENGINE ---
def to_fancy(text):
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    fancy  = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    table = str.maketrans(normal, fancy)
    return text.translate(table)

# --- BOT CLIENT ---
bot = Client(
    "DxServiceRemover",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- START HANDLER ---
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user = message.from_user
    await add_user(user.id)
    
    fname = user.first_name if user.first_name else "User"
    fancy_name = to_fancy(fname)
    
    # Notification Trigger (Hidden Mention)
    mention = f"<a href='tg://user?id={user.id}'>{fancy_name}</a>"
    
    # Advanced Dashboard Design
    text = f"""
┏━━「 <b>ᴅᴀsʜʙᴏᴀʀᴅ</b> 」━━┓
┃ ┏─「 <b>ᴜsᴇʀ ᴘʀᴏғɪʟᴇ</b> 」
┃ ┃ 👤 <b>ɴᴀᴍᴇ:</b> {mention}
┃ ┃ 🆔 <b>ɪᴅ:</b> <code>{user.id}</code>
┃ ┗───────────╼
┃ 
┃ ┏─「 <b>ʙᴏᴛ ғᴇᴀᴛᴜʀᴇs</b> 」
┃ ┃ 🗑 <b>ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ sᴇʀᴠɪᴄᴇ ᴍsɢ</b>
┃ ┃ 📌 <b>ʀᴇᴍᴏᴠᴇ ᴊᴏɪɴ/ʟᴇᴀᴠᴇ/ᴘɪɴ</b>
┃ ┃ 🔊 <b>ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ʟᴏɢ ᴄʟᴇᴀɴᴇʀ</b>
┃ ┃ 🚀 <b>ғᴀsᴛ ʙᴏᴛ</b>
┃ ┗───────────╼
┗━━━━━━━━━━┛
"""
    bot_user = await client.get_me()
    add_link = f"https://t.me/{bot_user.username}?startgroup=true&admin=delete_messages+invite_users"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕", url=add_link)]
    ])

    await message.reply_text(
        text=text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )

# --- SERVICE MESSAGE REMOVER ---
@bot.on_message(filters.service & filters.group)
async def delete_service(client, message):
    await add_chat(message.chat.id)
    try:
        await message.delete()
    except Exception:
        pass # Bot doesn't have delete permission

# --- STATS COMMAND ---
@bot.on_message(filters.command("users") & filters.user(OWNER_IDS))
async def stats_handler(client, message):
    status = await message.reply_text("<b>♻️ ᴘʀᴏᴄᴇssɪɴɢ ᴅᴀᴛᴀʙᴀsᴇ...</b>")
    
    users = await get_all_ids(users_col)
    chats = await get_all_ids(chats_col)
    
    # File Generation
    out_text = f"--- DX BOT DATABASE ---\n\nTOTAL USERS: {len(users)}\nTOTAL GROUPS: {len(chats)}\n\n--- USER LIST ---\n" + "\n".join(str(u) for u in users)
    
    bio = io.BytesIO(out_text.encode('utf-8'))
    bio.name = "DX_Database.txt"
    
    caption = f"""
<b>📊 sʏsᴛᴇᴍ sᴛᴀᴛɪsᴛɪᴄs</b>
━━━━━━━━━━━━━━━━━
👤 <b>ᴛᴏᴛᴀʟ ᴜsᴇʀs:</b> {len(users)}
👥 <b>ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs:</b> {len(chats)}
━━━━━━━━━━━━━━━━━
"""
    await message.reply_document(document=bio, caption=caption, parse_mode=enums.ParseMode.HTML)
    await status.delete()

# --- ADVANCED BROADCAST ---
def parse_btn(text):
    if not text: return None, ""
    pattern = r"\[([^\|\]]+)\|\s*([^\]]+)\]"
    matches = re.findall(pattern, text)
    clean_text = re.sub(pattern, "", text).strip()
    
    if not matches: return None, clean_text
    
    rows = []
    temp = []
    for txt, url in matches:
        temp.append(InlineKeyboardButton(txt.strip(), url=url.strip()))
        if len(temp) == 2:
            rows.append(temp)
            temp = []
    if temp: rows.append(temp)
    return InlineKeyboardMarkup(rows), clean_text

# --- IMPROVED BROADCAST SYSTEM (FIXED HTML & GROUP SUPPORT) ---

async def broadcast_logic(chat_id, msg):
    """Handles broadcasting to both Users and Groups with full HTML support"""
    try:
        # If it's a reply, use copy_message to preserve media and HTML entities
        if msg.reply_to_message:
            reply = msg.reply_to_message
            
            # Check if owner provided a custom caption with the command
            if len(msg.command) > 1:
                # Re-extracting the raw text to keep HTML tags intact
                full_text = msg.text.html if msg.text.html else msg.text
                raw_cap = full_text.split(None, 1)[1]
                markup, clean_cap = parse_btn(raw_cap)
            else:
                # Use original message's HTML caption/text
                clean_cap = reply.caption.html if reply.caption else (reply.text.html if reply.text else "")
                markup = reply.reply_markup
            
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=msg.chat.id,
                message_id=reply.id,
                caption=clean_cap,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            # Simple text broadcast from the command itself
            full_text = msg.text.html if msg.text.html else msg.text
            raw_txt = full_text.split(None, 1)[1]
            markup, clean_txt = parse_btn(raw_txt)
            
            await bot.send_message(
                chat_id=chat_id,
                text=clean_txt,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True
            )
        return "OK"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_logic(chat_id, msg)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
        await remove_user(chat_id)
        return "BLOCK"
    except Exception as e:
        logger.error(f"Broadcast Error for {chat_id}: {e}")
        return "FAIL"

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_IDS))
async def broadcast_handler(client, message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("<b>⚠️ Usage:</b> Reply to a message or use <code>/broadcast Text [Btn|Url]</code>")

    status = await message.reply_text("<b>🚀 ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛɪɴɢ...</b>")
    
    # Fetching both Users and Groups from DB
    users = await get_all_ids(users_col)
    chats = await get_all_ids(chats_col)
    all_targets = list(set(users + chats)) # Combining both and removing duplicates
    
    total = len(all_targets)
    stats = {"OK": 0, "BLOCK": 0, "FAIL": 0}
    
    for i, chat_id in enumerate(all_targets):
        res = await broadcast_logic(chat_id, message)
        stats[res] += 1
        
        # UI update every 15 targets
        if (i + 1) % 15 == 0 or (i + 1) == total:
            try:
                await status.edit_text(
                    f"<b>🚀 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ...</b>\n\n"
                    f"<b>📊 Progress:</b> <code>{i+1}/{total}</code>\n"
                    f"<b>✅ Success:</b> <code>{stats['OK']}</code>\n"
                    f"<b>🚫 Blocked:</b> <code>{stats['BLOCK']}</code>\n"
                    f"<b>❌ Failed:</b> <code>{stats['FAIL']}</code>"
                )
            except: pass

    await status.edit_text(
        f"""
<b>✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>
━━━━━━━━━━━━━━━━━
👤 <b>ᴛᴏᴛᴀʟ ᴛᴀʀɢᴇᴛs:</b> {total}
📨 <b>sᴇɴᴛ sᴜᴄᴄᴇss:</b> {stats['OK']}
🚫 <b>ʀᴇᴍᴏᴠᴇᴅ/ʙʟᴏᴄᴋᴇᴅ:</b> {stats['BLOCK']}
❌ <b>ғᴀɪʟᴇᴅ/ᴇʀʀᴏʀ:</b> {stats['FAIL']}
━━━━━━━━━━━━━━━━━
"""
    )

if __name__ == "__main__":
    print("Bot Starting...")
    bot.run()
