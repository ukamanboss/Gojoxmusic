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

import config
from ShrutiMusic import app

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"

# Compatible with both old and new Pillow versions (Prevents AttributeError)
RESAMPLE_MODE = getattr(Image, "Resampling", Image).LANCZOS


def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> float:
    """Safely calculates text width across all Pillow versions."""
    clean = " ".join(str(text).splitlines())
    if hasattr(draw, "textlength"):
        return draw.textlength(clean, font=font)
    bbox = draw.textbbox((0, 0), clean, font=font)
    return bbox[2] - bbox[0]


def get_vibrant_color(img: Image.Image) -> tuple:
    """Extracts a dominant vibrant color from the artwork for UI accents."""
    try:
        small = img.copy().resize((20, 20), RESAMPLE_MODE).convert("RGB")
        pixels = list(small.getdata())

        best_color = (88, 166, 255)
        max_score = -1

        for r, g, b in pixels:
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            score = s * v
            if 0.15 < v < 0.95 and s > 0.25 and score > max_score:
                max_score = score
                s = min(1.0, max(0.65, s * 1.2))
                v = min(1.0, max(0.85, v * 1.2))
                nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
                best_color = (int(nr * 255), int(ng * 255), int(nb * 255))

        return best_color
    except Exception:
        return (88, 166, 255)


def wrap_and_truncate(draw, text: str, font, max_width: int, max_lines: int = 2) -> list:
    """Wraps text into lines and safely truncates overflow."""
    clean_text = " ".join(str(text or "Unknown").split())
    words = clean_text.split()
    if not words:
        return ["Unknown"]

    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if _text_width(draw, test_line, font) <= max_width:
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
        while _text_width(draw, last + "...", font) > max_width and len(last) > 0:
            last = last[:-1]
        lines[-1] = last.strip() + "..."

    return lines


def draw_player_controls(draw: ImageDraw.ImageDraw, center_x: int, y: int, accent: tuple):
    """Draws vector media player controls (Prev, Play/Pause, Next)."""
    r = 32
    draw.ellipse([center_x - r, y - r, center_x + r, y + r], fill=(*accent, 255))

    bar_w, bar_h = 5, 20
    gap = 5
    draw.rounded_rectangle(
        [center_x - gap - bar_w, y - bar_h // 2, center_x - gap, y + bar_h // 2],
        radius=2, fill=(15, 15, 20, 255),
    )
    draw.rounded_rectangle(
        [center_x + gap, y - bar_h // 2, center_x + gap + bar_w, y + bar_h // 2],
        radius=2, fill=(15, 15, 20, 255),
    )

    nx = center_x + 85
    draw.polygon([(nx, y - 12), (nx, y + 12), (nx + 18, y)], fill=(255, 255, 255, 220))
    draw.rounded_rectangle([nx + 18, y - 12, nx + 22, y + 12], radius=1, fill=(255, 255, 255, 220))

    px = center_x - 85
    draw.polygon([(px, y - 12), (px, y + 12), (px - 18, y)], fill=(255, 255, 255, 220))
    draw.rounded_rectangle([px - 22, y - 12, px - 18, y + 12], radius=1, fill=(255, 255, 255, 220))


def _load_base_image(thumb_path: Path) -> Image.Image:
    """Loads downloaded thumbnail, falls back to default asset, or generates a dark canvas."""
    if thumb_path and thumb_path.exists() and thumb_path.stat().st_size > 500:
        try:
            return Image.open(thumb_path).convert("RGBA")
        except Exception:
            pass

    if os.path.exists(DEFAULT_THUMB):
        try:
            return Image.open(DEFAULT_THUMB).convert("RGBA")
        except Exception:
            pass

    # Ultimate fallback if default asset is missing
    return Image.new("RGBA", (CANVAS_W, CANVAS_H), (20, 22, 35, 255))


def _render_sync(thumb_path: Path, out_path: str, title: str, duration: str, views: str, channel: str, bot_username: str):
    """CPU-bound Pillow image generation isolated for thread execution."""
    base_img = _load_base_image(thumb_path)
    accent = get_vibrant_color(base_img)

    # 1. CINEMATIC BLURRED BACKGROUND
    bg = base_img.resize((CANVAS_W, CANVAS_H), RESAMPLE_MODE)
    bg = bg.filter(ImageFilter.GaussianBlur(55))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)

    # 2. FROSTED GLASSMORPHISM CARD
    glass = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glass)
    card_box = [45, 45, CANVAS_W - 45, CANVAS_H - 45]
    g_draw.rounded_rectangle(
        card_box, radius=42, fill=(18, 18, 24, 165), outline=(255, 255, 255, 45), width=2
    )

    art_size = 480
    art_x = 95
    art_y = (CANVAS_H - art_size) // 2

    glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.rounded_rectangle(
        [art_x - 15, art_y - 15, art_x + art_size + 15, art_y + art_size + 15],
        radius=50, fill=(*accent, 85),
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(35))

    bg = Image.alpha_composite(bg, glass)
    bg = Image.alpha_composite(bg, glow_layer)

    # 3. MAIN ARTWORK (SQUARE CROP + ROUNDED CORNERS)
    min_dim = min(base_img.width, base_img.height)
    left = (base_img.width - min_dim) // 2
    top = (base_img.height - min_dim) // 2
    art = base_img.crop((left, top, left + min_dim, top + min_dim))
    art = art.resize((art_size, art_size), RESAMPLE_MODE)

    mask = Image.new("L", (art_size, art_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, art_size, art_size], radius=36, fill=255)
    art.putalpha(mask)

    bg.paste(art, (art_x, art_y), art)
    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle(
        [art_x, art_y, art_x + art_size, art_y + art_size],
        radius=36, outline=(255, 255, 255, 60), width=2,
    )

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

    badge_w, badge_h = 200, 38
    badge_y = art_y + 10
    draw.rounded_rectangle(
        [text_x, badge_y, text_x + badge_w, badge_y + badge_h],
        radius=19, fill=(*accent, 35), outline=(*accent, 200), width=2,
    )
    draw.ellipse([text_x + 16, badge_y + 13, text_x + 28, badge_y + 25], fill=(*accent, 255))
    draw.text((text_x + 38, badge_y + 7), "NOW PLAYING", fill=(255, 255, 255, 240), font=font_badge)

    if bot_username:
        brand_txt = f"@{str(bot_username).lstrip('@')}"
        b_w = _text_width(draw, brand_txt, font_badge)
        draw.text((CANVAS_W - 90 - b_w, badge_y + 7), brand_txt, fill=(255, 255, 255, 130), font=font_badge)

    title_lines = wrap_and_truncate(draw, title, font_title, max_text_w, max_lines=2)
    title_y = badge_y + 62
    for line in title_lines:
        draw.text((text_x + 2, title_y + 2), line, fill=(0, 0, 0, 160), font=font_title)
        draw.text((text_x, title_y), line, fill=(255, 255, 255, 255), font=font_title)
        title_y += 56

    meta_y = art_y + 205
    clean_channel = wrap_and_truncate(draw, f"Artist :  {channel}", font_sub, max_text_w, max_lines=1)[0]
    draw.text((text_x, meta_y), clean_channel, fill=(210, 210, 220, 255), font=font_sub)
    draw.text((text_x, meta_y + 42), f"Views :  {views}", fill=(165, 165, 180, 255), font=font_sub)

    # 6. PROGRESS BAR
    bar_y = art_y + 325
    bar_w = max_text_w

    draw.rounded_rectangle([text_x, bar_y, text_x + bar_w, bar_y + 8], radius=4, fill=(255, 255, 255, 50))

    prog_w = int(bar_w * 0.35)
    draw.rounded_rectangle([text_x, bar_y, text_x + prog_w, bar_y + 8], radius=4, fill=(*accent, 255))

    thumb_x = text_x + prog_w
    draw.ellipse([thumb_x - 10, bar_y - 6, thumb_x + 10, bar_y + 14], fill=(255, 255, 255, 255))
    draw.ellipse([thumb_x - 5, bar_y - 1, thumb_x + 5, bar_y + 9], fill=(*accent, 255))

    draw.text((text_x, bar_y + 18), "0:00", fill=(190, 190, 205, 255), font=font_time)
    dur_str = str(duration) if duration else "LIVE"
    dur_w = _text_width(draw, dur_str, font_time)
    draw.text((text_x + bar_w - dur_w, bar_y + 18), dur_str, fill=(190, 190, 205, 255), font=font_time)

    # 7. VECTOR MEDIA CONTROLS
    controls_center_x = text_x + (bar_w // 2)
    draw_player_controls(draw, controls_center_x, art_y + 425, accent)

    bg.convert("RGB").save(out_path, "PNG", optimize=True)
    return str(out_path)


async def gen_thumb(videoid: str) -> str:
    videoid = str(videoid).strip()
    out_path = f"cache/{videoid}_ultra_v4.png"
    if os.path.isfile(out_path):
        return out_path

    title = "ShrutiMusic Audio"
    duration = "0:00"
    views = "N/A"
    channel = "YouTube Music"
    fallback_url = None
    thumb_path = CACHE_DIR / f"raw_{videoid}.jpg"

    # Step 1: Safely fetch metadata (Isolated so NoneType never blocks image download)
    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        res_data = await results.next()
        result_list = (res_data or {}).get("result")
        if result_list and isinstance(result_list, list):
            result = result_list[0] or {}
            title = result.get("title") or title
            duration = result.get("duration") or duration

            view_data = result.get("viewCount")
            if isinstance(view_data, dict):
                views = view_data.get("short") or views

            chan_data = result.get("channel")
            if isinstance(chan_data, dict):
                channel = chan_data.get("name") or channel

            thumbs = result.get("thumbnails")
            if isinstance(thumbs, list) and len(thumbs) > 0 and isinstance(thumbs[-1], dict):
                raw_u = thumbs[-1].get("url")
                if raw_u:
                    fallback_url = raw_u.split("?")[0]
    except Exception as e:
        print(f"[gen_thumb Metadata Warning] {e}")

    # Step 2: Independently download HD YouTube thumbnail directly by videoid
    hd_urls = [
        f"https://i.ytimg.com/vi/{videoid}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{videoid}/hqdefault.jpg",
    ]
    if fallback_url:
        hd_urls.append(fallback_url)

    try:
        async with aiohttp.ClientSession() as session:
            for url in hd_urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            if len(data) > 1000:
                                async with aiofiles.open(thumb_path, "wb") as f:
                                    await f.write(data)
                                break
                except Exception:
                    continue
    except Exception as e:
        print(f"[gen_thumb Download Warning] {e}")

    # Step 3: Render image in background thread; fallback to STREAM_IMG_URL if anything fails
    try:
        bot_uname = getattr(app, "username", None) or "ShrutiBots"
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
        if os.path.exists(DEFAULT_THUMB):
            return DEFAULT_THUMB
        return getattr(config, "STREAM_IMG_URL", "https://telegra.ph/file/05aa686cf52fc666184bf.jpg")
    finally:
        if thumb_path.exists():
            try:
                os.remove(thumb_path)
            except Exception:
                pass
