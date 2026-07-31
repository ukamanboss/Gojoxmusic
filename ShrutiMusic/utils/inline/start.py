# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.

from pyrogram.types import InlineKeyboardButton
from pyrogram.enums import ButtonStyle
import config
from ShrutiMusic import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true",
                style=ButtonStyle.SUCCESS
            ),
            InlineKeyboardButton(
                text=_["S_B_2"],
                url=config.SUPPORT_GROUP,
                style=ButtonStyle.PRIMARY
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["E_X_1"],
                url=config.UPSTREAM_REPO,
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                text=_["S_B_11"],
                callback_data="about_page",
                style=ButtonStyle.SUCCESS
            )
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true",
                style=ButtonStyle.SUCCESS
            )
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_11"],
                callback_data="about_page",
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                text=_["S_B_12"],
                callback_data="owner_page",
                style=ButtonStyle.PRIMARY
            )
        ],
        [
            InlineKeyboardButton(
                text=_["E_X_1"],
                callback_data="fork_repo",
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                text=_["S_B_5"],
                user_id=config.OWNER_ID,
                style=ButtonStyle.SUCCESS
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_4"],
                callback_data="help_page_1",
                style=ButtonStyle.PRIMARY
            )
        ],
    ]
    return buttons


def about_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_6"],
                url=config.SUPPORT_CHANNEL,
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                text=_["S_B_2"],
                url=config.SUPPORT_GROUP,
                style=ButtonStyle.SUCCESS
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data="settingsback_helper",
                style=ButtonStyle.PRIMARY
            )
        ]
    ]
    return buttons


def owner_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_H_1"],
                url=config.INSTAGRAM,
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                text=_["S_H_2"],
                url=config.YOUTUBE,
                style=ButtonStyle.DANGER
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_H_3"],
                url=config.GITHUB,
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                text=_["S_H_4"],
                url=config.DONATE,
                style=ButtonStyle.SUCCESS
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data="settingsback_helper",
                style=ButtonStyle.PRIMARY
            )
        ]
    ]
    return buttons
