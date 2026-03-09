import os
import re
import asyncio

# --- FIX FOR RENDER & PYTHON 3.10+ ---
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
# -------------------------------------

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

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FLASK SERVER (KEEP ALIVE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🔥 DX Bot Service is Online & High Performance! 🔥"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    B = "INFO" 
    port = int(os.environ.get('PORT', 8080))
    URL = os.environ.get('RENDER_EXTERNAL_URL', f"http://localhost:{port}")
    while True:
        try:
            requests.get(URL)
            print(f"[{B}] Pinging server ({URL}) to stay awake...")
        except Exception as e:
            print(f"[{B}] Ping failed: {e}")
        time.sleep(300)

# Start Background Threads
t1 = threading.Thread(target=run_flask, daemon=True)
t1.start()
t2 = threading.Thread(target=keep_alive, daemon=True)
t2.start()

# --- DATABASE LOGIC ---
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo[DB_NAME]
users_col = db["users"]
chats_col = db["chats"]

async def add_user(user_id, name="Unknown"):
    try:
        await users_col.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "name": name}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"DB Error (User): {e}")

async def add_chat(chat_id, name="Unknown Group"):
    try:
        await chats_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "name": name}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"DB Error (Chat): {e}")

async def remove_target(target_id):
    await users_col.delete_one({"user_id": target_id})
    await chats_col.delete_one({"chat_id": target_id})

async def get_all_ids(collection):
    ids = []
    async for doc in collection.find():
        if "user_id" in doc:
            ids.append(doc["user_id"])
        elif "chat_id" in doc:
            ids.append(doc["chat_id"])
    return ids

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
    bot_token=BOT_TOKEN,
    in_memory=True
)

# --- START HANDLER ---
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user = message.from_user
    fname = user.first_name if user.first_name else "User"
    fname_safe = fname.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
    await add_user(user.id, fname_safe)
    
    fancy_name = to_fancy(fname_safe)
    mention = f"<a href='tg://user?id={user.id}'>{fancy_name}</a>"
    
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
┃ ┃ 🚫 <b>ᴀɴᴛɪ ʟɪɴᴋ sʏsᴛᴇᴍ</b>
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

# --- SERVICE MESSAGE REMOVER & GROUP WELCOME LOGIC ---
@bot.on_message(
    (
        filters.service | 
        filters.pinned_message | 
        filters.new_chat_members | 
        filters.left_chat_member | 
        filters.chat_joined_by_request | 
        filters.video_chat_started | 
        filters.video_chat_ended | 
        filters.video_chat_members_invited | 
        filters.video_chat_scheduled | 
        filters.message_auto_delete_timer_changed |
        filters.forum_topic_created |
        filters.forum_topic_closed |
        filters.forum_topic_reopened |
        filters.forum_topic_edited |
        filters.general_forum_topic_hidden |
        filters.general_forum_topic_unhidden |
        filters.giveaway_created |
        filters.giveaway_winners_announced |
        filters.boost_added |
        filters.successful_payment |
        filters.refunded_payment |
        filters.proximity_alert_triggered |
        filters.write_access_allowed |
        filters.migrate_to_chat_id |
        filters.migrate_from_chat_id
    ) & filters.group
    )
async def delete_service(client, message):
    chat_title = message.chat.title if message.chat.title else "Unknown Group"
    chat_title_safe = chat_title.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
    
    await add_chat(message.chat.id, chat_title_safe)
    
    if message.new_chat_members:
        me = await client.get_me()
        for member in message.new_chat_members:
            if member.id == me.id:
                member_info = await client.get_chat_member(message.chat.id, me.id)
                if member_info.privileges and member_info.privileges.can_delete_messages:
                    welcome_text = f"""
<b>┏━━「 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ɢʀᴏᴜᴘ 」━━┓
┃
┃ 👋 ʜᴇʟʟᴏ! ɪ ᴀᴍ ʀᴇᴀᴅʏ ᴛᴏ ᴋᴇᴇᴘ
┃ <b>{chat_title_safe}</b> ᴄʟᴇᴀɴ.
┃ 
┃ 📌 <b>ᴍʏ ғᴇᴀᴛᴜʀᴇs:</b>
┃ ┣ 🗑 ᴅᴇʟᴇᴛᴇ ᴊᴏɪɴ/ʟᴇᴀᴠᴇ ᴍsɢ
┃ ┣ 📌 ᴅᴇʟᴇᴛᴇ ᴘɪɴ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs
┃ ┣ ⏳ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ ʟᴏɢs
┃ ┗ 🔊 ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ʟᴏɢs ᴄʟᴇᴀɴᴇʀ
┃
┃ ✅ <b>sᴛᴀᴛᴜs:</b> ᴀᴄᴛɪᴠᴇ & ᴀᴅᴍɪɴ
┗━━━━━━━━━━━━━━━━┛</b>
"""
                    await message.reply_text(welcome_text, parse_mode=enums.ParseMode.HTML)
                else:
                    warning_text = f"""
<b>┏━━「 ⚠️ ᴀᴛᴛᴇɴᴛɪᴏɴ ɴᴇᴇᴅᴇᴅ 」━━┓
┃
┃ ❌ ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴇɴᴏᴜɢʜ ᴘᴇʀᴍɪssɪᴏɴs
┃ in <b>{chat_title_safe}</b>!
┃ 
┃ ⚙️ <b>ʀᴇǫᴜɪʀᴇᴅ ᴘᴇʀᴍɪssɪᴏɴs:</b>
┃ ┣ 🗑 ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs
┃ ┗ 👥 ɪɴᴠɪᴛᴇ ᴜsᴇʀs
┃
┃ 👇 ᴘʟᴇᴀsᴇ ᴘʀᴏᴍᴏᴛᴇ ᴍᴇ ᴜsɪɴɢ 
┃ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.
┗━━━━━━━━━━━━━━━━┛</b>
"""
                    btn = InlineKeyboardMarkup([[InlineKeyboardButton("👑 ᴘʀᴏᴍᴏᴛᴇ ᴀs ᴀᴅᴍɪɴ 👑", url=f"https://t.me/{me.username}?startgroup=true&admin=delete_messages+invite_users")]])
                    warn_msg = await message.reply_text(warning_text, reply_markup=btn, parse_mode=enums.ParseMode.HTML)
                    await chats_col.update_one({"chat_id": message.chat.id}, {"$set": {"warning_msg_id": warn_msg.id}}, upsert=True)

    try:
        await message.delete()
    except Exception:
        pass 

# --- ANTI-LINK SYSTEM ---
@bot.on_message(filters.group & (filters.text | filters.caption) & ~filters.service)
async def anti_link(client, message):
    has_link = False
    
    if message.entities:
        for ent in message.entities:
            if ent.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]:
                has_link = True
                break
    if message.caption_entities and not has_link:
        for ent in message.caption_entities:
            if ent.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]:
                has_link = True
                break
                
    if has_link:
        user = message.from_user
        sender_chat = message.sender_chat
        
        # Ignore if sent by anonymous group admin or channel
        if sender_chat:
            return
        
        # Ignore bot owners
        if user and user.id in OWNER_IDS:
            return
            
        try:
            # Check user privileges
            member = await client.get_chat_member(message.chat.id, user.id)
            if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                await message.delete()
        except Exception:
            # If user not found or bot lacks permission, ignore silently
            pass

# --- CHAT MEMBER UPDATED (PROMOTION DETECTOR) ---
@bot.on_chat_member_updated(filters.group)
async def chat_member_update(client, chat_member_updated):
    me = await client.get_me()
    
    if chat_member_updated.new_chat_member and chat_member_updated.new_chat_member.user.id == me.id:
        new_status = chat_member_updated.new_chat_member.status
        old_status = chat_member_updated.old_chat_member.status if chat_member_updated.old_chat_member else None
        
        if new_status == enums.ChatMemberStatus.ADMINISTRATOR and old_status != enums.ChatMemberStatus.ADMINISTRATOR:
            chat_id = chat_member_updated.chat.id
            chat_title = chat_member_updated.chat.title if chat_member_updated.chat.title else "Unknown Group"
            chat_title_safe = chat_title.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
            
            chat_data = await chats_col.find_one({"chat_id": chat_id})
            if chat_data and "warning_msg_id" in chat_data:
                try:
                    await client.delete_messages(chat_id, chat_data["warning_msg_id"])
                    await chats_col.update_one({"chat_id": chat_id}, {"$unset": {"warning_msg_id": ""}})
                except:
                    pass
            
            welcome_text = f"""
<b>┏━━「 ᴘᴇʀᴍɪssɪᴏɴ ɢʀᴀɴᴛᴇᴅ 」━━┓
┃
┃ ✅ ᴛʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ᴘʀᴏᴍᴏᴛɪɴɢ ᴍᴇ!
┃ 
┃ 🗑 ɴᴏᴡ ɪ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇ:
┃ ┣ 📌 ᴘɪɴɴᴇᴅ/ɪᴏɪɴ/ʟᴇᴀᴠᴇ ᴍᴇssᴀɢᴇs
┃ ┣ ⏳ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ ʟᴏɢs
┃ ┗ 🔊 ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ʟᴏɢs
┃
┃ 🚀 ʀᴇᴀᴅʏ ᴛᴏ ᴋᴇᴇᴘ <b>{chat_title_safe}</b> ᴄʟᴇᴀɴ!
┗━━━━━━━━━━━━━━━━┛</b>
"""
            await client.send_message(chat_id, welcome_text, parse_mode=enums.ParseMode.HTML)

# --- STATS COMMAND ---
@bot.on_message(filters.command("users") & filters.user(OWNER_IDS))
async def stats_handler(client, message):
    status = await message.reply_text("<b>♻️ ᴘʀᴏᴄᴇssɪɴɢ ᴅᴀᴛᴀʙᴀsᴇ...</b>")
    
    users = []
    async for doc in users_col.find():
        users.append(f"{doc.get('user_id')} | {doc.get('name', 'Unknown')}")
        
    chats = []
    async for doc in chats_col.find():
        chats.append(f"{doc.get('chat_id')} | {doc.get('name', 'Unknown')}")
    
    out_text = f"--- DX BOT DATABASE ---\n\nTOTAL USERS: {len(users)}\nTOTAL GROUPS: {len(chats)}\n\n--- USER LIST ---\n"
    out_text += "\n".join(users)
    out_text += "\n\n--- GROUP LIST ---\n"
    out_text += "\n".join(chats)
    
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

# --- NEW ADVANCED IMPORT SYSTEM ---
@bot.on_message(filters.command("import") & filters.user(OWNER_IDS))
async def import_handler(client, message):
    doc = None
    if message.reply_to_message and message.reply_to_message.document:
        doc = message.reply_to_message.document
    elif message.document:
        doc = message.document
        
    if not doc or not doc.file_name.endswith('.txt'):
        return await message.reply_text("<b>⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ .txt ғɪʟᴇ ᴏʀ sᴇɴᴅ ᴡɪᴛʜ /import ᴄᴀᴘᴛɪᴏɴ.</b>")
    
    status = await message.reply_text("<b>📥 ɪᴍᴘᴏʀᴛɪɴɢ ᴅᴀᴛᴀ... ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.</b>")
    
    file_path = await client.download_media(doc, in_memory=True)
    content = file_path.getvalue().decode('utf-8')
    
    # Extracting all IDs
    raw_ids = re.findall(r"-?\d+", content)
    total = len(raw_ids)
    success = 0
    exists = 0
    failed = 0
    
    for cid_str in raw_ids:
        try:
            cid = int(cid_str)
            if cid < 0:
                check = await chats_col.find_one({"chat_id": cid})
                if check:
                    exists += 1
                else:
                    await add_chat(cid, "Imported Group")
                    success += 1
            else:
                check = await users_col.find_one({"user_id": cid})
                if check:
                    exists += 1
                else:
                    await add_user(cid, "Imported User")
                    success += 1
        except:
            failed += 1
            
    await status.edit_text(f"""
<b>✅ ɪᴍᴘᴏʀᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>
━━━━━━━━━━━━━━━━━
👤 <b>ᴛᴏᴛᴀʟ ɪᴅs ғᴏᴜɴᴅ:</b> {total}
✅ <b>sᴜᴄᴄᴇssғᴜʟʟʏ sᴀᴠᴇᴅ:</b> {success}
⚠️ <b>ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b> {exists}
❌ <b>ғᴀɪʟᴇᴅ/ɪɴᴠᴀʟɪᴅ:</b> {failed}
━━━━━━━━━━━━━━━━━
""")

# --- ADVANCED BROADCAST & BUTTON PARSER ---
def parse_btn(text):
    if not text: return None, ""
    lines = text.split('\n')
    clean_lines = []
    rows = []
    
    for line in lines:
        matches = re.findall(r"\[([^\|\]]+)\|\s*([^\]]+)\]", line)
        if matches:
            row = [InlineKeyboardButton(txt.strip(), url=url.strip()) for txt, url in matches]
            rows.append(row)
            # Remove buttons from text line
            clean_line = re.sub(r"\[([^\|\]]+)\|\s*([^\]]+)\]", "", line).strip()
            if clean_line:
                clean_lines.append(clean_line)
        else:
            clean_lines.append(line)
            
    clean_text = '\n'.join(clean_lines).strip()
    markup = InlineKeyboardMarkup(rows) if rows else None
    return markup, clean_text

async def broadcast_logic(chat_id, msg, do_pin, custom_text=None, custom_markup=None, override_caption=False):
    """Handles broadcasting with Pin and custom HTML format support"""
    try:
        sent_msg = None
        if msg.reply_to_message:
            kwargs = {
                "chat_id": chat_id,
                "from_chat_id": msg.chat.id,
                "message_id": msg.reply_to_message.id,
                "parse_mode": enums.ParseMode.HTML
            }
            if override_caption:
                kwargs["caption"] = custom_text
                kwargs["reply_markup"] = custom_markup
                
            sent_msg = await bot.copy_message(**kwargs)
        elif msg.media:
            # Handles sending /broadcast directly attached to an image, video, or doc
            kwargs = {
                "chat_id": chat_id,
                "from_chat_id": msg.chat.id,
                "message_id": msg.id,
                "parse_mode": enums.ParseMode.HTML
            }
            kwargs["caption"] = custom_text
            if custom_markup:
                kwargs["reply_markup"] = custom_markup
            sent_msg = await bot.copy_message(**kwargs)
        else:
            sent_msg = await bot.send_message(
                chat_id=chat_id,
                text=custom_text,
                reply_markup=custom_markup,
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True
            )
            
        if do_pin and sent_msg:
            try:
                await bot.pin_chat_message(chat_id, sent_msg.id)
            except:
                pass
        return "OK"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_logic(chat_id, msg, do_pin, custom_text, custom_markup, override_caption)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
        await remove_target(chat_id)
        return "BLOCK"
    except Exception as e:
        return "FAIL"

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_IDS))
async def broadcast_handler(client, message):
    if not message.reply_to_message and len(message.command) < 2 and not message.media:
        return await message.reply_text("<b>⚠️ Usage:</b> Reply to a message or use <code>/broadcast (pin) (group/user) Text [Btn|Url]</code> or send media with command in caption.")

    status = await message.reply_text("<b>🚀 ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛɪɴɢ...</b>")
    
    # Extracting text from either message or caption
    if message.text:
        raw_text = message.text.html
    elif message.caption:
        raw_text = message.caption.html
    else:
        raw_text = ""
    
    do_pin = "(pin)" in raw_text.lower()
    target_group = "(group)" in raw_text.lower()
    target_user = "(user)" in raw_text.lower()
    
    if target_group and target_user: target_type = "all"
    elif target_group: target_type = "group"
    elif target_user: target_type = "user"
    else: target_type = "all"

    # Cleaning flags from text to extract exactly the caption and buttons
    clean_raw_text = re.sub(r"(?i)\(pin\)", "", raw_text)
    clean_raw_text = re.sub(r"(?i)\(group\)", "", clean_raw_text)
    clean_raw_text = re.sub(r"(?i)\(user\)", "", clean_raw_text)
    clean_raw_text = re.sub(r"^/broadcast\s*", "", clean_raw_text).strip()
    
    custom_markup, custom_text = parse_btn(clean_raw_text)
    override_caption = bool(custom_text or custom_markup)

    users = await get_all_ids(users_col)
    chats = await get_all_ids(chats_col)
    
    if target_type == "group":
        all_targets = list(set(chats))
    elif target_type == "user":
        all_targets = list(set(users))
    else:
        all_targets = list(set(users + chats))
        
    total = len(all_targets)
    stats = {"OK": 0, "BLOCK": 0, "FAIL": 0}
    
    for i, chat_id in enumerate(all_targets):
        res = await broadcast_logic(chat_id, message, do_pin, custom_text, custom_markup, override_caption)
        stats[res] += 1
        
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

    await status.edit_text(f"""
<b>✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>
━━━━━━━━━━━━━━━━━
👤 <b>ᴛᴏᴛᴀʟ ᴛᴀʀɢᴇᴛs:</b> {total}
📨 <b>sᴇɴᴛ sᴜᴄᴄᴇss:</b> {stats['OK']}
🚫 <b>ʀᴇᴍᴏᴠᴇᴅ/ʙʟᴏᴄᴋᴇᴅ:</b> {stats['BLOCK']}
❌ <b>ғᴀɪʟᴇᴅ/ᴇʀʀᴏʀ:</b> {stats['FAIL']}
━━━━━━━━━━━━━━━━━
""")

if __name__ == "__main__":
    print("Bot Starting...")
    bot.run()
