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
    """Converts text to clean readable ASCII so custom fonts never render boxes."""
    if not text:
        return default
    try:
        ascii_text = unidecode(str(text))
    except Exception:
        ascii_text = str(text)
    cleaned = re.sub(r"[^\x20-\x7E]", " ", ascii_text)
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else default


def _clean_bot_brand() -> str:
    """Extracts a clean bot name/username without broken symbol artifacts."""
    raw_name = getattr(app, "name", "") or ""
    uname = getattr(app, "username", "") or ""

    try:
        decoded_name = unidecode(str(raw_name))
    except Exception:
        decoded_name = str(raw_name)

    # Keep only alphanumeric words from fancy unicode bot names
    alpha_words = re.findall(r"[A-Za-z0-9]+", decoded_name)
    clean_name = " ".join(alpha_words).strip()

    if clean_name and uname:
        return f"{clean_name.upper()}  |  @{uname}"
    if uname:
        return f"@{uname}"
    if clean_name:
        return clean_name.upper()
    return "MUSIC PLAYER"


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
    """Extracts a vibrant dominant color from the song thumbnail for UI glow."""
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

    for idx in range(len(lines)):
        while _text_width(draw, lines[idx], font) > max_width and len(lines[idx]) > 3:
            lines[idx] = lines[idx][:-4].strip() + "..."

    return lines


def _create_fallback_artwork() -> Image.Image:
    """Generates a dark neon studio background if YouTube image is unreachable."""
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (14, 16, 26, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = CANVAS_W // 2, CANVAS_H // 2
    for r in range(300, 40, -35):
        alpha = max(30, 160 - r // 3)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 210, 255, alpha), width=3)
    draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=(0, 210, 255, 220))
    draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(14, 16, 26, 255))
    return img


def _load_base_image(thumb_path: Path) -> Image.Image:
    if thumb_path and thumb_path.exists() and thumb_path.stat().st_size > 800:
        try:
            return Image.open(thumb_path).convert("RGBA")
        except Exception:
            pass
    return _create_fallback_artwork()


def draw_player_controls(draw: ImageDraw.ImageDraw, center_x: int, y: int, accent: tuple):
    """Draws vector media controls and equalizer bars."""
    r = 30
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

    nx = center_x + 76
    draw.polygon([(nx, y - 11), (nx, y + 11), (nx + 16, y)], fill=(255, 255, 255, 235))
    draw.rounded_rectangle([nx + 16, y - 11, nx + 20, y + 11], radius=1, fill=(255, 255, 255, 235))

    px = center_x - 76
    draw.polygon([(px, y - 11), (px, y + 11), (px - 16, y)], fill=(255, 255, 255, 235))
    draw.rounded_rectangle([px - 20, y - 11, px - 16, y + 11], radius=1, fill=(255, 255, 255, 235))

    eq_heights = [10, 22, 14, 26, 16, 12]
    for idx, eh in enumerate(eq_heights):
        lx = center_x - 185 + (idx * 10)
        rx = center_x + 135 + (idx * 10)
        draw.rounded_rectangle([lx, y - eh // 2, lx + 4, y + eh // 2], radius=2, fill=(*accent, 175))
        draw.rounded_rectangle([rx, y - eh // 2, rx + 4, y + eh // 2], radius=2, fill=(*accent, 175))


def _render_sync(
    thumb_path: Path,
    out_path: str,
    title: str,
    duration: str,
    views: str,
    channel: str,
    requested_by: str,
    bot_display: str,
):
    base_img = _load_base_image(thumb_path)
    accent = get_vibrant_color(base_img)

    # 1. BLURRED CINEMATIC BACKGROUND
    bg = base_img.resize((CANVAS_W, CANVAS_H), RESAMPLE_MODE)
    bg = bg.filter(ImageFilter.GaussianBlur(48))
    bg = ImageEnhance.Brightness(bg).enhance(0.36)

    # 2. FROSTED GLASS MAIN CARD
    glass = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glass)

    card_box = [38, 38, CANVAS_W - 38, CANVAS_H - 38]
    g_draw.rounded_rectangle(
        card_box,
        radius=36,
        fill=(12, 14, 22, 190),
        outline=(255, 255, 255, 55),
        width=2,
    )

    # 3. FULL 16:9 WIDESCREEN SONG THUMBNAIL ON LEFT (NO CUTTING FACES/POSTER TEXT)
    art_w, art_h = 490, 285
    art_x = 78
    art_y = 152

    glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.rounded_rectangle(
        [art_x - 12, art_y - 12, art_x + art_w + 12, art_y + art_h + 12],
        radius=32,
        fill=(*accent, 95),
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(28))

    bg = Image.alpha_composite(bg, glass)
    bg = Image.alpha_composite(bg, glow_layer)

    # Trim black letterbox bars from 4:3 thumbnails (hqdefault/sddefault) to clean 16:9
    w, h = base_img.size
    if (h / float(max(w, 1))) > 0.68:
        new_h = int(w * 9 / 16)
        top_trim = max(0, (h - new_h) // 2)
        cropped_src = base_img.crop((0, top_trim, w, top_trim + new_h))
    else:
        cropped_src = base_img

    art = cropped_src.resize((art_w, art_h), RESAMPLE_MODE)

    mask = Image.new("L", (art_w, art_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, art_w, art_h], radius=26, fill=255)
    art.putalpha(mask)

    bg.paste(art, (art_x, art_y), art)
    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle(
        [art_x, art_y, art_x + art_w, art_y + art_h],
        radius=26,
        outline=(*accent, 210),
        width=3,
    )

    # 4. LOAD FONTS
    try:
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 40)
        font_sub = ImageFont.truetype(FONT_BOLD_PATH, 24)
        font_meta = ImageFont.truetype(FONT_BOLD_PATH, 21)
        font_badge = ImageFont.truetype(FONT_BOLD_PATH, 20)
        font_time = ImageFont.truetype(FONT_BOLD_PATH, 20)
    except Exception:
        font_title = font_sub = font_meta = font_badge = font_time = ImageFont.load_default()

    # 5. LEFT BOTTOM INFO CARD (BELOW SONG THUMBNAIL)
    info_card_y = art_y + art_h + 26
    info_card_h = 152
    draw.rounded_rectangle(
        [art_x, info_card_y, art_x + art_w, info_card_y + info_card_h],
        radius=22,
        fill=(255, 255, 255, 16),
        outline=(255, 255, 255, 45),
        width=1,
    )

    clean_req = _clean_text(requested_by, "Group Member")
    req_line = wrap_and_truncate(draw, f"Played By :  {clean_req}", font_meta, art_w - 40, max_lines=1)[0]
    draw.text((art_x + 22, info_card_y + 22), req_line, fill=(255, 255, 255, 240), font=font_meta)
    draw.text((art_x + 22, info_card_y + 62), "Audio :  High Quality Stream", fill=(*accent, 245), font=font_meta)
    draw.text((art_x + 22, info_card_y + 102), f"Bot :  {bot_display}", fill=(195, 195, 215, 240), font=font_meta)

    # 6. TOP HEADER BAR (NOW PLAYING + YOUR BOT NAME)
    header_y = 72
    draw.rounded_rectangle(
        [78, header_y, 298, header_y + 42],
        radius=21,
        fill=(*accent, 40),
        outline=(*accent, 220),
        width=2,
    )
    draw.ellipse([96, header_y + 15, 108, header_y + 27], fill=(*accent, 255))
    draw.text((120, header_y + 9), "NOW PLAYING", fill=(255, 255, 255, 250), font=font_badge)

    clean_bot_top = wrap_and_truncate(draw, bot_display, font_badge, 460, max_lines=1)[0]
    bot_w = int(_text_width(draw, clean_bot_top, font_badge)) + 44
    bot_box_x1 = CANVAS_W - 78 - bot_w
    draw.rounded_rectangle(
        [bot_box_x1, header_y, CANVAS_W - 78, header_y + 42],
        radius=21,
        fill=(255, 255, 255, 24),
        outline=(*accent, 170),
        width=2,
    )
    draw.text((bot_box_x1 + 22, header_y + 9), clean_bot_top, fill=(255, 255, 255, 250), font=font_badge)

    # 7. RIGHT SIDE DETAILS (SONG NAME, CHANNEL, VIEWS, DURATION)
    text_x = art_x + art_w + 42
    max_text_w = (CANVAS_W - 78) - text_x

    # Song Title (2 Lines Max)
    clean_song_title = _clean_text(title, "Unknown Track")
    title_lines = wrap_and_truncate(draw, clean_song_title, font_title, max_text_w, max_lines=2)
    title_y = art_y + 2
    for line in title_lines:
        draw.text((text_x + 2, title_y + 2), line, fill=(0, 0, 0, 190), font=font_title)
        draw.text((text_x, title_y), line, fill=(255, 255, 255, 255), font=font_title)
        title_y += 50

    # Channel / Artist Name
    chan_y = art_y + 120
    clean_artist = _clean_text(channel, "Official Channel")
    chan_line = wrap_and_truncate(draw, f"Channel :  {clean_artist}", font_sub, max_text_w, max_lines=1)[0]
    draw.text((text_x, chan_y), chan_line, fill=(*accent, 255), font=font_sub)

    # Info Pills (VIEWS & DURATION)
    pill_y = art_y + 178
    pill_h = 54
    pill_w = (max_text_w - 18) // 2

    # Views Box
    draw.rounded_rectangle(
        [text_x, pill_y, text_x + pill_w, pill_y + pill_h],
        radius=15,
        fill=(255, 255, 255, 20),
        outline=(255, 255, 255, 55),
        width=1,
    )
    clean_views = _clean_text(views, "YouTube")
    views_str = wrap_and_truncate(draw, f"Views : {clean_views}", font_meta, pill_w - 26, max_lines=1)[0]
    draw.text((text_x + 15, pill_y + 14), views_str, fill=(235, 235, 245, 255), font=font_meta)

    # Duration Box
    dur_box_x = text_x + pill_w + 18
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
    dur_label = wrap_and_truncate(draw, f"Duration : {dur_str}", font_meta, pill_w - 26, max_lines=1)[0]
    draw.text((dur_box_x + 15, pill_y + 14), dur_label, fill=(235, 235, 245, 255), font=font_meta)

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
    draw_player_controls(draw, controls_center_x, art_y + 408, accent)

    bg.convert("RGB").save(out_path, "PNG", optimize=True)
    return str(out_path)


def _extract_clean_vidid(raw_id: str) -> str:
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
    """Gets exact title, duration, and user who played the song from active db queue."""
    try:
        if isinstance(db, dict):
            for _, queue_list in db.items():
                if isinstance(queue_list, list):
                    for item in queue_list:
                        if isinstance(item, dict):
                            item_vid = _extract_clean_vidid(item.get("vidid", ""))
                            if item_vid == videoid:
                                return item.get("title"), item.get("dur"), item.get("by")
    except Exception:
        pass
    return None, None, None


async def gen_thumb(videoid: str) -> str:
    clean_id = _extract_clean_vidid(videoid)
    out_path = f"cache/{clean_id}_v7_pro.png"
    if os.path.isfile(out_path):
        return out_path

    q_title, q_dur, q_user = _get_cached_queue_info(clean_id)
    title = q_title or ""
    duration = q_dur or ""
    requested_by = q_user or "Admin"
    views = "YouTube"
    channel = ""
    oembed_thumb = None
    search_thumb = None
    thumb_path = CACHE_DIR / f"raw_{clean_id}.jpg"

    # 1. Fetch 100% Exact Song Title & Channel from Official YouTube oEmbed API
    try:
        async with aiohttp.ClientSession(headers=HTTP_HEADERS) as session:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={clean_id}&format=json"
            async with session.get(oembed_url, timeout=aiohttp.ClientTimeout(total=5)) as oresp:
                if oresp.status == 200:
                    odata = await oresp.json()
                    if isinstance(odata, dict):
                        if not title:
                            title = odata.get("title") or ""
                        channel = odata.get("author_name") or ""
                        oembed_thumb = odata.get("thumbnail_url")
    except Exception as e:
        print(f"[gen_thumb oEmbed Warning] {e}")

    # 2. Fetch Views & Duration from VideosSearch ONLY if video ID matches strictly
    try:
        results = VideosSearch(clean_id, limit=5)
        res_data = await results.next()
        result_list = (res_data or {}).get("result") or []

        matched = None
        for item in result_list:
            if isinstance(item, dict) and item.get("id") == clean_id:
                matched = item
                break

        if matched:
            if not title:
                title = matched.get("title") or ""
            if not duration:
                duration = matched.get("duration") or ""
            if not channel:
                chan_data = matched.get("channel")
                if isinstance(chan_data, dict):
                    channel = chan_data.get("name") or ""

            view_data = matched.get("viewCount")
            if isinstance(view_data, dict):
                views = view_data.get("short") or view_data.get("text") or views
            elif isinstance(view_data, str):
                views = view_data

            thumbs = matched.get("thumbnails")
            if isinstance(thumbs, list) and thumbs and isinstance(thumbs[-1], dict):
                raw_u = thumbs[-1].get("url")
                if raw_u:
                    search_thumb = raw_u.split("?")[0]
    except Exception as e:
        print(f"[gen_thumb Search Warning] {e}")

    if not title:
        title = "Music Stream"
    if not duration:
        duration = "LIVE"
    if not channel:
        channel = "YouTube Music"

    # 3. Download Actual Song Thumbnail from YouTube Servers
    hd_urls = [
        f"https://i.ytimg.com/vi/{clean_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{clean_id}/sddefault.jpg",
        f"https://i.ytimg.com/vi/{clean_id}/hqdefault.jpg",
        f"https://i.ytimg.com/vi/{clean_id}/mqdefault.jpg",
    ]
    for extra_u in (oembed_thumb, search_thumb):
        if extra_u and extra_u not in hd_urls:
            hd_urls.append(extra_u)

    try:
        async with aiohttp.ClientSession(headers=HTTP_HEADERS) as session:
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

    # 4. Render Final Thumbnail
    try:
        bot_display = _clean_bot_brand()
        final_img = await asyncio.to_thread(
            _render_sync,
            thumb_path,
            out_path,
            title,
            duration,
            views,
            channel,
            requested_by,
            bot_display,
        )
        return final_img
    except Exception as e:
        print(f"[gen_thumb Render Error] {e}")
        traceback.print_exc()
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
