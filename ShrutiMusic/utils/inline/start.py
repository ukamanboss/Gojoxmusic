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
# Internal helper
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


# ============================================================
# Start Panel
# ============================================================

def start_panel(_):
    return [
        [
            _button(
                text=_["S_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true",
                style="success"  # Green
            ),
            _button(
                text=_["S_B_2"],
                url=config.SUPPORT_GROUP,
                style="primary"  # Blue
            ),
        ],
        [
            _button(
                text=_["E_X_1"],
                url=config.UPSTREAM_REPO,
                style="primary"  # Blue
            ),
            _button(
                text=_["S_B_11"],
                callback_data="about_page",
                style="danger"   # Red
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
                style="success"  # Green
            )
        ],
        [
            _button(
                text=_["S_B_11"],
                callback_data="about_page",
                style="danger"   # Red
            ),
            _button(
                text=_["S_B_12"],
                callback_data="owner_page",
                style="primary"  # Blue
            ),
        ],
        [
            _button(
                text=_["E_X_1"],
                callback_data="fork_repo",
                style="primary"  # Blue
            ),
            _button(
                text=_["S_B_5"],
                user_id=config.OWNER_ID,
                style="danger"   # Red
            ),
        ],
        [
            _button(
                text=_["S_B_4"],
                callback_data="help_page_1",
                style="primary"  # Blue
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
                style="primary"  # Blue
            ),
            _button(
                text=_["S_B_2"],
                url=config.SUPPORT_GROUP,
                style="primary"  # Blue
            ),
        ],
        [
            _button(
                text=_["BACK_BUTTON"],
                callback_data="settingsback_helper",
                style="danger"   # Red
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
                style="primary"  # Blue
            ),
            _button(
                text=_["S_H_2"],
                url=config.YOUTUBE,
                style="danger"   # Red (YouTube theme)
            ),
        ],
        [
            _button(
                text=_["S_H_3"],
                url=config.GITHUB,
                style="primary"  # Blue
            ),
            _button(
                text=_["S_H_4"],
                url=config.DONATE,
                style="success"  # Green (Money theme)
            ),
        ],
        [
            _button(
                text=_["BACK_BUTTON"],
                callback_data="settingsback_helper",
                style="danger"   # Red
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
