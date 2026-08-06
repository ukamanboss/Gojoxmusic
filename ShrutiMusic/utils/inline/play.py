# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import math
from pyrogram.types import InlineKeyboardButton
from ShrutiMusic.utils.formatters import time_to_seconds
from config import BOT_USERNAME, SUPPORT_GROUP, SUPPORT_CHANNEL

def _button(text, callback_data=None, url=None, user_id=None, style=None):
    kwargs = {"text": text}
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if url is not None:
        kwargs["url"] = url
    if user_id is not None:
        kwargs["user_id"] = user_id
    return InlineKeyboardButton(**kwargs)


def _progress_bar(played, duration):
    try:
        played_sec = time_to_seconds(played)
        duration_sec = time_to_seconds(duration)
        if duration_sec <= 0:
            return "—————————◉"
        percentage = (played_sec / duration_sec) * 100
        percentage = max(0, min(100, percentage))
        position = min(9, int(percentage / 10))
        bar = ["—"] * 10
        bar[position] = "◉"
        return "".join(bar)
    except (TypeError, ValueError, ZeroDivisionError):
        return "—————————◉"


def track_markup(_, videoid, user_id, channel, fplay):
    return [
        [
            _button(text=_["P_B_1"], callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}"),
            _button(text=_["P_B_2"], callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}"),
        ],
        [
            _button(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}")
        ],
    ]


def stream_markup_timer(_, chat_id, played, dur):
    bar = _progress_bar(played, dur)
    return [
        [
            _button(text=f"{played} {bar} {dur}", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ],
        [
            _button(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            _button(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
            _button(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            _button(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            _button(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            _button(text="💬 sᴜᴘᴘᴏʀᴛ", url=SUPPORT_GROUP),
            _button(text="📢 ᴄʜᴀɴɴᴇʟ", url=SUPPORT_CHANNEL),
        ],
        [
            _button(text=_["CLOSE_BUTTON"], callback_data="close")
        ],
    ]


def stream_markup(_, chat_id):
    return [
        [
            _button(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            _button(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
            _button(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            _button(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            _button(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            _button(text=_["CLOSE_BUTTON"], callback_data="close")
        ],
    ]


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    return [
        [
            _button(text=_["P_B_1"], callback_data=f"NandPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}"),
            _button(text=_["P_B_2"], callback_data=f"NandPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}"),
        ],
        [
            _button(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}")
        ],
    ]


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    return [
        [
            _button(text=_["P_B_3"], callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}")
        ],
        [
            _button(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}")
        ],
    ]


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = str(query)[:20]
    return [
        [
            _button(text=_["P_B_1"], callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}"),
            _button(text=_["P_B_2"], callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}"),
        ],
        [
            _button(text="◁", callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}"),
            _button(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {query}|{user_id}"),
            _button(text="▷", callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}"),
        ],
    ]

# ❤️ Love From ShrutiBots
