import os
import re
import asyncio
import logging
import time
import io
import threading
import requests
from flask import Flask
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from motor.motor_asyncio import AsyncIOMotorClient

# --- CONFIGURATION ---
API_ID = 20579940
API_HASH = "6fc0ea1c8dacae05751591adedc177d7"
BOT_TOKEN = "8270046107:AAHA3k62htFOPitlivuyDgx4aS7gjcqu0bo"

# Owner IDs (String to List)
OWNER_IDS_STR = "6703335929, 5136260272"
OWNER_IDS = [int(x.strip()) for x in OWNER_IDS_STR.split(",") if x.strip().isdigit()]

# MongoDB Connection
MONGO_URL = "mongodb+srv://dxsimu:mnbvcxzdx@dxsimu.0qrxmsr.mongodb.net/?appName=dxsimu"
DB_NAME = "DX-REMOVE"

# --- FLASK SERVER & KEEP ALIVE (Render Support) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "DX Bot Service is Running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    """Pings the server every 5 minutes"""
    while True:
        time.sleep(300)
        try:
            requests.get("https://code-net-nkr9.onrender.com")
        except:
            pass

# Start Server in Background
t1 = threading.Thread(target=run_flask)
t1.start()
t2 = threading.Thread(target=keep_alive)
t2.start()

# --- DATABASE FUNCTIONS (Advanced) ---
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo[DB_NAME]
users_col = db["users"]
chats_col = db["chats"]

async def add_user(user_id):
    """Saves User ID if not exists"""
    found = await users_col.find_one({"user_id": user_id})
    if not found:
        await users_col.insert_one({"user_id": user_id})

async def add_chat(chat_id):
    """Saves Group/Chat ID if not exists"""
    found = await chats_col.find_one({"chat_id": chat_id})
    if not found:
        await chats_col.insert_one({"chat_id": chat_id})

async def remove_user(user_id):
    """Removes invalid users from DB"""
    await users_col.delete_one({"user_id": user_id})

async def get_all_users():
    return [user["user_id"] async for user in users_col.find()]

async def get_all_chats():
    return [chat["chat_id"] async for chat in chats_col.find()]

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

print("Bot started successfully...")

# --- WELCOME / START MESSAGE ---
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user = message.from_user
    # Save User to Database
    await add_user(user.id)
    
    # Fancy Name Generation
    fname = user.first_name if user.first_name else "User"
    fancy_name = to_fancy(fname)
    
    # Mention Logic (Hyperlink for Notification)
    # <a href="tg://user?id=123">Name</a> triggers a mention
    mention_link = f"<a href='tg://user?id={user.id}'>{fancy_name}</a>"
    
    # Dashboard Design
    text = f"""
┏━━「 ᴅᴀsʜʙᴏᴀʀᴅ 」━━┓
┃ ┏─「 ᴜsᴇʀ ᴘʀᴏғɪʟᴇ 」
┃ ┃ 👤 ɴᴀᴍᴇ: {mention_link}
┃ ┃ 🆔 ɪᴅ: <code>{user.id}</code>
┃ ┗───────────╼
┃ 
┃ ┏─「 ʙᴏᴛ ғᴇᴀᴛᴜʀᴇs 」
┃ ┃ ✅ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ sᴇʀᴠɪᴄᴇ ᴍsɢ
┃ ┃ ✅ ʀᴇᴍᴏᴠᴇ ᴊᴏɪɴ/ʟᴇᴀᴠᴇ/ᴘɪɴ
┃ ┃ ✅ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ʟᴏɢ ᴄʟᴇᴀɴᴇʀ
┃ ┃ ✅ ᴀᴅᴠᴀɴᴄᴇᴅ ʙʀᴏᴀᴅᴄᴀsᴛ
┃ ┗───────────╼
┗━━━━━━━━━━┛
"""
    # Button (Auto Permission Link)
    bot_username = (await client.get_me()).username
    add_link = f"https://t.me/{bot_username}?startgroup=true&admin=delete_messages+invite_users"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕", url=add_link)]
    ])

    await message.reply_text(
        text=text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )

# --- ADVANCED SERVICE MESSAGE REMOVER ---
@bot.on_message(filters.service & filters.group)
async def delete_service(client, message):
    chat_id = message.chat.id
    # Save Group ID to Database
    await add_chat(chat_id)
    
    try:
        # Delete the service message (Join, Left, Pin, VC Start/End)
        await message.delete()
    except Exception:
        # Pass silently if bot is not admin
        pass

# --- STATS / USERS COMMAND ---
@bot.on_message(filters.command("users") & filters.user(OWNER_IDS))
async def stats_handler(client, message):
    msg = await message.reply_text("<b>🔄 ᴄᴏʟʟᴇᴄᴛɪɴɢ ᴅᴀᴛᴀ...</b>")
    
    users = await get_all_users()
    chats = await get_all_chats()
    
    total_users = len(users)
    total_chats = len(chats)
    
    # Create text file with all IDs
    file_content = f"TOTAL USERS: {total_users}\nTOTAL GROUPS: {total_chats}\n\n--- USER IDs ---\n"
    file_content += "\n".join(str(u) for u in users)
    
    bio = io.BytesIO(file_content.encode('utf-8'))
    bio.name = "DX_Users_List.txt"
    
    text = f"""
<b>📊 ᴅᴀᴛᴀʙᴀsᴇ sᴛᴀᴛɪsᴛɪᴄs</b>
━━━━━━━━━━━━━━━━━
👤 <b>ᴛᴏᴛᴀʟ ᴜsᴇʀs:</b> {total_users}
👥 <b>ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs:</b> {total_chats}
━━━━━━━━━━━━━━━━━
"""
    await message.reply_document(
        document=bio,
        caption=text,
        parse_mode=enums.ParseMode.HTML
    )
    await msg.delete()

# --- BROADCAST SYSTEM (ADVANCED) ---
def parse_buttons(text):
    """Extracts [Button|Url] and returns Markup + Clean Text"""
    if not text: return None, ""
    
    pattern = r"\[([^\|\]]+)\|\s*([^\]]+)\]"
    matches = re.findall(pattern, text)
    clean_text = re.sub(pattern, "", text).strip()
    
    if not matches: return None, clean_text
    
    buttons = []
    row = []
    for btn_text, btn_url in matches:
        row.append(InlineKeyboardButton(btn_text.strip(), url=btn_url.strip()))
        if len(row) == 2: # 2 Buttons per row
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    
    return InlineKeyboardMarkup(buttons), clean_text

async def broadcast_msg(user_id, source_msg):
    try:
        # Handles Text, Photo, Video, Document, Animation
        if source_msg.reply_to_message:
            reply = source_msg.reply_to_message
            
            # Use new caption if provided in command, else original caption
            if len(source_msg.command) > 1:
                # User provided new caption/buttons
                raw_caption = source_msg.text.split(" ", 1)[1]
                markup, clean_caption = parse_buttons(raw_caption)
            else:
                # Use original caption
                clean_caption = reply.caption or ""
                markup = reply.reply_markup
            
            await reply.copy(
                chat_id=user_id,
                caption=clean_caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            # Simple Text Broadcast
            raw_text = source_msg.text.split(" ", 1)[1]
            markup, clean_text = parse_buttons(raw_text)
            
            await bot.send_message(
                chat_id=user_id,
                text=clean_text,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True
            )
        return True, None
        
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_msg(user_id, source_msg)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
        # User blocked bot or deleted account -> Remove from DB
        await remove_user(user_id)
        return False, "Deleted"
    except Exception as e:
        return False, str(e)

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_IDS))
async def broadcast_handler(client, message):
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply_text("<b>⚠️ Usage:</b> Reply to a message or `/broadcast Hello [Btn|Url]`")
        return

    status = await message.reply_text("<b>🚀 sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ...</b>")
    
    users = await get_all_users()
    done = 0
    blocked = 0
    failed = 0
    
    for user_id in users:
        success, error = await broadcast_msg(user_id, message)
        if success:
            done += 1
        elif error == "Deleted":
            blocked += 1
        else:
            failed += 1
            
    await status.edit_text(
        f"""
<b>✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>
━━━━━━━━━━━━━━━━━
📨 <b>sᴜᴄᴄᴇss:</b> {done}
🚫 <b>ʙʟᴏᴄᴋᴇᴅ/ʀᴇᴍᴏᴠᴇᴅ:</b> {blocked}
❌ <b>ғᴀɪʟᴇᴅ:</b> {failed}
━━━━━━━━━━━━━━━━━
"""
    )

if __name__ == "__main__":
    bot.run()
