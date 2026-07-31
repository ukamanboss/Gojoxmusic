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

import math

from pyrogram.types import InlineKeyboardButton

from ShrutiMusic.utils.formatters import time_to_seconds
from config import BOT_USERNAME, SUPPORT_GROUP, SUPPORT_CHANNEL


# ============================================================
# Internal helpers
# ============================================================

def _button(text, callback_data=None, url=None, user_id=None):
    """
    Lightweight button factory.
    Keeps all button creation consistent without changing
    existing Pyrogram functionality.
    """
    kwargs = {"text": text}

    if callback_data is not None:
        kwargs["callback_data"] = callback_data

    if url is not None:
        kwargs["url"] = url

    if user_id is not None:
        kwargs["user_id"] = user_id

    return InlineKeyboardButton(**kwargs)


def _progress_bar(played, duration):
    """
    Generates a lightweight 10-position progress bar.
    Safely handles invalid/zero duration.
    """
    try:
        played_sec = time_to_seconds(played)
        duration_sec = time_to_seconds(duration)

        if duration_sec <= 0:
            return "—————————◉"

        percentage = (played_sec / duration_sec) * 100
        percentage = max(0, min(100, percentage))

        # Keep the same visual 10-position style.
        position = min(9, int(percentage / 10))

        bar = ["—"] * 10
        bar[position] = "◉"

        return "".join(bar)

    except (TypeError, ValueError, ZeroDivisionError):
        return "—————————◉"


# ============================================================
# Track / Search Buttons
# ============================================================

def track_markup(_, videoid, user_id, channel, fplay):
    return [
        [
            _button(
                text=_["P_B_1"],
                callback_data=(
                    f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}"
                ),
            ),
            _button(
                text=_["P_B_2"],
                callback_data=(
                    f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}"
                ),
            ),
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]


# ============================================================
# Active Stream + Timer
# ============================================================

def stream_markup_timer(_, chat_id, played, dur):
    bar = _progress_bar(played, dur)

    return [
        [
            _button(
                text=f"{played} {bar} {dur}",
                url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
            )
        ],
        [
            _button(
                text="▷",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
            _button(
                text="II",
                callback_data=f"ADMIN Pause|{chat_id}",
            ),
            _button(
                text="↻",
                callback_data=f"ADMIN Replay|{chat_id}",
            ),
            _button(
                text="‣‣I",
                callback_data=f"ADMIN Skip|{chat_id}",
            ),
            _button(
                text="▢",
                callback_data=f"ADMIN Stop|{chat_id}",
            ),
        ],
        [
            _button(
                text="💬 sᴜᴘᴘᴏʀᴛ",
                url=SUPPORT_GROUP,
            ),
            _button(
                text="📢 ᴄʜᴀɴɴᴇʟ",
                url=SUPPORT_CHANNEL,
            ),
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            )
        ],
    ]


# ============================================================
# Active Stream Controls
# ============================================================

def stream_markup(_, chat_id):
    return [
        [
            _button(
                text="▷",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
            _button(
                text="II",
                callback_data=f"ADMIN Pause|{chat_id}",
            ),
            _button(
                text="↻",
                callback_data=f"ADMIN Replay|{chat_id}",
            ),
            _button(
                text="‣‣I",
                callback_data=f"ADMIN Skip|{chat_id}",
            ),
            _button(
                text="▢",
                callback_data=f"ADMIN Stop|{chat_id}",
            ),
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            )
        ],
    ]


# ============================================================
# Playlist
# ============================================================

def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    return [
        [
            _button(
                text=_["P_B_1"],
                callback_data=(
                    f"NandPlaylists "
                    f"{videoid}|{user_id}|{ptype}|a|{channel}|{fplay}"
                ),
            ),
            _button(
                text=_["P_B_2"],
                callback_data=(
                    f"NandPlaylists "
                    f"{videoid}|{user_id}|{ptype}|v|{channel}|{fplay}"
                ),
            ),
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]


# ============================================================
# Live Stream
# ============================================================

def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    return [
        [
            _button(
                text=_["P_B_3"],
                callback_data=(
                    f"LiveStream "
                    f"{videoid}|{user_id}|{mode}|{channel}|{fplay}"
                ),
            )
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]


# ============================================================
# Search Slider
# ============================================================

def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    # Prevent unnecessarily large callback_data.
    query = str(query)[:20]

    return [
        [
            _button(
                text=_["P_B_1"],
                callback_data=(
                    f"MusicStream "
                    f"{videoid}|{user_id}|a|{channel}|{fplay}"
                ),
            ),
            _button(
                text=_["P_B_2"],
                callback_data=(
                    f"MusicStream "
                    f"{videoid}|{user_id}|v|{channel}|{fplay}"
                ),
            ),
        ],
        [
            _button(
                text="◁",
                callback_data=(
                    f"slider B|{query_type}|{query}|"
                    f"{user_id}|{channel}|{fplay}"
                ),
            ),
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
            ),
            _button(
                text="▷",
                callback_data=(
                    f"slider F|{query_type}|{query}|"
                    f"{user_id}|{channel}|{fplay}"
                ),
            ),
        ],
    ]


# ============================================================
# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi
#
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ============================================================

# ❤️ Love From ShrutiBots
