# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import os
import random
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from py_yt import VideosSearch
from ShrutiMusic import app

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# HD Resolution for better clarity
CANVAS_W, CANVAS_H = 1280, 720

# Fonts path
FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines[:2]


def create_rounded_mask(size, radius):
    """Creates a smooth rounded rectangle mask"""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return mask


def add_glass_gradient(base_canvas):
    """Adds a dark stylish gradient over the blurred background"""
    overlay = Image.new('RGBA', base_canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for y in range(CANVAS_H):
        alpha = int(255 * (y / CANVAS_H)) 
        # Darker at the bottom, slight tint at the top
        draw.line([(0, y), (CANVAS_W, y)], fill=(15, 15, 20, min(240, alpha + 60)))
        
    return Image.alpha_composite(base_canvas.convert("RGBA"), overlay)


def draw_audio_bars(draw, x_start, y_start, accent_color):
    """Draws a cool audio visualizer wave"""
    num_bars = 40
    bar_width = 6
    spacing = 4
    
    for i in range(num_bars):
        height = random.randint(10, 60)
        x = x_start + (i * (bar_width + spacing))
        y = y_start - height
        # Slightly transparent bars
        draw.rounded_rectangle([x, y, x + bar_width, y_start], radius=2, fill=(*accent_color, 180))


def get_accent_color(image):
    """Extracts a simple dominant color from the image to use as accent"""
    small_img = image.copy().resize((1, 1))
    color = small_img.getpixel((0, 0))
    # Ensure color isn't too dark
    if sum(color[:3]) < 150:
        return (66, 135, 245) # Default Blue if too dark
    return color[:3]


async def gen_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumburl) as resp:
                    if resp.status == 200:
                        thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await resp.read())
        except Exception:
            pass

        if thumb_path and thumb_path.exists():
            base_img = Image.open(thumb_path).convert("RGBA")
        else:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")

    except Exception as e:
        print(f"[gen_thumb Error - Using Default] {e}")
        try:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
            title = "ShrutiMusic Stream"
            duration = "Unknown"
            channel = "ShrutiBots"
        except:
            traceback.print_exc()
            return None

    try:
        # 1. CREATE BLURRED BACKGROUND (SPOTIFY STYLE)
        bg_canvas = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        bg_canvas = bg_canvas.filter(ImageFilter.GaussianBlur(45)) 
        canvas = add_glass_gradient(bg_canvas)
        
        draw = ImageDraw.Draw(canvas)
        accent_color = get_accent_color(base_img)

        # 2. PLACE MAIN ARTWORK (ROUNDED)
        art_size = 460
        art_x = 90
        art_y = (CANVAS_H - art_size) // 2
        
        art = base_img.resize((art_size, int(art_size * (base_img.height / base_img.width))), Image.LANCZOS)
        
        # Center crop the art to make it square
        left = (art.width - art_size)/2
        top = (art.height - art_size)/2
        right = (art.width + art_size)/2
        bottom = (art.height + art_size)/2
        art = art.crop((left, top, right, bottom))
        
        mask = create_rounded_mask((art_size, art_size), radius=40)
        art.putalpha(mask)
        
        # Glow Effect behind the art
        glow_size = art_size + 40
        glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.rounded_rectangle([0, 0, glow_size, glow_size], radius=50, fill=(*accent_color, 70))
        glow = glow.filter(ImageFilter.GaussianBlur(15))
        canvas.paste(glow, (art_x - 20, art_y - 20), glow)
        
        # Paste Main Art
        canvas.paste(art, (art_x, art_y), art)
        
        # 3. TYPOGRAPHY & INFO
        info_x = art_x + art_size + 60
        max_text_w = CANVAS_W - info_x - 40
        
        try:
            font_bold_large = ImageFont.truetype(FONT_BOLD_PATH, 55)
            font_bold_small = ImageFont.truetype(FONT_BOLD_PATH, 35)
            font_regular = ImageFont.truetype(FONT_REGULAR_PATH, 30)
        except:
            font_bold_large = ImageFont.load_default()
            font_bold_small = ImageFont.load_default()
            font_regular = ImageFont.load_default()

        # Bot Name / Brand
        draw.text((info_x, art_y + 10), "NOW PLAYING", fill=(*accent_color, 255), font=font_bold_small)
        
        # Track Title
        title_lines = wrap_text(draw, title, font_bold_large, max_text_w)
        title_y = art_y + 70
        for line in title_lines:
            # Drop shadow
            draw.text((info_x + 3, title_y + 3), line, fill=(0, 0, 0, 180), font=font_bold_large)
            draw.text((info_x, title_y), line, fill=(255, 255, 255, 255), font=font_bold_large)
            title_y += 65
            
        # Channel Name
        draw.text((info_x, title_y + 20), f"👤 {channel}", fill=(200, 200, 200, 255), font=font_regular)
        
        # Duration Label
        draw.text((info_x, title_y + 70), f"⏱️ {duration}", fill=(200, 200, 200, 255), font=font_regular)

        # Audio Visualizer at the bottom right
        draw_audio_bars(draw, info_x, art_y + art_size - 10, accent_color)

        # Save the final masterpiece
        out = CACHE_DIR / f"{videoid}_premium.png"
        canvas.save(out, quality=95, optimize=True)

        if thumb_path and thumb_path.exists():
            try:
                os.remove(thumb_path)
            except:
                pass

        return str(out)

    except Exception as e:
        print(f"[gen_thumb Processing Error] {e}")
        traceback.print_exc()
        return None
