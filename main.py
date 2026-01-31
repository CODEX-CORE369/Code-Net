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
PING_URL = "https://code-net-1.onrender.com"

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
┃ ┏─「 <b>ʙᴏᴛ sᴇʀᴠɪᴄᴇs</b> 」
┃ ┃ 🗑 <b>ᴀᴜᴛᴏ ᴄʟᴇᴀɴᴇʀ</b>
┃ ┃ 📌 <b>ᴀɴᴛɪ ᴘɪɴɴᴇᴅ</b>
┃ ┃ 🔊 <b>ᴠᴏɪᴄᴇ ʟᴏɢ ʀᴇᴍᴏᴠᴇʀ</b>
┃ ┃ 🚀 <b>ғᴀsᴛ ʙʀᴏᴀᴅᴄᴀsᴛ</b>
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

async def broadcast_logic(user_id, msg):
    try:
        if msg.reply_to_message:
            reply = msg.reply_to_message
            # Handle Custom Caption
            if len(msg.command) > 1:
                raw_cap = msg.text.split(" ", 1)[1]
                markup, clean_cap = parse_btn(raw_cap)
            else:
                clean_cap = reply.caption or ""
                markup = reply.reply_markup
            
            await reply.copy(chat_id=user_id, caption=clean_cap, reply_markup=markup)
        else:
            raw_txt = msg.text.split(" ", 1)[1]
            markup, clean_txt = parse_btn(raw_txt)
            await bot.send_message(chat_id=user_id, text=clean_txt, reply_markup=markup, disable_web_page_preview=True)
        return "OK"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_logic(user_id, msg)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
        await remove_user(user_id)
        return "BLOCK"
    except Exception:
        return "FAIL"

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_IDS))
async def broadcast_handler(client, message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("<b>⚠️ Format:</b> Reply or `/broadcast Text [Btn|Url]`")

    status = await message.reply_text("<b>🚀 ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛɪɴɢ...</b>")
    users = await get_all_ids(users_col)
    
    stats = {"OK": 0, "BLOCK": 0, "FAIL": 0}
    
    for i, user_id in enumerate(users):
        res = await broadcast_logic(user_id, message)
        stats[res] += 1
        
        # Update status every 20 users
        if (i + 1) % 20 == 0:
            try:
                await status.edit_text(f"<b>🚀 sᴇɴᴅɪɴɢ... {i+1}/{len(users)}</b>\n✅ {stats['OK']} | 🚫 {stats['BLOCK']} | ❌ {stats['FAIL']}")
            except: pass

    await status.edit_text(
        f"""
<b>✅ ʙʀᴏᴀᴅᴄᴀsᴛ ғɪɴɪsʜᴇᴅ</b>
━━━━━━━━━━━━━━━━━
📨 <b>sᴇɴᴛ:</b> {stats['OK']}
🚫 <b>ʀᴇᴍᴏᴠᴇᴅ:</b> {stats['BLOCK']}
❌ <b>ғᴀɪʟᴇᴅ:</b> {stats['FAIL']}
━━━━━━━━━━━━━━━━━
"""
    )

if __name__ == "__main__":
    print("Bot Starting...")
    bot.run()
