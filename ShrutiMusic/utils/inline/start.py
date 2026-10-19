# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# All rights reserved.

from pyrogram.types import InlineKeyboardButton
import config
from ShrutiMusic import app


def _get_safe_owner_url():
    """Returns a safe URL for the owner button to prevent ButtonUserPrivacyRestricted crashes."""
    owner_username = getattr(config, "OWNER_USERNAME", None)
    if owner_username:
        clean_username = str(owner_username).lstrip("@").strip()
        if clean_username.startswith("http"):
            return clean_username
        return f"https://t.me/{clean_username}"
    
    # Fallback to support group if username isn't set, avoiding restricted tg://user?id= links
    return getattr(config, "SUPPORT_GROUP", "https://t.me/Telegram")


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_GROUP),
        ],
    ]
    return buttons


def private_panel(_):
    owner_url = _get_safe_owner_url()

    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(text=_["S_B_4"], callback_data="settings_back_helper"),
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], url=owner_url),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_GROUP),
        ],
        [
            InlineKeyboardButton(text=_["S_B_6"], url=config.SUPPORT_CHANNEL),
            InlineKeyboardButton(text=_["S_B_7"], url=config.UPSTREAM_REPO),
        ],
    ]
    return buttons


def about_panel(_):
    owner_url = _get_safe_owner_url()

    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_6"], url=config.SUPPORT_CHANNEL),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_GROUP),
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], url=owner_url),
            InlineKeyboardButton(text=_["S_B_7"], url=config.UPSTREAM_REPO),
        ],
        [
            InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="settingsback_helper"),
        ],
    ]
    return buttons


def owner_panel(_):
    owner_url = _get_safe_owner_url()

    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_5"], url=owner_url),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_GROUP),
        ],
        [
            InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="settingsback_helper"),
        ],
    ]
    return buttons
