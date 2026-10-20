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
from ShrutiMusic.misc import db

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"

# Safe resampling mode across all Pillow versions (Prevents AttributeError)
RESAMPLE_MODE = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> float:
    """Safely calculates text width across all Pillow versions."""
    clean = " ".join(str(text or "").splitlines())
    try:
        if hasattr(draw, "textlength"):
            return float(draw.textlength(clean, font=font))
        if hasattr(draw, "textbbox"):
            bbox = draw.textbbox((0, 0), clean, font=font)
            return float(bbox[2] - bbox[0])
        return float(len(clean) * 14)
    except Exception:
        return float(len(clean) * 14)


def get_vibrant_color(img: Image.Image) -> tuple:
    """Extracts a vibrant dominant color from the song thumbnail for neon accents."""
    try:
        small = img.copy().resize((24, 24), RESAMPLE_MODE).convert("RGB")
        pixels = list(small.getdata())

        best_color = (0, 210, 255)
        max_score = -1.0

        for r, g, b in pixels:
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            score = s * v
            if 0.20 < v < 0.95 and s > 0.30 and score > max_score:
                max_score = score
                s = min(1.0, max(0.70, s * 1.25))
                v = min(1.0, max(0.88, v * 1.20))
                nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
                best_color = (int(nr * 255), int(ng * 255), int(nb * 255))

        return best_color
    except Exception:
        return (0, 210, 255)


def wrap_and_truncate(draw, text: str, font, max_width: int, max_lines: int = 2) -> list:
    """Wraps text into clean lines and truncates with '...' if too long."""
    clean_text = " ".join(str(text or "Unknown Track").split())
    words = clean_text.split()
    if not words:
        return ["Unknown Track"]

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
    """Draws vector player controls (Prev, Play/Pause Circle, Next) & equalizer bars."""
    # Central Play/Pause Circle
    r = 30
    draw.ellipse([center_x - r, y - r, center_x + r, y + r], fill=(*accent, 255))

    bar_w, bar_h = 5, 18
    gap = 4
    draw.rounded_rectangle(
        [center_x - gap - bar_w, y - bar_h // 2, center_x - gap, y + bar_h // 2],
        radius=2, fill=(12, 12, 18, 255),
    )
    draw.rounded_rectangle(
        [center_x + gap, y - bar_h // 2, center_x + gap + bar_w, y + bar_h // 2],
        radius=2, fill=(12, 12, 18, 255),
    )

    # Next Icon
    nx = center_x + 75
    draw.polygon([(nx, y - 11), (nx, y + 11), (nx + 16, y)], fill=(255, 255, 255, 230))
    draw.rounded_rectangle([nx + 16, y - 11, nx + 20, y + 11], radius=1, fill=(255, 255, 255, 230))

    # Previous Icon
    px = center_x - 75
    draw.polygon([(px, y - 11), (px, y + 11), (px - 16, y)], fill=(255, 255, 255, 230))
    draw.rounded_rectangle([px - 20, y - 11, px - 16, y + 11], radius=1, fill=(255, 255, 255, 230))


def _load_base_image(thumb_path: Path) -> Image.Image:
    """Safely loads the downloaded song thumbnail or fallback image."""
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

    return Image.new("RGBA", (CANVAS_W, CANVAS_H), (18, 20, 32, 255))


def _render_sync(
    thumb_path: Path,
    out_path: str,
    title: str,
    duration: str,
    views: str,
    channel: str,
    bot_name: str,
):
    """Generates the HD Glassmorphic Thumbnail in a background thread."""
    base_img = _load_base_image(thumb_path)
    accent = get_vibrant_color(base_img)

    # 1. BLURRED CINEMATIC BACKGROUND
    bg = base_img.resize((CANVAS_W, CANVAS_H), RESAMPLE_MODE)
    bg = bg.filter(ImageFilter.GaussianBlur(50))
    bg = ImageEnhance.Brightness(bg).enhance(0.40)

    # 2. GLASSMORPHIC MAIN CARD
    glass = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glass)

    card_box = [40, 40, CANVAS_W - 40, CANVAS_H - 40]
    g_draw.rounded_rectangle(
        card_box,
        radius=38,
        fill=(14, 15, 22, 180),
        outline=(255, 255, 255, 50),
        width=2,
    )

    # 3. ARTWORK POSITION & NEON BACK-GLOW
    art_w, art_h = 460, 460
    art_x = 85
    art_y = 155

    glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.rounded_rectangle(
        [art_x - 12, art_y - 12, art_x + art_w + 12, art_y + art_h + 12],
        radius=42,
        fill=(*accent, 90),
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(30))

    bg = Image.alpha_composite(bg, glass)
    bg = Image.alpha_composite(bg, glow_layer)

    # 4. CROP & PASTE SONG THUMBNAIL (ARTWORK)
    # Remove black top/bottom bars from standard 4:3 YT thumbs before square crop
    w, h = base_img.size
    crop_h = int(h * 0.75) if h / w > 0.7 else h
    top_trim = (h - crop_h) // 2
    cropped_src = base_img.crop((0, top_trim, w, top_trim + crop_h))

    min_dim = min(cropped_src.width, cropped_src.height)
    left = (cropped_src.width - min_dim) // 2
    top = (cropped_src.height - min_dim) // 2
    art = cropped_src.crop((left, top, left + min_dim, top + min_dim))
    art = art.resize((art_w, art_h), RESAMPLE_MODE)

    mask = Image.new("L", (art_w, art_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, art_w, art_h], radius=32, fill=255)
    art.putalpha(mask)

    bg.paste(art, (art_x, art_y), art)
    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle(
        [art_x, art_y, art_x + art_w, art_y + art_h],
        radius=32,
        outline=(*accent, 180),
        width=3,
    )

    # 5. LOAD FONTS
    try:
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 42)
        font_sub = ImageFont.truetype(FONT_BOLD_PATH, 25)
        font_meta = ImageFont.truetype(FONT_REGULAR_PATH, 23)
        font_badge = ImageFont.truetype(FONT_BOLD_PATH, 20)
        font_time = ImageFont.truetype(FONT_BOLD_PATH, 21)
    except Exception:
        font_title = font_sub = font_meta = font_badge = font_time = ImageFont.load_default()

    # 6. TOP HEADER BAR (NOW PLAYING + BOT NAME)
    header_y = 75
    # Left Badge: NOW PLAYING
    draw.rounded_rectangle(
        [85, header_y, 305, header_y + 42],
        radius=21,
        fill=(*accent, 35),
        outline=(*accent, 210),
        width=2,
    )
    draw.ellipse([103, header_y + 15, 115, header_y + 27], fill=(*accent, 255))
    draw.text((126, header_y + 9), "NOW STREAMING", fill=(255, 255, 255, 245), font=font_badge)

    # Right Badge: BOT NAME
    bot_label = f"BOT :  {bot_name}"
    bot_w = int(_text_width(draw, bot_label, font_badge)) + 44
    bot_box_x1 = CANVAS_W - 85 - bot_w
    draw.rounded_rectangle(
        [bot_box_x1, header_y, CANVAS_W - 85, header_y + 42],
        radius=21,
        fill=(255, 255, 255, 22),
        outline=(255, 255, 255, 80),
        width=2,
    )
    draw.text((bot_box_x1 + 22, header_y + 9), bot_label, fill=(255, 255, 255, 240), font=font_badge)

    # 7. RIGHT SIDE DETAILS (SONG NAME, CHANNEL, VIEWS, DURATION)
    text_x = art_x + art_w + 50
    max_text_w = (CANVAS_W - 85) - text_x

    # Song Name (Title)
    title_lines = wrap_and_truncate(draw, title, font_title, max_text_w, max_lines=2)
    title_y = art_y + 5
    for line in title_lines:
        draw.text((text_x + 2, title_y + 2), line, fill=(0, 0, 0, 180), font=font_title)
        draw.text((text_x, title_y), line, fill=(255, 255, 255, 255), font=font_title)
        title_y += 52

    # Channel / Artist Name
    chan_y = art_y + 125
    clean_chan = wrap_and_truncate(draw, f"Channel :  {channel}", font_sub, max_text_w, max_lines=1)[0]
    draw.text((text_x, chan_y), clean_chan, fill=(*accent, 255), font=font_sub)

    # Info Pills (VIEWS & DURATION Boxes)
    pill_y = art_y + 180
    pill_h = 52
    pill_w = (max_text_w - 20) // 2

    # Views Box
    draw.rounded_rectangle(
        [text_x, pill_y, text_x + pill_w, pill_y + pill_h],
        radius=14,
        fill=(255, 255, 255, 18),
        outline=(255, 255, 255, 45),
        width=1,
    )
    views_str = wrap_and_truncate(draw, f"Views : {views}", font_meta, pill_w - 24, max_lines=1)[0]
    draw.text((text_x + 16, pill_y + 13), views_str, fill=(230, 230, 240, 255), font=font_meta)

    # Duration Box
    dur_box_x = text_x + pill_w + 20
    draw.rounded_rectangle(
        [dur_box_x, pill_y, dur_box_x + pill_w, pill_y + pill_h],
        radius=14,
        fill=(255, 255, 255, 18),
        outline=(255, 255, 255, 45),
        width=1,
    )
    dur_str = str(duration) if duration and str(duration) != "None" else "LIVE"
    dur_label = wrap_and_truncate(draw, f"Duration : {dur_str}", font_meta, pill_w - 24, max_lines=1)[0]
    draw.text((dur_box_x + 16, pill_y + 13), dur_label, fill=(230, 230, 240, 255), font=font_meta)

    # 8. PROGRESS BAR & TIMESTAMPS
    bar_y = art_y + 300
    bar_w = max_text_w

    draw.rounded_rectangle(
        [text_x, bar_y, text_x + bar_w, bar_y + 8],
        radius=4,
        fill=(255, 255, 255, 55),
    )

    prog_w = int(bar_w * 0.38)
    draw.rounded_rectangle(
        [text_x, bar_y, text_x + prog_w, bar_y + 8],
        radius=4,
        fill=(*accent, 255),
    )

    thumb_x = text_x + prog_w
    draw.ellipse([thumb_x - 10, bar_y - 6, thumb_x + 10, bar_y + 14], fill=(255, 255, 255, 255))
    draw.ellipse([thumb_x - 5, bar_y - 1, thumb_x + 5, bar_y + 9], fill=(*accent, 255))

    draw.text((text_x, bar_y + 16), "00:00", fill=(200, 200, 215, 255), font=font_time)
    end_w = _text_width(draw, dur_str, font_time)
    draw.text((text_x + bar_w - end_w, bar_y + 16), dur_str, fill=(200, 200, 215, 255), font=font_time)

    # 9. PLAYER CONTROLS
    controls_center_x = text_x + (bar_w // 2)
    draw_player_controls(draw, controls_center_x, art_y + 405, accent)

    bg.convert("RGB").save(out_path, "PNG", optimize=True)
    return str(out_path)


def _get_cached_queue_info(videoid: str) -> tuple:
    """Checks in-memory queue (db) for already-fetched song title and duration."""
    try:
        if isinstance(db, dict):
            for _, queue_list in db.items():
                if isinstance(queue_list, list):
                    for item in queue_list:
                        if isinstance(item, dict) and item.get("vidid") == videoid:
                            t = item.get("title")
                            d = item.get("dur")
                            return t, d
    except Exception:
        pass
    return None, None


async def gen_thumb(videoid: str) -> str:
    videoid = str(videoid or "default").strip()
    out_path = f"cache/{videoid}_pro_v5.png"
    if os.path.isfile(out_path):
        return out_path

    q_title, q_dur = _get_cached_queue_info(videoid)
    title = q_title or "YouTube Music Stream"
    duration = q_dur or "03:30"
    views = "1.2M+ Views"
    channel = "Official Artist"
    fallback_url = None
    thumb_path = CACHE_DIR / f"raw_{videoid}.jpg"

    # 1. Fetch exact Video Details via VideosSearch (matching videoid)
    try:
        search_url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(search_url, limit=3)
        res_data = await results.next()
        result_list = (res_data or {}).get("result") or []

        matched = None
        for item in result_list:
            if isinstance(item, dict) and item.get("id") == videoid:
                matched = item
                break
        if not matched and result_list and isinstance(result_list[0], dict):
            matched = result_list[0]

        if matched:
            title = matched.get("title") or title
            duration = matched.get("duration") or duration

            view_data = matched.get("viewCount")
            if isinstance(view_data, dict):
                views = view_data.get("short") or view_data.get("text") or views
            elif isinstance(view_data, str):
                views = view_data

            chan_data = matched.get("channel")
            if isinstance(chan_data, dict):
                channel = chan_data.get("name") or channel

            thumbs = matched.get("thumbnails")
            if isinstance(thumbs, list) and thumbs and isinstance(thumbs[-1], dict):
                raw_u = thumbs[-1].get("url")
                if raw_u:
                    fallback_url = raw_u.split("?")[0]
    except Exception as e:
        print(f"[gen_thumb Search Warning] {e}")

    # 2. Download Official Song Thumbnail + oEmbed backup if Title/Channel missing
    hd_urls = [
        f"https://i.ytimg.com/vi/{videoid}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{videoid}/sddefault.jpg",
        f"https://i.ytimg.com/vi/{videoid}/hqdefault.jpg",
    ]
    if fallback_url:
        hd_urls.append(fallback_url)

    try:
        async with aiohttp.ClientSession() as session:
            # Backup metadata check from YouTube oEmbed if title is still generic
            if title == "YouTube Music Stream" or channel == "Official Artist":
                try:
                    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={videoid}&format=json"
                    async with session.get(oembed_url, timeout=aiohttp.ClientTimeout(total=4)) as oresp:
                        if oresp.status == 200:
                            odata = await oresp.json()
                            if isinstance(odata, dict):
                                title = odata.get("title") or title
                                channel = odata.get("author_name") or channel
                except Exception:
                    pass

            # Download song poster
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

    # 3. Render Final Image
    try:
        bot_uname = getattr(app, "username", None)
        bot_name = f"@{bot_uname}" if bot_uname else (getattr(app, "name", None) or "MusicBot")

        final_img = await asyncio.to_thread(
            _render_sync,
            thumb_path,
            out_path,
            title,
            duration,
            views,
            channel,
            bot_name,
        )
        return final_img
    except Exception as e:
        print(f"[gen_thumb Render Error] {e}")
        traceback.print_exc()
        if os.path.exists(DEFAULT_THUMB):
            return DEFAULT_THUMB
        return getattr(config, "STREAM_IMG_URL", "https://files.catbox.moe/7q8bfg.jpg")
    finally:
        if thumb_path.exists():
            try:
                os.remove(thumb_path)
            except Exception:
                pass
