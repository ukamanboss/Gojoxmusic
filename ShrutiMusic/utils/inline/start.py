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

from pyrogram.types import InlineKeyboardButton

import config
from ShrutiMusic import app


# ============================================================
# Internal helper
# ============================================================

def _button(text, callback_data=None, url=None, user_id=None):
    """
    Lightweight button factory.
    Does not change Pyrogram button behaviour.
    """
    kwargs = {"text": text}

    if callback_data is not None:
        kwargs["callback_data"] = callback_data

    if url is not None:
        kwargs["url"] = url

    if user_id is not None:
        kwargs["user_id"] = user_id

    return InlineKeyboardButton(**kwargs)


# ============================================================
# Start Panel
# ============================================================

def start_panel(_):
    return [
        [
            _button(
                text=_["S_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
            _button(
                text=_["S_B_2"],
                url=config.SUPPORT_GROUP,
            ),
        ],
        [
            _button(
                text=_["E_X_1"],
                url=config.UPSTREAM_REPO,
            ),
            _button(
                text=_["S_B_11"],
                callback_data="about_page",
            ),
        ],
    ]


# ============================================================
# Private Panel
# ============================================================

def private_panel(_):
    return [
        [
            _button(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [
            _button(
                text=_["S_B_11"],
                callback_data="about_page",
            ),
            _button(
                text=_["S_B_12"],
                callback_data="owner_page",
            ),
        ],
        [
            _button(
                text=_["E_X_1"],
                callback_data="fork_repo",
            ),
            _button(
                text=_["S_B_5"],
                user_id=config.OWNER_ID,
            ),
        ],
        [
            _button(
                text=_["S_B_4"],
                callback_data="help_page_1",
            )
        ],
    ]


# ============================================================
# About Panel
# ============================================================

def about_panel(_):
    return [
        [
            _button(
                text=_["S_B_6"],
                url=config.SUPPORT_CHANNEL,
            ),
            _button(
                text=_["S_B_2"],
                url=config.SUPPORT_GROUP,
            ),
        ],
        [
            _button(
                text=_["BACK_BUTTON"],
                callback_data="settingsback_helper",
            )
        ],
    ]


# ============================================================
# Owner Panel
# ============================================================

def owner_panel(_):
    return [
        [
            _button(
                text=_["S_H_1"],
                url=config.INSTAGRAM,
            ),
            _button(
                text=_["S_H_2"],
                url=config.YOUTUBE,
            ),
        ],
        [
            _button(
                text=_["S_H_3"],
                url=config.GITHUB,
            ),
            _button(
                text=_["S_H_4"],
                url=config.DONATE,
            ),
        ],
        [
            _button(
                text=_["BACK_BUTTON"],
                callback_data="settingsback_helper",
            )
        ],
    ]


# ============================================================
# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi
#
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ============================================================

# ❤️ Love From ShrutiBots
