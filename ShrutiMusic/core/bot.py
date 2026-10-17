# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import pyrogram
from pyrogram import Client
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import ChatWriteForbidden

import config
from ..logging import LOGGER


class Nand(Client):
    def __init__(self):
        LOGGER(__name__).info("Starting Bot Engine...")
        super().__init__(
            name="ShrutiMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=20, # Increased for 3x faster uploads/downloads
        )

    async def start(self):
        await super().start()
        get_me = await self.get_me()
        self.username = get_me.username
        self.id = get_me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.mention = self.me.mention

        button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="➕ Aᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕",
                        url=f"https://t.me/{self.username}?startgroup=true",
                    )
                ]
            ]
        )

        if config.LOG_GROUP_ID:
            # 1. Pre-Check Admin Privileges
            try:
                chat_member_info = await self.get_chat_member(config.LOG_GROUP_ID, self.id)
                if chat_member_info.status != ChatMemberStatus.ADMINISTRATOR:
                    LOGGER(__name__).warning("Bot is NOT an Admin in the Logger Group! Please promote it.")
            except Exception as e:
                LOGGER(__name__).error(f"Error checking bot status in log group: {e}")

            # 2. Premium VIP Startup Message
            startup_msg = f"""
✨ <b>𝐁 𝐎 𝐓  𝐒 𝐓 𝐀 𝐑 𝐓 𝐄 𝐃  𝐒 𝐔 𝐂 𝐂 𝐄 𝐒 𝐒 𝐅 𝐔 𝐋 𝐋 𝐘</b> ✨

✦ <b>𝐁𝐨𝐭 𝐍𝐚𝐦𝐞 :</b> {self.mention}
✦ <b>𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞 :</b> @{self.username}
✦ <b>𝐁𝐨𝐭 𝐈𝐃 :</b> <code>{self.id}</code>

🚀 <i>Sʏsᴛᴇᴍs ᴏɴʟɪɴᴇ ᴀɴᴅ ʀᴇᴀᴅʏ ᴛᴏ ᴘʟᴀʏ ᴍᴜsɪᴄ !</i>
"""
            # 3. Safe Sending Logic
            try:
                await self.send_photo(
                    config.LOG_GROUP_ID,
                    photo=config.START_IMG_URL,
                    caption=startup_msg,
                    reply_markup=button,
                )
            except ChatWriteForbidden:
                LOGGER(__name__).error("Bot cannot write to the log group. Check permissions.")
            except Exception as e:
                LOGGER(__name__).warning(f"Failed to send photo, falling back to text. Error: {e}")
                try:
                    await self.send_message(
                        config.LOG_GROUP_ID,
                        text=startup_msg,
                        reply_markup=button,
                        disable_web_page_preview=True
                    )
                except Exception as ex:
                    LOGGER(__name__).error(f"Failed to send text in log group: {ex}")
        else:
            LOGGER(__name__).warning("LOG_GROUP_ID is missing in config variables!")

        LOGGER(__name__).info(f"Music Bot Started successfully as {self.name} (@{self.username})")

    async def stop(self):
        LOGGER(__name__).info("Stopping Bot Engine...")
        try:
            await super().stop()
        except Exception:
            pass

# ❤️ Love From ShrutiBots
