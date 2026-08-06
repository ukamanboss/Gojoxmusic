# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import os
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from py_yt import VideosSearch
from ShrutiMusic import app

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"


def truncate(text, font, max_width, draw):
    """Truncates text with '...' if it exceeds max width"""
    if draw.textlength(text, font) <= max_width:
        return text
    else:
        while draw.textlength(text + "...", font) > max_width and len(text) > 0:
            text = text[:-1]
        return text + "..."


async def gen_thumb(videoid: str):
    # Changed cache name to avoid loading old glitched images
    out_path = f"cache/{videoid}_premium_v2.png"
    if os.path.isfile(out_path):
        return out_path

    try:
        # THE FIX: Search videoid directly instead of URL to avoid random YouTube results
        results = VideosSearch(videoid, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        views = result.get("viewCount", {}).get("short", "Unknown")
        channel = result.get("channel", {}).get("name", "Unknown Channel")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]

        thumb_path = CACHE_DIR / f"thumb_{videoid}.png"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumburl) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await resp.read())
        except Exception:
            pass

        if thumb_path.exists():
            base_img = Image.open(thumb_path).convert("RGBA")
        else:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")

    except Exception as e:
        print(f"[gen_thumb Error] {e}")
        try:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
            title = "ShrutiMusic Audio"
            duration = "0:00"
            views = "N/A"
            channel = "ShrutiBots"
        except:
            traceback.print_exc()
            return None

    try:
        # 1. APPLE MUSIC STYLE BLURRED BACKGROUND
        background = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(50))
        
        # Dark overlay for clear text visibility
        overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 160))
        background = Image.alpha_composite(background, overlay)
        
        draw = ImageDraw.Draw(background)
        
        # Load Fonts
        try:
            font_title = ImageFont.truetype(FONT_BOLD_PATH, 60)
            font_channel = ImageFont.truetype(FONT_REGULAR_PATH, 35)
            font_small = ImageFont.truetype(FONT_BOLD_PATH, 28)
            font_time = ImageFont.truetype(FONT_REGULAR_PATH, 22)
        except:
            font_title = ImageFont.load_default()
            font_channel = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_time = ImageFont.load_default()

        # 2. MAIN ARTWORK (ROUNDED SQUARE)
        art_size = 480
        art_x = 80
        art_y = (CANVAS_H - art_size) // 2

        # Center crop the art to a perfect square
        min_dim = min(base_img.width, base_img.height)
        left = (base_img.width - min_dim) / 2
        top = (base_img.height - min_dim) / 2
        right = (base_img.width + min_dim) / 2
        bottom = (base_img.height + min_dim) / 2
        art = base_img.crop((left, top, right, bottom))
        art = art.resize((art_size, art_size), Image.LANCZOS)

        # Apply smooth rounded corners
        mask = Image.new("L", (art_size, art_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, art_size, art_size], radius=35, fill=255)
        art.putalpha(mask)

        # Apply 3D Drop Shadow behind the art
        shadow = Image.new("RGBA", (art_size + 40, art_size + 40), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle([0, 0, art_size + 40, art_size + 40], radius=45, fill=(0, 0, 0, 180))
        shadow = shadow.filter(ImageFilter.GaussianBlur(25))
        background.paste(shadow, (art_x - 20, art_y - 15), shadow)

        # Paste the artwork onto background
        background.paste(art, (art_x, art_y), art)

        # 3. TEXT & UI ELEMENTS
        text_x = art_x + art_size + 60
        max_text_width = CANVAS_W - text_x - 50

        # "NOW PLAYING" Header
        draw.text((text_x, art_y + 35), "N O W   P L A Y I N G", fill=(255, 255, 255, 170), font=font_small)

        # Song Title
        title_text = truncate(title, font_title, max_text_width, draw)
        draw.text((text_x, art_y + 100), title_text, fill=(255, 255, 255, 255), font=font_title)

        # Channel Name
        channel_text = truncate(f"👤 {channel}", font_channel, max_text_width, draw)
        draw.text((text_x, art_y + 185), channel_text, fill=(200, 200, 200, 255), font=font_channel)

        # View Count
        draw.text((text_x, art_y + 245), f"👁‍🗨 {views} Views", fill=(170, 170, 170, 255), font=font_small)

        # 4. PROGRESS BAR UI
        bar_y = art_y + 390
        bar_width = max_text_width - 20
        
        # Grey background line
        draw.line([(text_x, bar_y), (text_x + bar_width, bar_y)], fill=(255, 255, 255, 70), width=6)
        
        # White progress line (simulating 30% played)
        progress_w = int(bar_width * 0.3)
        draw.line([(text_x, bar_y), (text_x + progress_w, bar_y)], fill=(255, 255, 255, 255), width=6)
        
        # Progress thumb (Circle)
        draw.ellipse([text_x + progress_w - 9, bar_y - 9, text_x + progress_w + 9, bar_y + 9], fill=(255, 255, 255, 255))

        # Timestamps
        draw.text((text_x, bar_y + 15), "0:00", fill=(200, 200, 200, 255), font=font_time)
        
        dur_w = draw.textlength(duration, font=font_time)
        draw.text((text_x + bar_width - dur_w, bar_y + 15), duration, fill=(200, 200, 200, 255), font=font_time)

        # Save and return
        background.save(out_path, quality=95, optimize=True)

        # Cleanup old raw image to save space
        if thumb_path.exists():
            try:
                os.remove(thumb_path)
            except:
                pass

        return out_path

    except Exception as e:
        print(f"[gen_thumb Generation Error] {e}")
        traceback.print_exc()
        return None
