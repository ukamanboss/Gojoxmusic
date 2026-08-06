import os
import asyncio
from unidecode import unidecode
from PIL import ImageDraw, Image, ImageFont, ImageChops, ImageFilter
from pyrogram import filters, enums
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from logging import getLogger
from ShrutiMusic import LOGGER, app
from ShrutiMusic.misc import SUDOERS
from ShrutiMusic.utils.database import db

try:
    wlcm = db.welcome
except Exception:
    from ShrutiMusic.utils.database import welcome as wlcm

LOGGER = getLogger(__name__)

class temp:
    ME = None
    CURRENT = 2
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None

def circle(pfp, size=(400, 400)):
    """Crops the image into a perfect circle with smooth anti-aliased edges."""
    pfp = pfp.resize(size, Image.LANCZOS).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.LANCZOS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

def generate_premium_welcome(pic_path, user_name, chat_title, user_id, uname):
    """Generates a dynamic HD blurred background welcome image."""
    try:
        pfp = Image.open(pic_path).convert("RGBA")
    except Exception:
        pfp = Image.open("ShrutiMusic/assets/upic.png").convert("RGBA")

    # 1. Create Dynamic Blurred Background
    CANVAS_W, CANVAS_H = 1280, 720
    bg = pfp.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(55)) 
    
    # Apply aesthetic dark overlay
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (10, 10, 15, 170))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)

    # 2. Process Avatar with Glow & Ring
    avatar = circle(pfp, size=(380, 380))
    avatar_x, avatar_y = 120, 170

    # Background Glow
    glow_size = 460
    glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([0, 0, glow_size, glow_size], fill=(255, 255, 255, 50))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    bg.paste(glow, (avatar_x - 40, avatar_y - 40), glow)
    
    # Clean White Ring
    draw.ellipse([avatar_x - 8, avatar_y - 8, avatar_x + 388, avatar_y + 388], outline=(255, 255, 255, 220), width=6)
    bg.paste(avatar, (avatar_x, avatar_y), avatar)

    # 3. Typography Setup
    try:
        font_title = ImageFont.truetype('ShrutiMusic/assets/font.ttf', size=65)
        font_name = ImageFont.truetype('ShrutiMusic/assets/font.ttf', size=85)
        font_sub = ImageFont.truetype('ShrutiMusic/assets/font.ttf', size=40)
    except Exception:
        font_title = ImageFont.load_default()
        font_name = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    text_x = 580
    clean_name = unidecode(user_name)[:15] + ".." if len(unidecode(user_name)) > 15 else unidecode(user_name)
    clean_chat = chat_title[:20] + ".." if len(chat_title) > 20 else chat_title

    # 4. Draw Texts with Drop Shadows for depth
    draw.text((text_x + 3, 203), "W E L C O M E", fill=(0, 0, 0, 150), font=font_title)
    draw.text((text_x, 200), "W E L C O M E", fill=(255, 255, 255, 220), font=font_title)
    
    draw.text((text_x + 3, 293), f"{clean_name}", fill=(0, 0, 0, 180), font=font_name)
    draw.text((text_x, 290), f"{clean_name}", fill=(255, 255, 255, 255), font=font_name)
    
    # Sub Information (ID, Username, Group)
    draw.text((text_x, 430), f"🆔 ID : {user_id}", fill=(200, 200, 200, 255), font=font_sub)
    if uname:
        draw.text((text_x, 490), f"👤 USERNAME : @{uname}", fill=(200, 200, 200, 255), font=font_sub)
    draw.text((text_x, 550), f"💬 GROUP : {clean_chat}", fill=(200, 200, 200, 255), font=font_sub)

    out_path = f"downloads/welcome_{user_id}.png"
    bg.save(out_path, quality=95, optimize=True)
    return out_path


@app.on_message(filters.command("welcome") & ~filters.private)
async def auto_state(_, message):
    usage = "<b>❖ ᴜsᴀɢᴇ ➥</b> /welcome [on|off]"
    if len(message.command) == 1:
        return await message.reply_text(usage)

    chat_id = message.chat.id
    user = await app.get_chat_member(message.chat.id, message.from_user.id)

    if user.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        A = await wlcm.find_one({"chat_id": chat_id})
        state = message.text.split(None, 1)[1].strip().lower()

        if state == "on":
            if A and not A.get("disabled", False):
                return await message.reply_text("✦ Special Welcome Already Enabled")
            await wlcm.update_one({"chat_id": chat_id}, {"$set": {"disabled": False}}, upsert=True)
            await message.reply_text(f"✦ Enabled Special Welcome in {message.chat.title}")

        elif state == "off":
            if A and A.get("disabled", False):
                return await message.reply_text("✦ Special Welcome Already Disabled")
            await wlcm.update_one({"chat_id": chat_id}, {"$set": {"disabled": True}}, upsert=True)
            await message.reply_text(f"✦ Disabled Special Welcome in {message.chat.title}")

        else:
            await message.reply_text(usage)
    else:
        await message.reply("✦ Only Admins Can Use This Command")


@app.on_chat_member_updated(filters.group, group=-3)
async def greet_group(_, member: ChatMemberUpdated):
    chat_id = member.chat.id
    A = await wlcm.find_one({"chat_id": chat_id})

    if A and A.get("disabled", False):  
        return

    if (
        not member.new_chat_member
        or member.new_chat_member.status in {"banned", "left", "restricted"}
        or member.old_chat_member
    ):
        return

    user = member.new_chat_member.user if member.new_chat_member else member.from_user
    pic_path = f"downloads/pp{user.id}.png"
    
    try:
        if user.photo:
            await app.download_media(user.photo.big_file_id, file_name=pic_path)
        else:
            pic_path = "ShrutiMusic/assets/upic.png"
    except Exception:
        pic_path = "ShrutiMusic/assets/upic.png"

    if temp.MELCOW.get(f"welcome-{member.chat.id}") is not None:
        try:
            await temp.MELCOW[f"welcome-{member.chat.id}"].delete()
        except Exception as e:
            LOGGER.error(f"Failed to delete old welcome: {e}")

    try:
        # Running heavy image generation in background thread to prevent bot freeze
        welcomeimg = await asyncio.to_thread(
            generate_premium_welcome,
            pic_path, user.first_name, member.chat.title, user.id, user.username
        )
        
        temp.MELCOW[f"welcome-{member.chat.id}"] = await app.send_photo(
            member.chat.id,
            photo=welcomeimg,
            caption=f"""🌟 <b>ᴡᴇʟᴄᴏᴍᴇ {user.mention}!</b>\n\n📋 <b>ɢʀᴏᴜᴘ:</b> {member.chat.title}\n🆔 <b>ʏᴏᴜʀ ɪᴅ:</b> <code>{user.id}</code>\n👤 <b>ᴜsᴇʀɴᴀᴍᴇ:</b> @{user.username if user.username else "ɴᴏᴛ sᴇᴛ"}\n\n<b><u>ʜᴏᴘᴇ ʏᴏᴜ ғɪɴᴅ ɢᴏᴏᴅ ᴠɪʙᴇs, ɴᴇᴡ ғʀɪᴇɴᴅs, ᴀɴᴅ ʟᴏᴛs ᴏғ ғᴜɴ ʜᴇʀᴇ!</u> 🌟</b>""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ 🎵", url=f"https://t.me/{app.username}?startgroup=True")]
            ]),
        )

    except Exception as e:
        LOGGER.error(f"Welcome Generation Error: {e}")

    finally:
        # Safe Cleanup
        try:
            if os.path.exists(f"downloads/welcome_{user.id}.png"):
                os.remove(f"downloads/welcome_{user.id}.png")
            if os.path.exists(f"downloads/pp{user.id}.png"):
                os.remove(f"downloads/pp{user.id}.png")
        except Exception:
            pass
