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

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"

RESAMPLE_MODE = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _clean_text(text: str, default: str = "") -> str:
    """Converts fancy unicode fonts/emojis into clean readable ASCII text for PIL."""
    if not text:
        return default
    try:
        ascii_text = unidecode(str(text))
    except Exception:
        ascii_text = str(text)
    cleaned = re.sub(r"[^\x20-\x7E]", "", ascii_text)
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else default


def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> float:
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
    """Extracts a vibrant dominant neon color from the song thumbnail."""
    try:
        small = img.copy().resize((28, 28), RESAMPLE_MODE).convert("RGB")
        pixels = list(small.getdata())

        best_color = (0, 215, 255)
        max_score = -1.0

        for r, g, b in pixels:
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            score = (s * 1.4) * v
            if 0.22 < v < 0.96 and s > 0.28 and score > max_score:
                max_score = score
                s = min(1.0, max(0.72, s * 1.25))
                v = min(1.0, max(0.90, v * 1.20))
                nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
                best_color = (int(nr * 255), int(ng * 255), int(nb * 255))

        return best_color
    except Exception:
        return (0, 215, 255)


def wrap_and_truncate(draw, text: str, font, max_width: int, max_lines: int = 2) -> list:
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


def _create_fallback_artwork() -> Image.Image:
    """Generates a custom dark neon vinyl cover if YouTube thumbnail is unavailable (No Shruti Logo)."""
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (14, 16, 26, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = CANVAS_W // 2, CANVAS_H // 2
    for r in range(320, 40, -35):
        alpha = max(25, 160 - r // 3)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 210, 255, alpha), width=3)
    draw.ellipse([cx - 55, cy - 55, cx + 55, cy + 55], fill=(0, 210, 255, 220))
    draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(14, 16, 26, 255))
    return img


def _load_base_image(thumb_path: Path) -> Image.Image:
    if thumb_path and thumb_path.exists() and thumb_path.stat().st_size > 800:
        try:
            return Image.open(thumb_path).convert("RGBA")
        except Exception:
            pass
    return _create_fallback_artwork()


def draw_player_controls(draw: ImageDraw.ImageDraw, center_x: int, y: int, accent: tuple):
    """Draws vector media controls and subtle equalizer bars."""
    # Central Play/Pause Circle
    r = 31
    draw.ellipse([center_x - r, y - r, center_x + r, y + r], fill=(*accent, 255))

    bar_w, bar_h = 5, 18
    gap = 4
    draw.rounded_rectangle(
        [center_x - gap - bar_w, y - bar_h // 2, center_x - gap, y + bar_h // 2],
        radius=2,
        fill=(12, 14, 20, 255),
    )
    draw.rounded_rectangle(
        [center_x + gap, y - bar_h // 2, center_x + gap + bar_w, y + bar_h // 2],
        radius=2,
        fill=(12, 14, 20, 255),
    )

    # Next Button
    nx = center_x + 78
    draw.polygon([(nx, y - 11), (nx, y + 11), (nx + 16, y)], fill=(255, 255, 255, 235))
    draw.rounded_rectangle([nx + 16, y - 11, nx + 20, y + 11], radius=1, fill=(255, 255, 255, 235))

    # Previous Button
    px = center_x - 78
    draw.polygon([(px, y - 11), (px, y + 11), (px - 16, y)], fill=(255, 255, 255, 235))
    draw.rounded_rectangle([px - 20, y - 11, px - 16, y + 11], radius=1, fill=(255, 255, 255, 235))

    # Mini Equalizer Bars on Left & Right
    eq_heights = [10, 22, 14, 26, 16, 12]
    for idx, eh in enumerate(eq_heights):
        lx = center_x - 190 + (idx * 10)
        rx = center_x + 140 + (idx * 10)
        draw.rounded_rectangle([lx, y - eh // 2, lx + 4, y + eh // 2], radius=2, fill=(*accent, 170))
        draw.rounded_rectangle([rx, y - eh // 2, rx + 4, y + eh // 2], radius=2, fill=(*accent, 170))


def _render_sync(
    thumb_path: Path,
    out_path: str,
    title: str,
    duration: str,
    views: str,
    channel: str,
    bot_display: str,
):
    base_img = _load_base_image(thumb_path)
    accent = get_vibrant_color(base_img)

    # 1. BLURRED CINEMATIC BACKGROUND
    bg = base_img.resize((CANVAS_W, CANVAS_H), RESAMPLE_MODE)
    bg = bg.filter(ImageFilter.GaussianBlur(48))
    bg = ImageEnhance.Brightness(bg).enhance(0.38)

    # 2. FROSTED GLASS CARD
    glass = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glass)

    card_box = [38, 38, CANVAS_W - 38, CANVAS_H - 38]
    g_draw.rounded_rectangle(
        card_box,
        radius=38,
        fill=(12, 14, 22, 185),
        outline=(255, 255, 255, 55),
        width=2,
    )

    # 3. NEON BACK-GLOW BEHIND ARTWORK
    art_w, art_h = 460, 460
    art_x = 82
    art_y = 156

    glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.rounded_rectangle(
        [art_x - 14, art_y - 14, art_x + art_w + 14, art_y + art_h + 14],
        radius=44,
        fill=(*accent, 95),
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(32))

    bg = Image.alpha_composite(bg, glass)
    bg = Image.alpha_composite(bg, glow_layer)

    # 4. SMART CROP & PASTE SONG THUMBNAIL
    # Automatically trims black top/bottom letterbox bars from 4:3 YouTube thumbnails
    w, h = base_img.size
    crop_h = int(h * 0.74) if (h / float(max(w, 1))) > 0.70 else h
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
        outline=(*accent, 200),
        width=3,
    )

    # 5. LOAD FONTS
    try:
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 42)
        font_sub = ImageFont.truetype(FONT_BOLD_PATH, 25)
        font_meta = ImageFont.truetype(FONT_BOLD_PATH, 22)
        font_badge = ImageFont.truetype(FONT_BOLD_PATH, 20)
        font_time = ImageFont.truetype(FONT_BOLD_PATH, 21)
    except Exception:
        font_title = font_sub = font_meta = font_badge = font_time = ImageFont.load_default()

    # 6. TOP HEADER BAR (NOW PLAYING + YOUR BOT NAME)
    header_y = 74
    draw.rounded_rectangle(
        [82, header_y, 302, header_y + 42],
        radius=21,
        fill=(*accent, 38),
        outline=(*accent, 220),
        width=2,
    )
    draw.ellipse([100, header_y + 15, 112, header_y + 27], fill=(*accent, 255))
    draw.text((123, header_y + 9), "NOW PLAYING", fill=(255, 255, 255, 250), font=font_badge)

    # Dynamic User Bot Name Pill on Top-Right
    clean_bot = wrap_and_truncate(draw, bot_display, font_badge, 460, max_lines=1)[0]
    bot_w = int(_text_width(draw, clean_bot, font_badge)) + 44
    bot_box_x1 = CANVAS_W - 82 - bot_w
    draw.rounded_rectangle(
        [bot_box_x1, header_y, CANVAS_W - 82, header_y + 42],
        radius=21,
        fill=(255, 255, 255, 24),
        outline=(*accent, 160),
        width=2,
    )
    draw.text((bot_box_x1 + 22, header_y + 9), clean_bot, fill=(255, 255, 255, 245), font=font_badge)

    # 7. RIGHT SIDE DETAILS (SONG NAME, CHANNEL, VIEWS, DURATION)
    text_x = art_x + art_w + 48
    max_text_w = (CANVAS_W - 82) - text_x

    # Song Title (2 Lines Max)
    clean_song_title = _clean_text(title, "Unknown Track")
    title_lines = wrap_and_truncate(draw, clean_song_title, font_title, max_text_w, max_lines=2)
    title_y = art_y + 4
    for line in title_lines:
        draw.text((text_x + 2, title_y + 2), line, fill=(0, 0, 0, 190), font=font_title)
        draw.text((text_x, title_y), line, fill=(255, 255, 255, 255), font=font_title)
        title_y += 52

    # Channel / Artist Name
    chan_y = art_y + 124
    clean_artist = _clean_text(channel, "YouTube Music")
    chan_line = wrap_and_truncate(draw, f"Artist :  {clean_artist}", font_sub, max_text_w, max_lines=1)[0]
    draw.text((text_x, chan_y), chan_line, fill=(*accent, 255), font=font_sub)

    # Info Pills (VIEWS & DURATION)
    pill_y = art_y + 180
    pill_h = 54
    pill_w = (max_text_w - 20) // 2

    # Views Box
    draw.rounded_rectangle(
        [text_x, pill_y, text_x + pill_w, pill_y + pill_h],
        radius=15,
        fill=(255, 255, 255, 20),
        outline=(255, 255, 255, 55),
        width=1,
    )
    clean_views = _clean_text(views, "1M+ Views")
    views_str = wrap_and_truncate(draw, f"Views : {clean_views}", font_meta, pill_w - 28, max_lines=1)[0]
    draw.text((text_x + 16, pill_y + 14), views_str, fill=(235, 235, 245, 255), font=font_meta)

    # Duration Box
    dur_box_x = text_x + pill_w + 20
    draw.rounded_rectangle(
        [dur_box_x, pill_y, dur_box_x + pill_w, pill_y + pill_h],
        radius=15,
        fill=(255, 255, 255, 20),
        outline=(255, 255, 255, 55),
        width=1,
    )
    dur_str = _clean_text(duration, "LIVE")
    if not dur_str or dur_str.lower() == "none":
        dur_str = "LIVE"
    dur_label = wrap_and_truncate(draw, f"Duration : {dur_str}", font_meta, pill_w - 28, max_lines=1)[0]
    draw.text((dur_box_x + 16, pill_y + 14), dur_label, fill=(235, 235, 245, 255), font=font_meta)

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

    draw.text((text_x, bar_y + 16), "00:00", fill=(205, 205, 220, 255), font=font_time)
    end_w = _text_width(draw, dur_str, font_time)
    draw.text((text_x + bar_w - end_w, bar_y + 16), dur_str, fill=(205, 205, 220, 255), font=font_time)

    # 9. PLAYER CONTROLS
    controls_center_x = text_x + (bar_w // 2)
    draw_player_controls(draw, controls_center_x, art_y + 405, accent)

    bg.convert("RGB").save(out_path, "PNG", optimize=True)
    return str(out_path)


def _extract_clean_vidid(raw_id: str) -> str:
    """Extracts the exact 11-character YouTube video ID even if prefixes or URLs are passed."""
    s = str(raw_id or "").strip()
    for prefix in ("vid_", "live_"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    if "v=" in s:
        s = s.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in s:
        s = s.split("youtu.be/")[-1].split("?")[0]
    return s.strip() or "default"


def _get_cached_queue_info(videoid: str) -> tuple:
    """Fetches song title & duration directly from the active bot queue (db)."""
    try:
        if isinstance(db, dict):
            for _, queue_list in db.items():
                if isinstance(queue_list, list):
                    for item in queue_list:
                        if isinstance(item, dict):
                            item_vid = _extract_clean_vidid(item.get("vidid", ""))
                            if item_vid == videoid:
                                return item.get("title"), item.get("dur")
    except Exception:
        pass
    return None, None


def _get_bot_display_name() -> str:
    """Returns the user's actual Bot Name and @username without Shruti branding."""
    raw_name = _clean_text(getattr(app, "name", ""), "")
    uname = _clean_text(getattr(app, "username", ""), "")
    if raw_name and uname:
        return f"{raw_name.upper()}  |  @{uname}"
    if raw_name:
        return raw_name.upper()
    if uname:
        return f"@{uname}"
    return "MUSIC STREAM BOT"


async def gen_thumb(videoid: str) -> str:
    clean_id = _extract_clean_vidid(videoid)
    out_path = f"cache/{clean_id}_custom_v6.png"
    if os.path.isfile(out_path):
        return out_path

    q_title, q_dur = _get_cached_queue_info(clean_id)
    title = q_title or "Unknown Song"
    duration = q_dur or "LIVE"
    views = "1M+ Views"
    channel = "YouTube Music"
    fallback_url = None
    thumb_path = CACHE_DIR / f"raw_{clean_id}.jpg"

    # 1. Fetch Video Metadata via VideosSearch
    try:
        search_url = f"https://www.youtube.com/watch?v={clean_id}"
        results = VideosSearch(search_url, limit=3)
        res_data = await results.next()
        result_list = (res_data or {}).get("result") or []

        matched = None
        for item in result_list:
            if isinstance(item, dict) and item.get("id") == clean_id:
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

    # 2. Download Song Thumbnail with Browser User-Agent + oEmbed Title/Channel Fallback
    hd_urls = [
        f"https://i.ytimg.com/vi/{clean_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{clean_id}/sddefault.jpg",
        f"https://i.ytimg.com/vi/{clean_id}/hqdefault.jpg",
        f"https://i.ytimg.com/vi/{clean_id}/mqdefault.jpg",
    ]
    if fallback_url and fallback_url not in hd_urls:
        hd_urls.append(fallback_url)

    try:
        async with aiohttp.ClientSession(headers=HTTP_HEADERS) as session:
            # Backup check via official YouTube oEmbed API if title/channel wasn't found
            if title == "Unknown Song" or channel == "YouTube Music":
                try:
                    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={clean_id}&format=json"
                    async with session.get(oembed_url, timeout=aiohttp.ClientTimeout(total=5)) as oresp:
                        if oresp.status == 200:
                            odata = await oresp.json()
                            if isinstance(odata, dict):
                                if title == "Unknown Song":
                                    title = odata.get("title") or title
                                if channel == "YouTube Music":
                                    channel = odata.get("author_name") or channel
                except Exception:
                    pass

            # Try downloading the song's actual poster from highest to standard quality
            for url in hd_urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
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

    # 3. Render Final Custom Thumbnail
    try:
        bot_display = _get_bot_display_name()
        final_img = await asyncio.to_thread(
            _render_sync,
            thumb_path,
            out_path,
            title,
            duration,
            views,
            channel,
            bot_display,
        )
        return final_img
    except Exception as e:
        print(f"[gen_thumb Render Error] {e}")
        traceback.print_exc()
        # Even in an extreme error, generate a clean dark fallback file rather than ShrutiBots.jpg
        fallback_file = f"cache/fallback_{clean_id}.png"
        try:
            _create_fallback_artwork().convert("RGB").save(fallback_file, "PNG")
            return fallback_file
        except Exception:
            return out_path
    finally:
        if thumb_path.exists():
            try:
                os.remove(thumb_path)
            except Exception:
                pass
