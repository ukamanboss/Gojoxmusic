# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import asyncio
import time
from logging import getLogger
from pyrogram import enums, filters
from pyrogram.types import ChatMemberUpdated

from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb
from ShrutiMusic.utils.database import get_assistant
from config import OWNER_ID

LOGGER = getLogger(__name__)

# MongoDB collection for awelcome
awelcome_collection = mongodb.awelcome


class AWelDatabase:
    """MongoDB-backed welcome state per group - FIXED LOGIC"""

    @staticmethod
    async def is_enabled(chat_id: int) -> bool:
        """Returns True if welcome is ON for this chat, False otherwise (Default is OFF)"""
        doc = await awelcome_collection.find_one({"chat_id": chat_id})
        if not doc:
            return False
        return doc.get("enabled", False)

    @staticmethod
    async def enable(chat_id: int):
        """Turn ON assistant welcome"""
        await awelcome_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": True}},
            upsert=True,
        )

    @staticmethod
    async def disable(chat_id: int):
        """Turn OFF assistant welcome"""
        await awelcome_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": False}},
            upsert=True,
        )


wlcm = AWelDatabase()

# Spam prevention dictionary
user_last_message_time = {}
user_command_count = {}
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5


@app.on_message(filters.command("awelcome") & ~filters.private)
async def auto_state(_, message):
    user_id = message.from_user.id
    current_time = time.time()
    last_message_time = user_last_message_time.get(user_id, 0)

    # Anti-Spam Logic
    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(
                f"⚠️ **{message.from_user.mention}, ᴘʟᴇᴀsᴇ ᴅᴏɴ'ᴛ sᴘᴀᴍ!**\nᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴀ ғᴇᴡ sᴇᴄᴏɴᴅs."
            )
            await asyncio.sleep(3)
            try:
                await hu.delete()
            except Exception:
                pass
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time

    usage = "<b>❖ ᴜsᴀɢᴇ ➥</b> /awelcome [on|off]"
    if len(message.command) == 1:
        return await message.reply_text(usage)

    chat_id = message.chat.id
    
    try:
        user = await app.get_chat_member(message.chat.id, message.from_user.id)
    except Exception:
        return await message.reply_text("❌ ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ᴀᴅᴍɪɴ sᴛᴀᴛᴜs.")

    # Admin Check
    if user.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        state = message.text.split(None, 1)[1].strip().lower()
        is_on = await wlcm.is_enabled(chat_id)

        if state == "on":
            if is_on:
                await message.reply_text("✦ **ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɪs ᴀʟʀᴇᴀᴅʏ ᴇɴᴀʙʟᴇᴅ!**")
            else:
                await wlcm.enable(chat_id)
                await message.reply_text(f"✦ **ᴇɴᴀʙʟᴇᴅ ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɪɴ {message.chat.title}** ✨")
                
        elif state == "off":
            if not is_on:
                await message.reply_text("✦ **ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɪs ᴀʟʀᴇᴀᴅʏ ᴅɪsᴀʙʟᴇᴅ!**")
            else:
                await wlcm.disable(chat_id)
                await message.reply_text(f"✦ **ᴅɪsᴀʙʟᴇᴅ ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɪɴ {message.chat.title}** ❌")
                
        else:
            await message.reply_text(usage)
    else:
        await message.reply("✦ **ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ!**")


@app.on_chat_member_updated(filters.group, group=5)
async def greet_new_members(_, member: ChatMemberUpdated):
    try:
        chat_id = member.chat.id
        is_on = await wlcm.is_enabled(chat_id)

        # Drop execution if feature is OFF
        if not is_on:
            return  

        # Check if it's a new member joining (not an old member updating status or leaving)
        if member.new_chat_member and not member.old_chat_member:
            chat_name = (await app.get_chat(chat_id)).title
            userbot = await get_assistant(chat_id)
            count = await app.get_chat_members_count(chat_id)
            user = member.new_chat_member.user if member.new_chat_member else member.from_user
            username_display = f"@{user.username}" if user.username else "ɴᴏɴᴇ"

            # VIP Welcome for Owner
            if user.id == OWNER_ID or user.id == 7574330905:
                owner_welcome_text = f"""
🌟 <b>𝐓 𝐇 𝐄  𝐎 𝐖 𝐍 𝐄 𝐑  𝐇 𝐀 𝐒  𝐀 𝐑 𝐑 𝐈 𝐕 𝐄 𝐃</b> 🌟

🔥 <b>𝐁𝐎𝐒𝐒:</b> {user.mention} <b>ʜᴀs ᴊᴏɪɴᴇᴅ ᴛʜᴇ ᴄʜᴀᴛ!</b>
👑 <b>𝐎𝐖𝐍𝐄𝐑 𝐈𝐃:</b> <code>{user.id}</code>
🎯 <b>𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄:</b> {username_display}
👥 <b>𝐓𝐎𝐓𝐀𝐋 𝐌𝐄𝐌𝐁𝐄𝐑𝐒:</b> {count}
🏰 <b>𝐊𝐈𝐍𝐆𝐃𝐎𝐌:</b> {chat_name}

<b>ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏ ʏᴏᴜʀ ᴇᴍᴘɪʀᴇ, ʙᴏss! 👑✨</b>
"""
                await asyncio.sleep(2)
                await userbot.send_message(chat_id, text=owner_welcome_text)
            
            # Standard Premium Welcome for regular users
            else:
                welcome_text = f"""
✨ <b>𝐖 𝐄 𝐋 𝐂 𝐎 𝐌 𝐄  𝐓 𝐎  𝐎 𝐔 𝐑  𝐆 𝐑 𝐎 𝐔 𝐏</b> ✨

✦ <b>𝐍𝐀𝐌𝐄 ◂⚚▸</b> {user.mention}
✦ <b>𝐔𝐒𝐄𝐑 𝐈𝐃 ◂⚚▸</b> <code>{user.id}</code>
✦ <b>𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄 ◂⚚▸</b> {username_display}
✦ <b>𝐌𝐄𝐌𝐁𝐄𝐑 𝐂𝐎𝐔𝐍𝐓 ◂⚚▸</b> #{count}

<b>ʜᴏᴘᴇ ʏᴏᴜ ʜᴀᴠᴇ ᴀ ɢʀᴇᴀᴛ ᴛɪᴍᴇ ʜᴇʀᴇ ᴀᴛ {chat_name}! 🥂</b>
"""
                await asyncio.sleep(2)
                await userbot.send_message(chat_id, text=welcome_text)

    except Exception as e:
        LOGGER.error(f"AWelcome Error: {e}")
        return
