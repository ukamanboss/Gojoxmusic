"""
░█▀█░█▀▄░█▀█░█▀█░█▀▄░▀█▀░█▀▀░▀█▀░█▀█░█▀▄░█░█░░░█░░░▀█▀░█▀▀░█▀▀░█▀█░█▀▀░█▀▀
░█▀▀░█▀▄░█░█░█▀▀░█▀▄░░█░░█▀▀░░█░░█▀█░█▀▄░░█░░░░█░░░░█░░█░░░█▀▀░█░█░▀▀█░█▀▀
░▀░░░▀░▀░▀▀▀░▀░░░▀░▀░▀▀▀░▀▀▀░░▀░░▀░▀░▀░▀░░▀░░░░▀▀▀░▀▀▀░▀▀▀░▀▀▀░▀░▀░▀▀▀░▀▀▀

Copyright (c) 2025 Nand Yaduwanshi (@NoxxOP)
Location: Supaul, Bihar
Email: badboy809075@gmail.com
GitHub: https://github.com/NoxxOP

All rights reserved.

This code is the intellectual property of Nand Yaduwanshi.
You are not allowed to copy, modify, redistribute, or use this
code for commercial or personal projects without explicit permission.

Allowed:
- Forking for personal learning
- Submitting improvements via pull requests

Not Allowed:
- Claiming this code as your own
- Re-uploading without credit or permission
- Selling or using commercially

Love From ShrutiBots
Telegram: https://t.me/ShrutiBots
"""

from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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


def help_pannel_page1(_, START: Union[bool, int] = None):
    return InlineKeyboardMarkup(
        [
            [
                PremiumInlineButton(text=_["H_B_1"], callback_data="help_callback hb1", style="primary"),
                PremiumInlineButton(text=_["H_B_2"], callback_data="help_callback hb2", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_3"], callback_data="help_callback hb3", style="primary"),
                PremiumInlineButton(text=_["H_B_4"], callback_data="help_callback hb4", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_5"], callback_data="help_callback hb5", style="primary"),
                PremiumInlineButton(text=_["H_B_6"], callback_data="help_callback hb6", style="primary"),
                PremiumInlineButton(text=_["H_B_7"], callback_data="help_callback hb7", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_8"], callback_data="help_callback hb8", style="primary"),
                PremiumInlineButton(text=_["H_B_9"], callback_data="help_callback hb9", style="primary"),
                PremiumInlineButton(text=_["H_B_10"], callback_data="help_callback hb10", style="primary"),
            ],
            [
                PremiumInlineButton(text="⏮", callback_data="help_page_4", style="primary"),
                PremiumInlineButton(
                    text=_["BACK_BUTTON"] if START else _["CLOSE_BUTTON"],
                    callback_data="settingsback_helper" if START else "close",
                    style="danger"
                ),
                PremiumInlineButton(text="⏭", callback_data="help_page_2", style="primary"),
            ],
        ]
    )

def help_pannel_page2(_, START: Union[bool, int] = None):
    return InlineKeyboardMarkup(
        [
            [
                PremiumInlineButton(text=_["H_B_11"], callback_data="help_callback hb11", style="primary"),
                PremiumInlineButton(text=_["H_B_12"], callback_data="help_callback hb12", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_13"], callback_data="help_callback hb13", style="primary"),
                PremiumInlineButton(text=_["H_B_14"], callback_data="help_callback hb14", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_15"], callback_data="help_callback hb15", style="primary"),
                PremiumInlineButton(text=_["H_B_16"], callback_data="help_callback hb16", style="primary"),
                PremiumInlineButton(text=_["H_B_17"], callback_data="help_callback hb17", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_18"], callback_data="help_callback hb18", style="primary"),
                PremiumInlineButton(text=_["H_B_19"], callback_data="help_callback hb19", style="primary"),
                PremiumInlineButton(text=_["H_B_20"], callback_data="help_callback hb20", style="primary"),
            ],
            [
                PremiumInlineButton(text="⏮", callback_data="help_page_1", style="primary"),
                PremiumInlineButton(
                    text=_["BACK_BUTTON"] if START else _["CLOSE_BUTTON"],
                    callback_data="settingsback_helper" if START else "close",
                    style="danger"
                ),
                PremiumInlineButton(text="⏭", callback_data="help_page_3", style="primary"),
            ],
        ]
    )

def help_pannel_page3(_, START: Union[bool, int] = None):
    return InlineKeyboardMarkup(
        [
            [
                PremiumInlineButton(text=_["H_B_21"], callback_data="help_callback hb21", style="primary"),
                PremiumInlineButton(text=_["H_B_22"], callback_data="help_callback hb22", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_23"], callback_data="help_callback hb23", style="primary"),
                PremiumInlineButton(text=_["H_B_24"], callback_data="help_callback hb24", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_25"], callback_data="help_callback hb25", style="primary"),
                PremiumInlineButton(text=_["H_B_26"], callback_data="help_callback hb26", style="primary"),
                PremiumInlineButton(text=_["H_B_27"], callback_data="help_callback hb27", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_28"], callback_data="help_callback hb28", style="primary"),
                PremiumInlineButton(text=_["H_B_29"], callback_data="help_callback hb29", style="primary"),
                PremiumInlineButton(text=_["H_B_30"], callback_data="help_callback hb30", style="primary"),
            ],
            [
                PremiumInlineButton(text="⏮", callback_data="help_page_2", style="primary"),
                PremiumInlineButton(
                    text=_["BACK_BUTTON"] if START else _["CLOSE_BUTTON"],
                    callback_data="settingsback_helper" if START else "close",
                    style="danger"
                ),
                PremiumInlineButton(text="⏭", callback_data="help_page_4", style="primary"),
            ],
        ]
    )

def help_pannel_page4(_, START: Union[bool, int] = None):
    return InlineKeyboardMarkup(
        [
            [
                PremiumInlineButton(text=_["H_B_31"], callback_data="help_callback hb31", style="primary"),
                PremiumInlineButton(text=_["H_B_32"], callback_data="help_callback hb32", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_33"], callback_data="help_callback hb33", style="primary"),
                PremiumInlineButton(text=_["H_B_34"], callback_data="help_callback hb34", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_35"], callback_data="help_callback hb35", style="primary"),
                PremiumInlineButton(text=_["H_B_37"], callback_data="help_callback hb37", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_38"], callback_data="help_callback hb38", style="primary"),
                PremiumInlineButton(text=_["H_B_39"], callback_data="help_callback hb39", style="primary"),
            ],
            [
                PremiumInlineButton(text=_["H_B_36"], callback_data="help_callback hb36", style="primary"),
            ],   
            [
                PremiumInlineButton(text="⏮", callback_data="help_page_3", style="primary"),
                PremiumInlineButton(
                    text=_["BACK_BUTTON"] if START else _["CLOSE_BUTTON"],
                    callback_data="settingsback_helper" if START else "close",
                    style="danger"
                ),
                PremiumInlineButton(text="⏭", callback_data="help_page_1", style="primary"),
            ],
        ]
    )

def help_back_markup(_, page: int = 1):
    return InlineKeyboardMarkup(
        [
            [
                PremiumInlineButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"help_page_{page}",
                    style="danger"
                )
            ]
        ]
    )


def private_help_panel(_):
    return [
        [
            PremiumInlineButton(
                text=_["S_B_4"],
                url=f"https://t.me/{app.username}?start=help",
                style="primary"
            ),
        ]
    ]
