# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import os
import asyncio
import colorsys
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from ShrutiMusic import app

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"


def get_vibrant_color(img: Image.Image) -> tuple:
    """Extracts a dominant color from the artwork and boosts its vibrancy for UI accents."""
    try:
        small = img.copy().resize((20, 20), Image.Resampling.LANCZOS).convert("RGB")
        pixels = list(small.getdata())
        
        best_color = (88, 166, 255)
        max_score = -1

        for r, g, b in pixels:
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            # Prefer colors that aren't too dark or washed out
            score = s * v
            if 0.15 < v < 0.95 and s > 0.25 and score > max_score:
                max_score = score
                # Boost saturation and brightness so it pops on dark glass
                s = min(1.0, max(0.65, s * 1.2))
                v = min(1.0, max(0.85, v * 1.2))
                nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
                best_color = (int(nr * 255), int(ng * 255), int(nb * 255))

        return best_color
    except Exception:
        return (88, 166, 255)


def wrap_and_truncate(draw, text: str, font, max_width: int, max_lines: int = 2) -> list:
    """Wraps text into 2 lines and adds '...' if it still overflows."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while draw.textlength(last + "...", font=font) > max_width and len(last) > 0:
            last = last[:-1]
        lines[-1] = last.strip() + "..."

    return lines


def draw_player_controls(draw: ImageDraw.ImageDraw, center_x: int, y: int, accent: tuple):
    """Draws crisp vector media player controls (Prev, Play/Pause, Next)."""
    # 1. Central Play/Pause Circle Button
    r = 32
    draw.ellipse([center_x - r, y - r, center_x + r, y + r], fill=(*accent, 255))
    
    # Pause Bars inside Circle
    bar_w, bar_h = 5, 20
    gap = 5
    draw.rounded_rectangle(
        [center_x - gap - bar_w, y - bar_h // 2, center_x - gap, y + bar_h // 2],
        radius=2, fill=(15, 15, 20, 255)
    )
    draw.rounded_rectangle(
        [center_x + gap, y - bar_h // 2, center_x + gap + bar_w, y + bar_h // 2],
        radius=2, fill=(15, 15, 20, 255)
    )

    # 2. Next Button (Right)
    nx = center_x + 85
    draw.polygon([(nx, y - 12), (nx, y + 12), (nx + 18, y)], fill=(255, 255, 255, 220))
    draw.rounded_rectangle([nx + 18, y - 12, nx + 22, y + 12], radius=1, fill=(255, 255, 255, 220))

    # 3. Previous Button (Left)
    px = center_x - 85
    draw.polygon([(px, y - 12), (px, y + 12), (px - 18, y)], fill=(255, 255, 255, 220))
    draw.rounded_rectangle([px - 22, y - 12, px - 18, y + 12], radius=1, fill=(255, 255, 255, 220))


def _render_sync(thumb_path: Path, out_path: str, title: str, duration: str, views: str, channel: str, bot_username: str):
    """CPU-bound Pillow image generation isolated for thread execution."""
    try:
        if thumb_path and thumb_path.exists():
            base_img = Image.open(thumb_path).convert("RGBA")
        else:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
    except Exception:
        base_img = Image.open(DEFAULT_THUMB).convert("RGBA")

    accent = get_vibrant_color(base_img)

    # 1. CINEMATIC BLURRED BACKGROUND
    bg = base_img.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(55))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)

    # 2. FROSTED GLASSMORPHISM CARD
    glass = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glass)
    
    # Outer glass board
    card_box = [45, 45, CANVAS_W - 45, CANVAS_H - 45]
    g_draw.rounded_rectangle(card_box, radius=42, fill=(18, 18, 24, 165), outline=(255, 255, 255, 45), width=2)
    
    # Ambient Accent Glow behind Artwork
    art_size = 480
    art_x = 95
    art_y = (CANVAS_H - art_size) // 2

    glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.rounded_rectangle(
        [art_x - 15, art_y - 15, art_x + art_size + 15, art_y + art_size + 15],
        radius=50, fill=(*accent, 85)
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(35))

    bg = Image.alpha_composite(bg, glass)
    bg = Image.alpha_composite(bg, glow_layer)

    # 3. MAIN ARTWORK (PERFECT SQUARE CROP + ROUNDED CORNERS)
    min_dim = min(base_img.width, base_img.height)
    left = (base_img.width - min_dim) / 2
    top = (base_img.height - min_dim) / 2
    art = base_img.crop((left, top, left + min_dim, top + min_dim))
    art = art.resize((art_size, art_size), Image.Resampling.LANCZOS)

    mask = Image.new("L", (art_size, art_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, art_size, art_size], radius=36, fill=255)
    art.putalpha(mask)

    # Subtle border around artwork
    bg.paste(art, (art_x, art_y), art)
    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle([art_x, art_y, art_x + art_size, art_y + art_size], radius=36, outline=(255, 255, 255, 60), width=2)

    # 4. LOAD FONTS
    try:
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 46)
        font_sub = ImageFont.truetype(FONT_REGULAR_PATH, 28)
        font_badge = ImageFont.truetype(FONT_BOLD_PATH, 20)
        font_time = ImageFont.truetype(FONT_BOLD_PATH, 22)
    except Exception:
        font_title = font_sub = font_badge = font_time = ImageFont.load_default()

    # 5. RIGHT-SIDE PLAYER UI & TYPOGRAPHY
    text_x = art_x + art_size + 55
    max_text_w = (CANVAS_W - 45) - text_x - 45

    # "NOW PLAYING" Neon Badge
    badge_w, badge_h = 200, 38
    badge_y = art_y + 10
    draw.rounded_rectangle(
        [text_x, badge_y, text_x + badge_w, badge_y + badge_h],
        radius=19, fill=(*accent, 35), outline=(*accent, 200), width=2
    )
    draw.ellipse([text_x + 16, badge_y + 13, text_x + 28, badge_y + 25], fill=(*accent, 255))
    draw.text((text_x + 38, badge_y + 7), "NOW PLAYING", fill=(255, 255, 255, 240), font=font_badge)

    # Bot Branding Top-Right
    if bot_username:
        brand_txt = f"@{bot_username}"
        b_w = draw.textlength(brand_txt, font=font_badge)
        draw.text((CANVAS_W - 90 - b_w, badge_y + 7), brand_txt, fill=(255, 255, 255, 130), font=font_badge)

    # Song Title (2-Line Smart Wrap)
    title_lines = wrap_and_truncate(draw, title, font_title, max_text_w, max_lines=2)
    title_y = badge_y + 62
    for line in title_lines:
        draw.text((text_x + 2, title_y + 2), line, fill=(0, 0, 0, 160), font=font_title)
        draw.text((text_x, title_y), line, fill=(255, 255, 255, 255), font=font_title)
        title_y += 56

    # Channel & Views Info (Clean Text without Broken Emojis)
    meta_y = art_y + 205
    clean_channel = wrap_and_truncate(draw, f"Artist :  {channel}", font_sub, max_text_w, max_lines=1)[0]
    draw.text((text_x, meta_y), clean_channel, fill=(210, 210, 220, 255), font=font_sub)
    draw.text((text_x, meta_y + 42), f"Views :  {views}", fill=(165, 165, 180, 255), font=font_sub)

    # 6. PROGRESS BAR
    bar_y = art_y + 325
    bar_w = max_text_w
    
    # Background Track
    draw.rounded_rectangle([text_x, bar_y, text_x + bar_w, bar_y + 8], radius=4, fill=(255, 255, 255, 50))
    
    # Active Track (35% Progress)
    prog_w = int(bar_w * 0.35)
    draw.rounded_rectangle([text_x, bar_y, text_x + prog_w, bar_y + 8], radius=4, fill=(*accent, 255))
    
    # Glowing Thumb Dot
    thumb_x = text_x + prog_w
    draw.ellipse([thumb_x - 10, bar_y - 6, thumb_x + 10, bar_y + 14], fill=(255, 255, 255, 255))
    draw.ellipse([thumb_x - 5, bar_y - 1, thumb_x + 5, bar_y + 9], fill=(*accent, 255))

    # Timestamps
    draw.text((text_x, bar_y + 18), "0:00", fill=(190, 190, 205, 255), font=font_time)
    dur_str = str(duration) if duration else "LIVE"
    dur_w = draw.textlength(dur_str, font=font_time)
    draw.text((text_x + bar_w - dur_w, bar_y + 18), dur_str, fill=(190, 190, 205, 255), font=font_time)

    # 7. VECTOR MEDIA CONTROLS
    controls_center_x = text_x + (bar_w // 2)
    draw_player_controls(draw, controls_center_x, art_y + 425, accent)

    # Save Final Image
    bg.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path


async def gen_thumb(videoid: str):
    out_path = f"cache/{videoid}_ultra_v3.png"
    if os.path.isfile(out_path):
        return out_path

    title = "ShrutiMusic Audio"
    duration = "0:00"
    views = "N/A"
    channel = "ShrutiBots"
    thumb_path = CACHE_DIR / f"raw_{videoid}.jpg"

    try:
        results = VideosSearch(videoid, limit=1)
        res_data = await results.next()
        if res_data and res_data.get("result"):
            result = res_data["result"][0]
            title = result.get("title", title)
            duration = result.get("duration", duration)
            views = result.get("viewCount", {}).get("short", views)
            channel = result.get("channel", {}).get("name", channel)
            # Pick highest resolution thumbnail from list
            thumbs = result.get("thumbnails", [])
            fallback_url = thumbs[-1]["url"].split("?")[0] if thumbs else None
        else:
            fallback_url = None

        # Try fetching direct 1080p MaxRes thumbnail first, then fallback
        hd_urls = [
            f"https://i.ytimg.com/vi/{videoid}/maxresdefault.jpg",
            f"https://i.ytimg.com/vi/{videoid}/hqdefault.jpg",
        ]
        if fallback_url:
            hd_urls.append(fallback_url)

        async with aiohttp.ClientSession() as session:
            for url in hd_urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            async with aiofiles.open(thumb_path, "wb") as f:
                                await f.write(await resp.read())
                            break
                except Exception:
                    continue

    except Exception as e:
        print(f"[gen_thumb Metadata Error] {e}")

    try:
        bot_uname = getattr(app, "username", "ShrutiBots")
        # Run heavy PIL processing in a background thread to prevent VC audio lag
        final_img = await asyncio.to_thread(
            _render_sync,
            thumb_path,
            out_path,
            title,
            duration,
            views,
            channel,
            bot_uname,
        )
        return final_img
    except Exception as e:
        print(f"[gen_thumb Render Error] {e}")
        traceback.print_exc()
        return None
    finally:
        if thumb_path.exists():
            try:
                os.remove(thumb_path)
            except Exception:
                pass
