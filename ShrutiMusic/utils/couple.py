# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

from typing import Any, Dict, Union

# ============================================================
# 💖 COUPLE DATABASE (IN-MEMORY CACHE)
# ============================================================
# Bug Fix: Changed 'Coupledb' to 'coupledb' to match function calls
coupledb: Dict[int, Dict[str, Any]] = {}


async def _get_lovers(cid: int) -> dict:
    """Fetch all couples for a specific chat."""
    chat_data = coupledb.get(cid, {})
    return chat_data.get("couple", {})


async def get_image(cid: int) -> str:
    """Fetch the latest couple image link for a specific chat."""
    chat_data = coupledb.get(cid, {})
    return chat_data.get("img", "")


async def get_couple(cid: int, date: str) -> Union[dict, bool]:
    """Get the couple details for a specific date in a chat."""
    lovers = await _get_lovers(cid)
    return lovers.get(date, False)


async def save_couple(cid: int, date: str, couple: dict, img: str) -> None:
    """Save a new couple and their generated image for a specific date."""
    if cid not in coupledb:
        coupledb[cid] = {"couple": {}, "img": ""}
        
    coupledb[cid]["couple"][date] = couple
    coupledb[cid]["img"] = img


# ❤️ Love From ShrutiBots 
