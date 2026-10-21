# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

import os
import re
import asyncio
import colorsys
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from unidecode import unidecode
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch

from ShrutiMusic import app
from ShrutiMusic.misc import db
import config

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"

# Yahan Aapki Custom Image (1:1 PFP) Load Hogi Fallback Ke Liye
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"

RESAMPLE_MODE = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def _clean_text(text: str, default: str = "") -> str:
    if not text: return default
    try: ascii_text = unidecode(str(text))
    except Exception: ascii_text = str(text)
    cleaned = re.sub(r"[^\x20-\x7E]", " ", ascii_text)
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else default

def _clean_bot_brand() -> str:
    raw_name = getattr(app, "name", "") or ""
    uname = getattr(app, "username", "") or ""
    try: decoded_name = unidecode(str(raw_name))
    except Exception: decoded_name = str(raw_name)
    alpha_words = re.findall(r"[A-Za-z0-9]+", decoded_name)
    clean_name = " ".join(alpha_words).strip()
    if clean_name and uname: return f"{clean_name.upper()} | @{uname}"
    if uname: return f"@{uname}"
    if clean_name: return clean_name.upper()
    return "MUSIC PLAYER"

def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> float:
    clean = " ".join(str(text or "").splitlines())
    try:
        if hasattr(draw, "textlength"): return float(draw.textlength(clean, font=font))
        if hasattr(draw, "textbbox"):
            bbox = draw.textbbox((0, 0), clean, font=font)
            return float(bbox[2] - bbox[0])
        return float(len(clean) * 14)
    except Exception: return float(len(clean) * 14)

def get_vibrant_color(img: Image.Image) -> tuple:
    try:
        small = img.copy().resize((28, 28), RESAMPLE_MODE).convert("RGB")
        pixels = list(small.getdata())
        best_color = (0, 215, 255)
        max_score = -1.0
        for r, g, b in pixels:
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            score = (s * 1.4) * v
            if 0.20 < v < 0.96 and s > 0.25 and score > max_score:
                max_score = score
                s = min(1.0, max(0.70, s * 1.25))
                v = min(1.0, max(0.90, v * 1.20))
                nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
                best_color = (int(nr * 255), int(ng * 255), int(nb * 255))
        return best_color
    except Exception: return (0, 215, 255)

def wrap_and_truncate(draw, text: str, font, max_width: int, max_lines: int = 2) -> list:
    clean_text = " ".join(str(text or "Unknown Track").split())
    words = clean_text.split()
    if not words: return ["Unknown Track"]
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if _text_width(draw, test_line, font) <= max_width:
            current_line = test_line
        else:
            if current_line: lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while _text_width(draw, last + "...", font) > max_width and len(last) > 0:
            last = last[:-1]
        lines[-1] = last.strip() + "..."
    return lines

def _load_base_image(thumb_path: Path) -> Image.Image:
    if thumb_path and thumb_path.exists() and thumb_path.stat().st_size > 800:
        try: return Image.open(thumb_path).convert("RGBA")
        except Exception: pass
    if os.path.exists(DEFAULT_THUMB):
        try: return Image.open(DEFAULT_THUMB).convert("RGBA")
        except Exception: pass
    return Image.new("RGBA", (CANVAS_W, CANVAS_H), (14, 16, 26, 255))

def draw_player_controls(draw: ImageDraw.ImageDraw, center_x: int, y: int, accent: tuple):
    r = 30
    draw.ellipse([center_x - r, y - r, center_x + r, y + r], fill=(*accent, 255))
    bar_w, bar_h, gap = 5, 18, 4
    draw.rounded_rectangle([center_x - gap - bar_w, y - bar_h // 2, center_x - gap, y + bar_h // 2], radius=2, fill=(12, 14, 20, 255))
    draw.rounded_rectangle([center_x + gap, y - bar_h // 2, center_x + gap + bar_w, y + bar_h // 2], radius=2, fill=(12, 14, 20, 255))
    nx, px = center_x + 76, center_x - 76
    draw.polygon([(nx, y - 11), (nx, y + 11), (nx + 16, y)], fill=(255, 255, 255, 235))
    draw.rounded_rectangle([nx + 16, y - 11, nx + 20, y + 11], radius=1, fill=(255, 255, 255, 235))
    draw.polygon([(px, y - 11), (px, y + 11), (px - 16, y)], fill=(255, 255, 255, 235))
    draw.rounded_rectangle([px - 20, y - 11, px - 16, y + 11], radius=1, fill=(255, 255, 255, 235))

def _render_sync(thumb_path: Path, out_path: str, title: str, duration: str, views: str, channel: str, requested_by: str, bot_display: str):
    base_img = _load_base_image(thumb_path)
    accent = get_vibrant_color(base_img)

    # 1. BLURRED CINEMATIC BACKGROUND
    bg = base_img.resize((CANVAS_W, CANVAS_H), RESAMPLE_MODE)
    bg = bg.filter(ImageFilter.GaussianBlur(55))
    bg = ImageEnhance.Brightness(bg).enhance(0.35)

    # 2. FROSTED GLASS MAIN CARD
    glass = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glass)
    card_box = [40, 40, CANVAS_W - 40, CANVAS_H - 40]
    g_draw.rounded_rectangle(card_box, radius=38, fill=(12, 14, 22, 180), outline=(255, 255, 255, 45), width=2)

    # 3. SQUARE 1:1 ARTWORK CROP (Perfect for Custom PFP & YT Thumbs)
    art_w, art_h = 460, 460
    art_x, art_y = 80, 130

    glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(glow_layer).rounded_rectangle([art_x - 14, art_y - 14, art_x + art_w + 14, art_y + art_h + 14], radius=44, fill=(*accent, 95))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(32))

    bg = Image.alpha_composite(bg, glass)
    bg = Image.alpha_composite(bg, glow_layer)

    # Smart Square Center Crop Logic
    w, h = base_img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    art = base_img.crop((left, top, left + min_dim, top + min_dim))
    art = art.resize((art_w, art_h), RESAMPLE_MODE)

    mask = Image.new("L", (art_w, art_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, art_w, art_h], radius=32, fill=255)
    art.putalpha(mask)
    bg.paste(art, (art_x, art_y), art)
    
    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle([art_x, art_y, art_x + art_w, art_y + art_h], radius=32, outline=(*accent, 220), width=3)

    # 4. FONTS
    try:
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 42)
        font_sub = ImageFont.truetype(FONT_BOLD_PATH, 25)
        font_meta = ImageFont.truetype(FONT_BOLD_PATH, 22)
        font_badge = ImageFont.truetype(FONT_BOLD_PATH, 20)
    except Exception:
        font_title = font_sub = font_meta = font_badge = ImageFont.load_default()

    # 5. RIGHT SIDE INFO PANEL
    text_x = art_x + art_w + 50
    max_text_w = (CANVAS_W - 60) - text_x

    # Header Bar
    header_y = 130
    draw.rounded_rectangle([text_x, header_y, text_x + 200, header_y + 40], radius=20, fill=(*accent, 40), outline=(*accent, 220), width=2)
    draw.ellipse([text_x + 15, header_y + 14, text_x + 27, header_y + 26], fill=(*accent, 255))
    draw.text((text_x + 36, header_y + 9), "NOW PLAYING", fill=(255, 255, 255, 245), font=font_badge)

    clean_bot_top = wrap_and_truncate(draw, bot_display, font_badge, 400, 1)[0]
    bot_w = int(_text_width(draw, clean_bot_top, font_badge)) + 40
    draw.rounded_rectangle([CANVAS_W - 60 - bot_w, header_y, CANVAS_W - 60, header_y + 40], radius=20, fill=(255, 255, 255, 20), outline=(*accent, 150), width=2)
    draw.text((CANVAS_W - 60 - bot_w + 20, header_y + 9), clean_bot_top, fill=(255, 255, 255, 250), font=font_badge)

    # Title
    title_y = header_y + 75
    for line in wrap_and_truncate(draw, _clean_text(title, "Unknown Track"), font_title, max_text_w, 2):
        draw.text((text_x + 2, title_y + 2), line, fill=(0, 0, 0, 190), font=font_title)
        draw.text((text_x, title_y), line, fill=(255, 255, 255, 255), font=font_title)
        title_y += 52

    # Channel & Played By
    chan_y = title_y + 15
    draw.text((text_x, chan_y), wrap_and_truncate(draw, f"Artist : {_clean_text(channel, 'Music')}", font_sub, max_text_w, 1)[0], fill=(*accent, 255), font=font_sub)
    draw.text((text_x, chan_y + 40), wrap_and_truncate(draw, f"Played By : {_clean_text(requested_by, 'Admin')}", font_meta, max_text_w, 1)[0], fill=(200, 200, 220, 255), font=font_meta)

    # Views & Duration Pills
    pill_y, pill_h, pill_w = chan_y + 100, 52, (max_text_w - 18) // 2
    draw.rounded_rectangle([text_x, pill_y, text_x + pill_w, pill_y + pill_h], radius=15, fill=(255, 255, 255, 18), outline=(255, 255, 255, 45), width=1)
    draw.text((text_x + 15, pill_y + 14), wrap_and_truncate(draw, f"Views : {_clean_text(views, 'YouTube')}", font_meta, pill_w - 26, 1)[0], fill=(235, 235, 245, 255), font=font_meta)

    dur_box_x = text_x + pill_w + 18
    draw.rounded_rectangle([dur_box_x, pill_y, dur_box_x + pill_w, pill_y + pill_h], radius=15, fill=(255, 255, 255, 18), outline=(255, 255, 255, 45), width=1)
    dur_str = _clean_text(duration, "LIVE")
    draw.text((dur_box_x + 15, pill_y + 14), wrap_and_truncate(draw, f"Duration : {dur_str if dur_str != 'None' else 'LIVE'}", font_meta, pill_w - 26, 1)[0], fill=(235, 235, 245, 255), font=font_meta)

    # Progress Bar
    bar_y, bar_w = pill_y + 95, max_text_w
    draw.rounded_rectangle([text_x, bar_y, text_x + bar_w, bar_y + 8], radius=4, fill=(255, 255, 255, 40))
    prog_w = int(bar_w * 0.38)
    draw.rounded_rectangle([text_x, bar_y, text_x + prog_w, bar_y + 8], radius=4, fill=(*accent, 255))
    draw.ellipse([text_x + prog_w - 5, bar_y - 1, text_x + prog_w + 5, bar_y + 9], fill=(*accent, 255))
    
    draw.text((text_x, bar_y + 16), "00:00", fill=(190, 190, 205, 255), font=font_badge)
    draw.text((text_x + bar_w - _text_width(draw, dur_str if dur_str != 'None' else 'LIVE', font_badge), bar_y + 16), dur_str if dur_str != 'None' else 'LIVE', fill=(190, 190, 205, 255), font=font_badge)

    draw_player_controls(draw, text_x + (bar_w // 2), bar_y + 80, accent)
    bg.convert("RGB").save(out_path, "PNG", optimize=True)
    return str(out_path)

def _extract_clean_vidid(raw_id: str) -> str:
    s = str(raw_id or "").strip()
    for prefix in ("vid_", "live_"):
        if s.startswith(prefix): s = s[len(prefix):]
    if "v=" in s: s = s.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in s: s = s.split("youtu.be/")[-1].split("?")[0]
    return s.strip() or "default"

def _get_cached_queue_info(videoid: str) -> tuple:
    try:
        if isinstance(db, dict):
            for _, queue_list in db.items():
                if isinstance(queue_list, list):
                    for item in queue_list:
                        if isinstance(item, dict) and _extract_clean_vidid(item.get("vidid", "")) == videoid:
                            return item.get("title"), item.get("dur"), item.get("by")
    except Exception: pass
    return None, None, None

async def gen_thumb(videoid: str) -> str:
    clean_id = _extract_clean_vidid(videoid)
    out_path = f"cache/{clean_id}_v8_square.png"
    if os.path.isfile(out_path): return out_path

    q_title, q_dur, q_user = _get_cached_queue_info(clean_id)
    title = q_title or ""
    duration = q_dur or ""
    requested_by = q_user or "Admin"
    views = "YouTube"
    channel = ""
    thumb_path = CACHE_DIR / f"raw_{clean_id}.jpg"

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={clean_id}", limit=2)
        res_data = await results.next()
        matched = (res_data or {}).get("result", [{}])[0]
        if matched:
            title = matched.get("title") or title
            duration = matched.get("duration") or duration
            view_data = matched.get("viewCount")
            if isinstance(view_data, dict): views = view_data.get("short") or views
            chan_data = matched.get("channel")
            if isinstance(chan_data, dict): channel = chan_data.get("name") or channel
    except Exception: pass

    title, duration, channel = title or "Music Stream", duration or "LIVE", channel or "YouTube"

    hd_urls = [
        f"https://i.ytimg.com/vi/{clean_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{clean_id}/hqdefault.jpg",
    ]

    try:
        async with aiohttp.ClientSession(headers=HTTP_HEADERS) as session:
            for url in hd_urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            if len(data) > 1000:
                                async with aiofiles.open(thumb_path, "wb") as f: await f.write(data)
                                break
                except Exception: continue
    except Exception: pass

    try:
        bot_display = _clean_bot_brand()
        final_img = await asyncio.to_thread(_render_sync, thumb_path, out_path, title, duration, views, channel, requested_by, bot_display)
        return final_img
    except Exception:
        return getattr(config, "STREAM_IMG_URL", DEFAULT_THUMB)
    finally:
        if thumb_path.exists():
            try: os.remove(thumb_path)
            except: pass
