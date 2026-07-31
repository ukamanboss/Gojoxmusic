# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.

import math

from pyrogram.types import InlineKeyboardButton

from ShrutiMusic.utils.formatters import time_to_seconds
from config import BOT_USERNAME, SUPPORT_GROUP, SUPPORT_CHANNEL


def track_markup(_, videoid, user_id, channel, fplay):
    return [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=(
                    f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}"
                ),
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=(
                    f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]


def _progress_bar(played, dur):
    try:
        played_sec = time_to_seconds(played)
        duration_sec = time_to_seconds(dur)

        if duration_sec <= 0:
            return "—————————◉"

        percentage = max(
            0,
            min(100, (played_sec / duration_sec) * 100),
        )

        position = min(9, int(percentage / 10))

        chars = ["—"] * 10
        chars[position] = "◉"

        return "".join(chars)

    except (TypeError, ValueError, ZeroDivisionError):
        return "—————————◉"


def stream_markup_timer(_, chat_id, played, dur):
    bar = _progress_bar(played, dur)

    return [
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(
                text="▷",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
            InlineKeyboardButton(
                text="II",
                callback_data=f"ADMIN Pause|{chat_id}",
            ),
            InlineKeyboardButton(
                text="↻",
                callback_data=f"ADMIN Replay|{chat_id}",
            ),
            InlineKeyboardButton(
                text="‣‣I",
                callback_data=f"ADMIN Skip|{chat_id}",
            ),
            InlineKeyboardButton(
                text="▢",
                callback_data=f"ADMIN Stop|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="💬 sᴜᴘᴘᴏʀᴛ",
                url=SUPPORT_GROUP,
            ),
            InlineKeyboardButton(
                text="📢 ᴄʜᴀɴɴᴇʟ",
                url=SUPPORT_CHANNEL,
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            )
        ],
    ]


def stream_markup(_, chat_id):
    return [
        [
            InlineKeyboardButton(
                text="▷",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
            InlineKeyboardButton(
                text="II",
                callback_data=f"ADMIN Pause|{chat_id}",
            ),
            InlineKeyboardButton(
                text="↻",
                callback_data=f"ADMIN Replay|{chat_id}",
            ),
            InlineKeyboardButton(
                text="‣‣I",
                callback_data=f"ADMIN Skip|{chat_id}",
            ),
            InlineKeyboardButton(
                text="▢",
                callback_data=f"ADMIN Stop|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            )
        ],
    ]


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    return [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=(
                    f"NandPlaylists "
                    f"{videoid}|{user_id}|{ptype}|a|{channel}|{fplay}"
                ),
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=(
                    f"NandPlaylists "
                    f"{videoid}|{user_id}|{ptype}|v|{channel}|{fplay}"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    return [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=(
                    f"LiveStream "
                    f"{videoid}|{user_id}|{mode}|{channel}|{fplay}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]


def slider_markup(
    _,
    videoid,
    user_id,
    query,
    query_type,
    channel,
    fplay,
):
    query = str(query)[:20]

    return [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=(
                    f"MusicStream "
                    f"{videoid}|{user_id}|a|{channel}|{fplay}"
                ),
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=(
                    f"MusicStream "
                    f"{videoid}|{user_id}|v|{channel}|{fplay}"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=(
                    f"slider B|{query_type}|{query}|"
                    f"{user_id}|{channel}|{fplay}"
                ),
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="▷",
                callback_data=(
                    f"slider F|{query_type}|{query}|"
                    f"{user_id}|{channel}|{fplay}"
                ),
            ),
        ],
    ]
