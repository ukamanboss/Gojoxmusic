# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import os
import random
import aiohttp
import aiofiles
import traceback
from datetime import datetime, timedelta
import pytz
from PIL import Image, ImageDraw, ImageFilter

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatType

from ShrutiMusic.utils import get_image, get_couple, save_couple
from ShrutiMusic import app

# Dimensions for HD Canvas
CANVAS_W, CANVAS_H = 1280, 720
DEFAULT_PFP = "https://telegra.ph/file/05aa686cf52fc666184bf.jpg"

# ==========================================
# ASYNC UTILITIES (For Zero-Lag Performance)
# ==========================================
async def download_image_async(url: str, path: str):
    """Downloads images asynchronously without blocking the bot."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(path, "wb") as f:
                        await f.write(await resp.read())
        return path
    except Exception:
        return None


async def upload_to_graph_async(path: str):
    """Uploads image to Graph.org asynchronously."""
    try:
        async with aiohttp.ClientSession() as session:
            with open(path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f, filename=os.path.basename(path))
                async with session.post("https://graph.org/upload", data=form) as resp:
                    res = await resp.json()
                    return "https://graph.org" + res[0]['src']
    except Exception as e:
        print(f"Graph Upload Error: {e}")
        return None


# ==========================================
# DATE UTILITIES
# ==========================================
def get_today_date():
    timezone = pytz.timezone("Asia/Kolkata")
    now = datetime.now(timezone)
    return now.strftime("%d/%m/%Y")


def get_todmorrow_date():
    timezone = pytz.timezone("Asia/Kolkata")
    tomorrow = datetime.now(timezone) + timedelta(days=1)
    return tomorrow.strftime("%d/%m/%Y")


# ==========================================
# COUPLE COMMAND
# ==========================================
@app.on_message(filters.command(["couple", "couples"]))
async def ctest(_, message):
    cid = message.chat.id
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("Tʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋs ɪɴ ɢʀᴏᴜᴘs.")

    today = get_today_date()
    tomorrow = get_todmorrow_date()

    p1_path = f"downloads/pfp1_{cid}.png"
    p2_path = f"downloads/pfp2_{cid}.png"
    out_path = f"downloads/couple_{cid}.png"

    try:
        is_selected = await get_couple(cid, today)
        if not is_selected:
            msg = await message.reply_text("💖 **Fɪɴᴅɪɴɢ ᴛʜᴇ ᴘᴇʀғᴇᴄᴛ ᴍᴀᴛᴄʜ...**")
            list_of_users = []

            async for i in app.get_chat_members(message.chat.id, limit=50):
                if not i.user.is_bot and not i.user.is_deleted:
                    list_of_users.append(i.user.id)
            
            if len(list_of_users) < 2:
                return await msg.edit_text("Nᴏᴛ ᴇɴᴏᴜɢʜ ᴜsᴇʀs ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ!")

            c1_id = random.choice(list_of_users)
            c2_id = random.choice(list_of_users)
            while c1_id == c2_id:
                c1_id = random.choice(list_of_users)

            user1 = await app.get_users(c1_id)
            user2 = await app.get_users(c2_id)

            N1 = user1.mention
            N2 = user2.mention

            # Download P1
            if user1.photo:
                await app.download_media(user1.photo.big_file_id, file_name=p1_path)
            else:
                await download_image_async(DEFAULT_PFP, p1_path)

            # Download P2
            if user2.photo:
                await app.download_media(user2.photo.big_file_id, file_name=p2_path)
            else:
                await download_image_async(DEFAULT_PFP, p2_path)

            # --- DYNAMIC PREMIUM IMAGE GENERATION ---
            img1 = Image.open(p1_path).convert("RGBA")
            img2 = Image.open(p2_path).convert("RGBA")

            # 1. Create Glassmorphism Background
            bg1 = img1.copy().resize((CANVAS_W // 2, CANVAS_H), Image.LANCZOS)
            bg2 = img2.copy().resize((CANVAS_W // 2, CANVAS_H), Image.LANCZOS)
            canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H))
            canvas.paste(bg1, (0, 0))
            canvas.paste(bg2, (CANVAS_W // 2, 0))
            
            # Apply heavy blur and dark overlay
            canvas = canvas.filter(ImageFilter.GaussianBlur(60))
            overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 150))
            canvas = Image.alpha_composite(canvas, overlay)
            draw = ImageDraw.Draw(canvas)

            # 2. Process Circular Avatars
            AVATAR_SIZE = 360
            img1 = img1.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
            img2 = img2.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)

            mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
            img1.putalpha(mask)
            img2.putalpha(mask)

            # Coordinates
            y_pos = (CANVAS_H - AVATAR_SIZE) // 2
            x1_pos = 180
            x2_pos = CANVAS_W - AVATAR_SIZE - 180

            # 3. Connection Line & Glow
            draw.line([(x1_pos + AVATAR_SIZE, CANVAS_H//2), (x2_pos, CANVAS_H//2)], fill=(255, 255, 255, 120), width=6)
            
            # Center Heart/Plus text illusion using shapes
            center_x = CANVAS_W // 2
            draw.ellipse([center_x - 30, (CANVAS_H//2) - 30, center_x + 30, (CANVAS_H//2) + 30], fill=(255, 75, 100, 255))
            draw.line([(center_x - 10, CANVAS_H//2), (center_x + 10, CANVAS_H//2)], fill="white", width=4)
            draw.line([(center_x, (CANVAS_H//2) - 10), (center_x, (CANVAS_H//2) + 10)], fill="white", width=4)

            # 4. Avatar Drop Shadows
            shadow = Image.new("RGBA", (AVATAR_SIZE + 40, AVATAR_SIZE + 40), (0, 0, 0, 0))
            s_draw = ImageDraw.Draw(shadow)
            s_draw.ellipse([0, 0, AVATAR_SIZE + 40, AVATAR_SIZE + 40], fill=(0, 0, 0, 180))
            shadow = shadow.filter(ImageFilter.GaussianBlur(25))
            
            canvas.paste(shadow, (x1_pos - 20, y_pos - 15), shadow)
            canvas.paste(shadow, (x2_pos - 20, y_pos - 15), shadow)

            # 5. Avatar Rings
            draw.ellipse([x1_pos-8, y_pos-8, x1_pos+AVATAR_SIZE+8, y_pos+AVATAR_SIZE+8], outline=(255, 255, 255, 220), width=8)
            draw.ellipse([x2_pos-8, y_pos-8, x2_pos+AVATAR_SIZE+8, y_pos+AVATAR_SIZE+8], outline=(255, 255, 255, 220), width=8)

            # Paste Avatars
            canvas.paste(img1, (x1_pos, y_pos), img1)
            canvas.paste(img2, (x2_pos, y_pos), img2)

            canvas.save(out_path, quality=95, optimize=True)
            # ----------------------------------------

            TXT = f"""
<b>Tᴏᴅᴀʏ's ᴄᴏᴜᴘʟᴇ ᴏғ ᴛʜᴇ ᴅᴀʏ 🎉:

{N1} + {N2} = 💚

Nᴇxᴛ ᴄᴏᴜᴘʟᴇs ᴡɪʟʟ ʙᴇ sᴇʟᴇᴄᴛᴇᴅ ᴏɴ {tomorrow}!!</b>
"""
            await message.reply_photo(
                out_path,
                caption=TXT,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="Aᴅᴅ ᴍᴇ 🌋", url=f"https://t.me/{app.username}?startgroup=true")]]
                ),
            )

            await msg.delete()
            
            # Async Upload
            img_url = await upload_to_graph_async(out_path)
            if img_url:
                couple = {"c1_id": c1_id, "c2_id": c2_id}
                await save_couple(cid, today, couple, img_url)

        else:
            msg = await message.reply_text("💖 **Fᴇᴛᴄʜɪɴɢ ᴛᴏᴅᴀʏ's ᴄᴏᴜᴘʟᴇ...**")
            b = await get_image(cid)
            c1_id = int(is_selected["c1_id"])
            c2_id = int(is_selected["c2_id"])
            c1_name = (await app.get_users(c1_id)).first_name
            c2_name = (await app.get_users(c2_id)).first_name

            TXT = f"""
<b>Tᴏᴅᴀʏ's ᴄᴏᴜᴘʟᴇ ᴏғ ᴛʜᴇ ᴅᴀʏ 🎉:

[{c1_name}](tg://openmessage?user_id={c1_id}) + [{c2_name}](tg://openmessage?user_id={c2_id}) = ❣️

Nᴇxᴛ ᴄᴏᴜᴘʟᴇs ᴡɪʟʟ ʙᴇ sᴇʟᴇᴄᴛᴇᴅ ᴏɴ {tomorrow}!!</b>
"""
            await message.reply_photo(
                b,
                caption=TXT,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="Aᴅᴅ ᴍᴇ🌋", url=f"https://t.me/{app.username}?startgroup=true")]]
                ),
            )
            await msg.delete()

    except Exception as e:
        print(f"Couple Error: {str(e)}")
        traceback.print_exc()
    finally:
        # Safe Cleanup
        for file in [p1_path, p2_path, out_path]:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except Exception:
                    pass

# ❤️ Love From ShrutiBots
