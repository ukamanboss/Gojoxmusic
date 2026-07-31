# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com


import time

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from py_yt import VideosSearch

import config

from ShrutiMusic import app
from ShrutiMusic.misc import _boot_
from ShrutiMusic.plugins.sudo.sudoers import sudoers_list

from ShrutiMusic.utils import bot_sys_stats
from ShrutiMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from ShrutiMusic.utils.decorators.language import LanguageStart
from ShrutiMusic.utils.formatters import get_readable_time
from ShrutiMusic.utils.inline import (
    help_pannel_page1,
    private_panel,
    start_panel,
)

from config import BANNED_USERS
from strings import get_string


# ============================================================
# Constants
# ============================================================

START_EFFECT_ID = 5159385139981059251


# ============================================================
# Helper Functions
# ============================================================

async def _reply_start_photo(
    message: Message,
    caption: str,
    keyboard,
):
    """
    Sends the main start/help photo.

    Telegram message effects are attempted first.
    If the current Telegram/Pyrogram environment does not
    support the effect, it automatically falls back.
    """

    markup = InlineKeyboardMarkup(keyboard)

    try:
        return await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=caption,
            reply_markup=markup,
            message_effect_id=START_EFFECT_ID,
        )
    except Exception:
        return await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=caption,
            reply_markup=markup,
        )


async def _send_start_photo(
    chat_id,
    caption: str,
    keyboard,
):
    """
    Sends start photo directly through the bot.
    """

    markup = InlineKeyboardMarkup(keyboard)

    try:
        return await app.send_photo(
            chat_id=chat_id,
            photo=config.START_IMG_URL,
            caption=caption,
            reply_markup=markup,
            message_effect_id=START_EFFECT_ID,
        )
    except Exception:
        return await app.send_photo(
            chat_id=chat_id,
            photo=config.START_IMG_URL,
            caption=caption,
            reply_markup=markup,
        )


async def _send_start_log(message: Message, text: str):
    """
    Sends optional start logs without breaking the main
    command if the log group is unavailable.
    """

    try:
        if await is_on_off(2):
            await app.send_message(
                chat_id=config.LOG_GROUP_ID,
                text=text,
            )
    except Exception as ex:
        print(f"[START LOG ERROR] {ex}")


def _user_log(message: Message, action: str):
    """
    Creates a consistent user log message.
    """

    username = message.from_user.username

    if username:
        username_text = f"@{username}"
    else:
        username_text = "N/A"

    return (
        f"{message.from_user.mention} {action}\n\n"
        f"<b>ᴜsᴇʀ ɪᴅ :</b> "
        f"<code>{message.from_user.id}</code>\n"
        f"<b>ᴜsᴇʀɴᴀᴍᴇ :</b> {username_text}"
    )


async def _send_normal_start(message: Message, _):
    """
    Handles the normal private /start screen.
    """

    out = private_panel(_)

    try:
        UP, CPU, RAM, DISK = await bot_sys_stats()
    except Exception:
        UP, CPU, RAM, DISK = "N/A", "N/A", "N/A", "N/A"

    caption = _["start_2"].format(
        message.from_user.mention,
        app.mention,
        UP,
        DISK,
        CPU,
        RAM,
    )

    await _reply_start_photo(
        message=message,
        caption=caption,
        keyboard=out,
    )

    await _send_start_log(
        message,
        _user_log(
            message,
            "ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.",
        ),
    )


# ============================================================
# PRIVATE /START
# ============================================================

@app.on_message(
    filters.command(["start"])
    & filters.private
    & ~BANNED_USERS
)
@LanguageStart
async def start_pm(client, message: Message, _):

    # --------------------------------------------------------
    # Save user
    # --------------------------------------------------------

    try:
        await add_served_user(message.from_user.id)
    except Exception as ex:
        print(f"[SERVED USER ERROR] {ex}")

    # --------------------------------------------------------
    # Start argument
    # --------------------------------------------------------

    parts = message.text.split(maxsplit=1)

    if len(parts) <= 1:
        return await _send_normal_start(message, _)

    name = parts[1].strip()

    if not name:
        return await _send_normal_start(message, _)

    # ========================================================
    # HELP
    # ========================================================

    if name.startswith("help"):

        keyboard = help_pannel_page1(_)

        await _reply_start_photo(
            message=message,
            caption=_["help_1"].format(config.SUPPORT_GROUP),
            keyboard=keyboard,
        )

        return

    # ========================================================
    # SUDO LIST
    # ========================================================

    if name.startswith("sud"):

        await sudoers_list(
            client=client,
            message=message,
            _=_,
        )

        await _send_start_log(
            message,
            _user_log(
                message,
                "ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ "
                "<b>sᴜᴅᴏʟɪsᴛ</b>.",
            ),
        )

        return

    # ========================================================
    # YOUTUBE TRACK INFORMATION
    # ========================================================

    if name.startswith("inf"):

        loading = await message.reply_text("🔎")

        try:
            query = name.replace("info_", "", 1).strip()

            if not query:
                await loading.delete()
                return

            youtube_url = (
                f"https://www.youtube.com/watch?v={query}"
            )

            results = VideosSearch(
                youtube_url,
                limit=1,
            )

            data = await results.next()
            result_list = data.get("result", [])

            if not result_list:
                await loading.edit_text(
                    "❌ No information found."
                )
                return

            result = result_list[0]

            title = result.get("title", "Unknown")
            duration = result.get("duration", "Unknown")

            view_data = result.get("viewCount") or {}
            views = view_data.get("short", "Unknown")

            thumbnails = result.get("thumbnails") or []

            if thumbnails:
                thumbnail = thumbnails[0]["url"].split("?")[0]
            else:
                thumbnail = config.START_IMG_URL

            channel_data = result.get("channel") or {}

            channellink = channel_data.get(
                "link",
                "",
            )

            channel = channel_data.get(
                "name",
                "Unknown",
            )

            link = result.get(
                "link",
                youtube_url,
            )

            published = result.get(
                "publishedTime",
                "Unknown",
            )

            searched_text = _["start_6"].format(
                title,
                duration,
                views,
                published,
                channellink,
                channel,
                app.mention,
            )

            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=_["S_B_8"],
                            url=link,
                        ),
                        InlineKeyboardButton(
                            text=_["S_B_9"],
                            url=config.SUPPORT_GROUP,
                        ),
                    ]
                ]
            )

            try:
                await loading.delete()
            except Exception:
                pass

            try:
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail,
                    caption=searched_text,
                    reply_markup=key,
                    message_effect_id=START_EFFECT_ID,
                )
            except Exception:
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail,
                    caption=searched_text,
                    reply_markup=key,
                )

            await _send_start_log(
                message,
                _user_log(
                    message,
                    "ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ "
                    "<b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.",
                ),
            )

        except Exception as ex:

            print(f"[TRACK INFO ERROR] {ex}")

            try:
                await loading.edit_text(
                    "❌ Unable to fetch track information."
                )
            except Exception:
                pass

        return

    # ========================================================
    # EXPLICIT START
    # ========================================================

    if name == "start":
        return await _send_normal_start(message, _)

    # ========================================================
    # UNKNOWN START PARAMETER
    # ========================================================

    # Preserve the original behaviour:
    # unknown /start parameters simply open the main panel.

    return await _send_normal_start(message, _)


# ============================================================
# GROUP /START
# ============================================================

@app.on_message(
    filters.command(["start"])
    & filters.group
    & ~BANNED_USERS
)
@LanguageStart
async def start_gp(client, message: Message, _):

    out = start_panel(_)

    try:
        uptime = int(time.time() - _boot_)
    except Exception:
        uptime = 0

    caption = _["start_1"].format(
        app.mention,
        get_readable_time(uptime),
    )

    try:
        await _reply_start_photo(
            message=message,
            caption=caption,
            keyboard=out,
        )

    except Exception as ex:
        print(f"[GROUP START ERROR] {ex}")

    # Always register the served chat.
    try:
        await add_served_chat(message.chat.id)
    except Exception as ex:
        print(f"[SERVED CHAT ERROR] {ex}")


# ============================================================
# BOT ADDED / WELCOME
# ============================================================

@app.on_message(
    filters.new_chat_members,
    group=-1,
)
async def welcome(client, message: Message):

    for member in message.new_chat_members:

        try:

            # ------------------------------------------------
            # Language
            # ------------------------------------------------

            try:
                language = await get_lang(
                    message.chat.id
                )
            except Exception:
                language = "en"

            _ = get_string(language)

            # ------------------------------------------------
            # Banned user protection
            # ------------------------------------------------

            try:
                if await is_banned_user(member.id):

                    try:
                        await message.chat.ban_member(
                            member.id
                        )
                    except Exception:
                        pass

            except Exception as ex:
                print(
                    f"[BAN CHECK ERROR] {ex}"
                )

            # ------------------------------------------------
            # Only continue when this bot joined
            # ------------------------------------------------

            if member.id != app.id:
                continue

            # ------------------------------------------------
            # Bot must be in a SUPERGROUP
            # ------------------------------------------------

            if message.chat.type != ChatType.SUPERGROUP:

                try:
                    await message.reply_text(
                        _["start_4"]
                    )
                finally:
                    try:
                        await app.leave_chat(
                            message.chat.id
                        )
                    except Exception:
                        pass

                return

            # ------------------------------------------------
            # Blacklisted chat
            # ------------------------------------------------

            try:
                blacklisted = (
                    message.chat.id
                    in await blacklisted_chats()
                )
            except Exception:
                blacklisted = False

            if blacklisted:

                try:
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            (
                                f"https://t.me/"
                                f"{app.username}"
                                f"?start=sudolist"
                            ),
                            config.SUPPORT_GROUP,
                        ),
                        disable_web_page_preview=True,
                    )
                finally:
                    try:
                        await app.leave_chat(
                            message.chat.id
                        )
                    except Exception:
                        pass

                return

            # ------------------------------------------------
            # Normal welcome
            # ------------------------------------------------

            out = start_panel(_)

            caption = _["start_3"].format(
                message.from_user.first_name,
                app.mention,
                message.chat.title,
                app.mention,
            )

            try:
                await _send_start_photo(
                    chat_id=message.chat.id,
                    caption=caption,
                    keyboard=out,
                )

            except Exception as ex:
                print(
                    f"[WELCOME SEND ERROR] {ex}"
                )

            # ------------------------------------------------
            # Register served chat
            # ------------------------------------------------

            try:
                await add_served_chat(
                    message.chat.id
                )
            except Exception as ex:
                print(
                    f"[WELCOME CHAT ERROR] {ex}"
                )

            # ------------------------------------------------
            # Stop propagation
            # ------------------------------------------------

            try:
                await message.stop_propagation()
            except Exception:
                pass

        except Exception as ex:

            print(
                f"[WELCOME ERROR] {ex}"
            )
