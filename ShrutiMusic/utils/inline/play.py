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
# CUSTOM NATIVE STYLE BUTTON CLASS
# ============================================================
class PremiumInlineButton(InlineKeyboardButton):
    """
    Ye custom class Telegram API ke native style field ko 
    (primary=Blue, success=Green, danger=Red) support karwati hai.
    """
    def __init__(self, text, callback_data=None, url=None, user_id=None, style=None, **kwargs):
        super().__init__(text=text, callback_data=callback_data, url=url, user_id=user_id, **kwargs)
        self.style = style

    def to_dict(self):
        dic = super().to_dict()
        if self.style:
            dic['style'] = self.style
        return dic


# ============================================================
# Internal helpers
# ============================================================

def _button(text, callback_data=None, url=None, user_id=None, style=None):
    """
    Lightweight button factory.
    Ab ye PremiumInlineButton use karke native styles support karta hai.
    """
    kwargs = {"text": text}

    if callback_data is not None:
        kwargs["callback_data"] = callback_data

    if url is not None:
        kwargs["url"] = url

    if user_id is not None:
        kwargs["user_id"] = user_id
        
    if style is not None:
        kwargs["style"] = style

    return PremiumInlineButton(**kwargs)


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
                style="success"  # Green
            ),
            _button(
                text=_["P_B_2"],
                callback_data=(
                    f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}"
                ),
                style="primary"  # Blue
            ),
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
                style="danger"   # Red
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
                style="primary"  # Blue
            )
        ],
        [
            _button(
                text="▷",
                callback_data=f"ADMIN Resume|{chat_id}",
                style="success"  # Green
            ),
            _button(
                text="II",
                callback_data=f"ADMIN Pause|{chat_id}",
                style="primary"  # Blue
            ),
            _button(
                text="↻",
                callback_data=f"ADMIN Replay|{chat_id}",
                style="primary"  # Blue
            ),
            _button(
                text="‣‣I",
                callback_data=f"ADMIN Skip|{chat_id}",
                style="primary"  # Blue
            ),
            _button(
                text="▢",
                callback_data=f"ADMIN Stop|{chat_id}",
                style="danger"   # Red
            ),
        ],
        [
            _button(
                text="💬 sᴜᴘᴘᴏʀᴛ",
                url=SUPPORT_GROUP,
                style="primary"  # Blue
            ),
            _button(
                text="📢 ᴄʜᴀɴɴᴇʟ",
                url=SUPPORT_CHANNEL,
                style="primary"  # Blue
            ),
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style="danger"   # Red
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
                style="success"  # Green
            ),
            _button(
                text="II",
                callback_data=f"ADMIN Pause|{chat_id}",
                style="primary"  # Blue
            ),
            _button(
                text="↻",
                callback_data=f"ADMIN Replay|{chat_id}",
                style="primary"  # Blue
            ),
            _button(
                text="‣‣I",
                callback_data=f"ADMIN Skip|{chat_id}",
                style="primary"  # Blue
            ),
            _button(
                text="▢",
                callback_data=f"ADMIN Stop|{chat_id}",
                style="danger"   # Red
            ),
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style="danger"   # Red
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
                style="success"  # Green
            ),
            _button(
                text=_["P_B_2"],
                callback_data=(
                    f"NandPlaylists "
                    f"{videoid}|{user_id}|{ptype}|v|{channel}|{fplay}"
                ),
                style="primary"  # Blue
            ),
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
                style="danger"   # Red
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
                style="success"  # Green
            )
        ],
        [
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
                style="danger"   # Red
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
                style="success"  # Green
            ),
            _button(
                text=_["P_B_2"],
                callback_data=(
                    f"MusicStream "
                    f"{videoid}|{user_id}|v|{channel}|{fplay}"
                ),
                style="primary"  # Blue
            ),
        ],
        [
            _button(
                text="◁",
                callback_data=(
                    f"slider B|{query_type}|{query}|"
                    f"{user_id}|{channel}|{fplay}"
                ),
                style="primary"  # Blue
            ),
            _button(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
                style="danger"   # Red
            ),
            _button(
                text="▷",
                callback_data=(
                    f"slider F|{query_type}|{query}|"
                    f"{user_id}|{channel}|{fplay}"
                ),
                style="primary"  # Blue
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
