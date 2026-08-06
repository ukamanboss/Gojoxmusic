# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import asyncio
import random
import re
from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ParseMode, ChatMemberStatus
from pyrogram.errors import FloodWait

from ShrutiMusic import app

SPAM_CHATS = []
EMOJI = [
    "🦋🦋🦋🦋🦋", "🧚🌸🧋🍬🫖", "🥀🌷🌹🌺💐", "🌸🌿💮🌱🌵", "❤️💚💙💜🖤",
    "💓💕💞💗💖", "🌸💐🌺🌹🦋", "🍔🦪🍛🍲🥗", "🍎🍓🍒🍑🌶️", "🧋🥤🧋🥛🍷",
    "🍬🍭🧁🎂🍡", "🍨🧉🍺☕🍻", "🥪🥧🍦🍥🍚", "🫖☕🍹🍷🥛", "☕🧃🍩🍦🍙",
    "🍁🌾💮🍂🌿", "🌨️🌥️⛈️🌩️🌧️", "🌷🏵️🌸🌺💐", "💮🌼🌻🍀🍁", "🧟🦸🦹🧙👸",
    "🧅🍠🥕🌽🥦", "🐷🐹🐭🐨🐻‍❄️", "🦋🐇🐀🐈🐈‍⬛", "🌼🌳🌲🌴🌵", "🥩🍋🍐🍈🍇",
    "🍴🍽️🔪🍶🥃", "🕌🏰🏩⛩️🏩", "🎉🎊🎈🎂🎀", "🪴🌵🌴🌳🌲", "🎄🎋🎍🎑🎎",
    "🦅🦜🕊️🦤🦢", "🦤🦩🦚🦃🦆", "🐬🦭🦈🐋🐳", "🐔🐟🐠🐡🦐", "🦩🦀🦑🐙🦪",
    "🐦🦂🕷️🕸️🐚", "🥪🍰🥧🍨🍨", "🥬🍉🧁🧇🔮",
]


def clean_text(text):
    """Escape markdown special characters"""
    if not text:
        return ""
    return re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\1', text)


async def is_admin(chat_id: int, user_id: int) -> bool:
    """Optimized single API call to check admin status."""
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False


async def process_members(chat_id, member_generator, text=None, replied=None):
    """Stream processes members without storing them all in RAM."""
    tagged_members = 0
    usernum = 0
    usertxt = ""
    emoji_sequence = random.choice(EMOJI)
    emoji_index = 0
    
    async for member in member_generator:
        if chat_id not in SPAM_CHATS:
            break
        if member.user.is_deleted or member.user.is_bot:
            continue
            
        tagged_members += 1
        usernum += 1
        
        emoji = emoji_sequence[emoji_index % len(emoji_sequence)]
        usertxt += f"[{emoji}](tg://user?id={member.user.id}) "
        emoji_index += 1
        
        # Optimized to tag 7 users per batch for faster execution
        if usernum == 7:
            try:
                if replied:
                    await replied.reply_text(
                        usertxt,
                        disable_web_page_preview=True,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await app.send_message(
                        chat_id,
                        f"**{text}**\n\n{usertxt}" if text else usertxt,
                        disable_web_page_preview=True,
                        parse_mode=ParseMode.MARKDOWN
                    )
                await asyncio.sleep(1.5)  # Perfect balance to avoid FloodWait
                
                # Reset for next batch
                usernum = 0
                usertxt = ""
                emoji_sequence = random.choice(EMOJI)
                emoji_index = 0
                
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
            except Exception as e:
                print(f"Tag Error: {e}")
                continue
    
    # Process remaining users in the last incomplete batch
    if usernum > 0 and chat_id in SPAM_CHATS:
        try:
            if replied:
                await replied.reply_text(
                    usertxt,
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await app.send_message(
                    chat_id,
                    f"**{text}**\n\n{usertxt}" if text else usertxt,
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception:
            pass
            
    return tagged_members


@app.on_message(filters.command(["all", "allmention", "mentionall", "tagall"], prefixes=["/", "@"]))
async def tag_all_users(_, message):
    admin = await is_admin(message.chat.id, message.from_user.id)
    if not admin:
        return await message.reply_text("✦ **ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ!**")

    if message.chat.id in SPAM_CHATS:  
        return await message.reply_text("✦ **ᴛᴀɢɢɪɴɢ ɪs ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ! ᴜsᴇ /cancel ᴛᴏ sᴛᴏᴘ.**")  
    
    replied = message.reply_to_message  
    if len(message.command) < 2 and not replied:  
        return await message.reply_text("✦ **ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ ᴛᴀɢ, ᴇxᴀᴍᴘʟᴇ:** `@all Hi Friends`")  
    
    try:  
        SPAM_CHATS.append(message.chat.id)
        text = clean_text(message.text.split(None, 1)[1]) if not replied and len(message.command) > 1 else None
        
        # Direct generator passing - Zero Memory Load
        member_generator = app.get_chat_members(message.chat.id)
        
        tagged_members = await process_members(
            message.chat.id,
            member_generator,
            text=text,
            replied=replied
        )
        
        if message.chat.id in SPAM_CHATS:
            summary_msg = f"""
✅ **𝐓 𝐀 𝐆 𝐆 𝐈 𝐍 𝐆  𝐂 𝐎 𝐌 𝐏 𝐋 𝐄 𝐓 𝐄 𝐃**

✦ **𝐓𝐨𝐭𝐚𝐥 𝐓𝐚𝐠𝐠𝐞𝐝:** `{tagged_members}` 𝐌𝐞𝐦𝐛𝐞𝐫𝐬
"""
            await app.send_message(message.chat.id, summary_msg)

    except FloodWait as e:  
        await asyncio.sleep(e.value)  
    except Exception as e:  
        await app.send_message(message.chat.id, f"❌ **ᴇʀʀᴏʀ:** {str(e)}")  
    finally:  
        if message.chat.id in SPAM_CHATS:
            SPAM_CHATS.remove(message.chat.id)


@app.on_message(filters.command(["admintag", "adminmention", "admins", "report"], prefixes=["/", "@"]))
async def tag_all_admins(_, message):
    if not message.from_user:
        return

    admin = await is_admin(message.chat.id, message.from_user.id)  
    if not admin:  
        return await message.reply_text("✦ **ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ!**")  

    if message.chat.id in SPAM_CHATS:  
        return await message.reply_text("✦ **ᴛᴀɢɢɪɴɢ ɪs ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ! ᴜsᴇ /cancel ᴛᴏ sᴛᴏᴘ.**")  
    
    replied = message.reply_to_message  
    if len(message.command) < 2 and not replied:  
        return await message.reply_text("✦ **ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ ᴛᴀɢ, ᴇxᴀᴍᴘʟᴇ:** `@admins Hi Boss`")  
    
    try:  
        SPAM_CHATS.append(message.chat.id)
        text = clean_text(message.text.split(None, 1)[1]) if not replied and len(message.command) > 1 else None
        
        # Fetching only admins via generator
        admin_generator = app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS)
        
        tagged_admins = await process_members(
            message.chat.id,
            admin_generator,
            text=text,
            replied=replied
        )
        
        if message.chat.id in SPAM_CHATS:
            summary_msg = f"""
✅ **𝐀 𝐃 𝐌 𝐈 𝐍  𝐓 𝐀 𝐆  𝐂 𝐎 𝐌 𝐏 𝐋 𝐄 𝐓 𝐄 𝐃**

✦ **𝐓𝐨𝐭𝐚𝐥 𝐀𝐝𝐦𝐢𝐧𝐬 𝐓𝐚𝐠𝐠𝐞𝐝:** `{tagged_admins}`
"""
            await app.send_message(message.chat.id, summary_msg)

    except FloodWait as e:  
        await asyncio.sleep(e.value)  
    except Exception as e:  
        await app.send_message(message.chat.id, f"❌ **ᴇʀʀᴏʀ:** {str(e)}")  
    finally:  
        if message.chat.id in SPAM_CHATS:
            SPAM_CHATS.remove(message.chat.id)


@app.on_message(filters.command(["stopmention", "cancel", "cancelmention", "offmention", "mentionoff", "cancelall"], prefixes=["/", "@"]))
async def cancelcmd(_, message):
    chat_id = message.chat.id
    admin = await is_admin(chat_id, message.from_user.id)
    
    if not admin:
        return await message.reply_text("✦ **ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ!**")

    if chat_id in SPAM_CHATS:  
        SPAM_CHATS.remove(chat_id)  
        return await message.reply_text("🚫 **ᴛᴀɢɢɪɴɢ ᴘʀᴏᴄᴇss sᴜᴄᴄᴇssғᴜʟʟʏ sᴛᴏᴘᴘᴇᴅ!**")  
    else:  
        return await message.reply_text("✦ **ɴᴏ ᴛᴀɢɢɪɴɢ ᴘʀᴏᴄᴇss ɪs ᴄᴜʀʀᴇɴᴛʟʏ ʀᴜɴɴɪɴɢ.**")

MODULE = "Tᴀɢᴀʟʟ"
HELP = """
@all or /all | /tagall or @tagall | /mentionall or @mentionall [text] or [reply to any message] - Tag all users in your group with random emojis.

/admintag or @admintag | /adminmention or @adminmention | /admins or @admins [text] or [reply to any message] - Tag all admins in your group with random emojis.

/stopmention or @stopmention | /cancel or @cancel | /cancelall or @cancelall - Stop any running tagging process.

Note:
1. These commands can only be used by admins.
2. The bot must be an admin in your group.
3. Users will be tagged with unique emojis linking to their profiles.
"""

# ❤️ Love From ShrutiBots 
