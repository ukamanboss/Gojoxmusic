# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.

import os
import aiohttp
import aiofiles
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from ShrutiMusic import app

REPO_VIDEO = "https://files.catbox.moe/aoafwn.mp4"

@app.on_message(filters.command("vid"))
async def video_downloader(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ **Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠɪᴅᴇᴏ ᴜʀʟ.**\n\n**Exᴀᴍᴘʟᴇ:**\n`/vid Any_video_url`")

    video_url = message.text.split(None, 1)[1]
    msg = await message.reply("🔍 **Fᴇᴛᴄʜɪɴɢ ᴠɪᴅᴇᴏ ᴅᴇᴛᴀɪʟs...**")

    # Step 1: Call API Asynchronously
    payload = {
        "url": video_url,
        "token": "c99f113fab0762d216b4545e5c3d615eefb30f0975fe107caab629d17e51b52d"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14)",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://allvideodownloader.cc/wp-json/aio-dl/video-data/", data=payload, headers=headers) as r:
                data = await r.json()

            if "medias" not in data or not data["medias"]:
                return await msg.edit("❌ **Nᴏ ᴅᴏᴡɴʟᴏᴀᴅᴀʙʟᴇ ᴠɪᴅᴇᴏ ғᴏᴜɴᴅ.**")

            # Step 2: Get best quality video URL
            best_video = sorted(data["medias"], key=lambda x: x.get("quality", ""), reverse=True)[0]
            video_link = best_video["url"]

            await msg.edit("⬇️ **Dᴏᴡɴʟᴏᴀᴅɪɴɢ ᴠɪᴅᴇᴏ ɪɴ ʙᴀᴄᴋɢʀᴏᴜɴᴅ...**")

            # Step 3: Download the video asynchronously without blocking bot
            # Unique filename to prevent conflicts if multiple users download at once
            os.makedirs("downloads", exist_ok=True)
            file_name = f"downloads/video_{message.chat.id}_{message.id}.mp4"
            
            async with session.get(video_link) as v:
                async with aiofiles.open(file_name, "wb") as f:
                    async for chunk in v.content.iter_chunked(8192):
                        await f.write(chunk)

        # Step 4: Send video to user
        await msg.edit("📤 **Uᴘʟᴏᴀᴅɪɴɢ ᴛᴏ Tᴇʟᴇɢʀᴀᴍ...**")
        await app.send_video(
            chat_id=message.chat.id,
            video=file_name,
            caption=f"🎬 **{data.get('title', 'Video')}**\n\n✅ **Dᴏᴡɴʟᴏᴀᴅᴇᴅ ᴠɪᴀ {app.mention}**",
            supports_streaming=True
        )

        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ **Eʀʀᴏʀ:** `{str(e)}`")
        
    finally:
        # Safe cleanup of the unique file
        if 'file_name' in locals() and os.path.exists(file_name):
            try:
                os.remove(file_name)
            except Exception:
                pass


@app.on_message(filters.command(["repo", "source"]))
async def send_repo(_, message: Message):
    await message.reply_video(
        video=REPO_VIDEO,
        caption=(
            "✨ **Hᴇʏ ᴅᴇᴀʀ, ʜᴇʀᴇ ɪs ᴛʜᴇ ᴏғғɪᴄɪᴀʟ ʀᴇᴘᴏsɪᴛᴏʀʏ ᴏғ ᴛʜɪs ʙᴏᴛ** ✨\n\n"
            "🔗 **Dᴏɴ'ᴛ ғᴏʀɢᴇᴛ ᴛᴏ ɢɪᴠᴇ ᴀ sᴛᴀʀ** 🌟 **ᴀɴᴅ ғᴏʟʟᴏᴡ!**\n\n"
            "🧡 **Cʀᴇᴅɪᴛs:** [ShrutiBots](https://t.me/ShrutiBots)"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📂 Mᴀɴᴀɢᴇᴍᴇɴᴛ Bᴏᴛ", url="http://github.com/NoxxOP/ShrutiMusic"),
                    InlineKeyboardButton("📂 Mᴜsɪᴄ Bᴏᴛ", url="http://github.com/NoxxOP/ShrutixMusic")
                ]
            ]
        ),
        supports_streaming=True,
        has_spoiler=True,
    )

# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================

# ❤️ Love From ShrutiBots 
