import os
import math
import colorsys
import traceback
from pathlib import Path

import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from ShrutiMusic import app

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720
FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"

# Aapki custom PFP jo sab gano par show hogi
DEFAULT_THUMB_URL = "https://graph.org/file/8900e3ff2d522b0a72fde-85a16f08cdf35e4b93.jpg"
DEFAULT_THUMB_CACHE = CACHE_DIR / "custom_music_thumb.jpg"

# Fallback Resampling mode
RESAMPLE_MODE = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size=size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf" if "font3" in path else "DejaVuSans.ttf", size=size)
        except (OSError, IOError):
            return ImageFont.load_default()


def get_vibrant_color(img: Image.Image) -> tuple:
    """Extracts a vibrant dominant color directly from the image for UI themes."""
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


def cover_crop(image, size):
    """Scale and center-crop an image to fill a perfectly square/rectangular frame."""
    image = image.convert("RGB")
    target_w, target_h = size
    ratio = max(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (max(1, int(image.width * ratio)), max(1, int(image.height * ratio))),
        RESAMPLE_MODE,
    )
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h)).convert("RGBA")


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def format_duration(duration):
    duration = str(duration or "LIVE").strip()
    if duration.lower() == "none" or not duration:
        return "LIVE"
    return duration


def wrap_and_truncate(draw, text: str, font, max_width: int, max_lines: int = 2) -> list:
    """Wraps text cleanly and truncates with ... if it overflows."""
    clean_text = " ".join(str(text or "Unknown Track").split())
    words = clean_text.split()
    if not words: return ["Unknown Track"]

    def _text_width(draw_obj, txt, f):
        try:
            if hasattr(draw_obj, "textlength"): return float(draw_obj.textlength(txt, font=f))
            bbox = draw_obj.textbbox((0, 0), txt, font=f)
            return float(bbox[2] - bbox[0])
        except Exception: return float(len(txt) * 14)

    lines, current_line = [], ""
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


async def fetch_fixed_default_thumbnail():
    """Download/cache the user's chosen PFP once; use it for every song."""
    if DEFAULT_THUMB_CACHE.exists() and DEFAULT_THUMB_CACHE.stat().st_size > 0:
        return DEFAULT_THUMB_CACHE

    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(DEFAULT_THUMB_URL) as response:
                if response.status == 200:
                    content = await response.read()
                    if content:
                        async with aiofiles.open(DEFAULT_THUMB_CACHE, "wb") as file:
                            await file.write(content)
                        return DEFAULT_THUMB_CACHE
    except Exception as exc:
        print(f"[gen_thumb] Fixed default image download failed: {exc}")
    
    return Path(DEFAULT_THUMB) if Path(DEFAULT_THUMB).exists() else None


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


def build_thumbnail(base_img, videoid, title, duration, views, channel):
    """Render the ultra-premium 1280x720 thumbnail with Frosted Glass UI."""
    accent = get_vibrant_color(base_img)

    # 1. Cinematic Blurred Background
    bg = base_img.resize((CANVAS_W, CANVAS_H), RESAMPLE_MODE)
    bg = bg.filter(ImageFilter.GaussianBlur(55))
    bg = ImageEnhance.Brightness(bg).enhance(0.38)

    # 2. Frosted Glass Main Card
    glass = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glass)
    g_draw.rounded_rectangle([40, 40, CANVAS_W - 40, CANVAS_H - 40], radius=38, fill=(12, 14, 22, 185), outline=(255, 255, 255, 45), width=2)

    # 3. Square 1:1 PFP Artwork with Neon Glow
    art_size = 460
    art_x, art_y = 80, 130

    glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(glow_layer).rounded_rectangle([art_x - 14, art_y - 14, art_x + art_size + 14, art_y + art_size + 14], radius=44, fill=(*accent, 95))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(32))

    bg = Image.alpha_composite(bg, glass)
    bg = Image.alpha_composite(bg, glow_layer)

    art = cover_crop(base_img, (art_size, art_size))
    art.putalpha(rounded_mask((art_size, art_size), 32))
    bg.paste(art, (art_x, art_y), art)
    
    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle([art_x, art_y, art_x + art_size, art_y + art_size], radius=32, outline=(*accent, 220), width=3)

    # 4. Load Fonts
    font_title = load_font(FONT_BOLD_PATH, 42)
    font_sub = load_font(FONT_BOLD_PATH, 25)
    font_meta = load_font(FONT_BOLD_PATH, 22)
    font_badge = load_font(FONT_BOLD_PATH, 20)

    # 5. Top Header (Now Streaming & Bot Name)
    text_x = art_x + art_size + 50
    max_text_w = (CANVAS_W - 60) - text_x
    header_y = 130

    draw.rounded_rectangle([text_x, header_y, text_x + 215, header_y + 40], radius=20, fill=(*accent, 40), outline=(*accent, 220), width=2)
    draw.ellipse([text_x + 15, header_y + 14, text_x + 27, header_y + 26], fill=(*accent, 255))
    draw.text((text_x + 36, header_y + 9), "NOW STREAMING", fill=(255, 255, 255, 245), font=font_badge)

    brand = str(getattr(app, "username", None) or getattr(app, "name", "MUSIC PLAYER")).lstrip("@").upper()
    bot_w = int(draw.textbbox((0, 0), brand, font=font_badge)[2]) + 40
    draw.rounded_rectangle([CANVAS_W - 60 - bot_w, header_y, CANVAS_W - 60, header_y + 40], radius=20, fill=(255, 255, 255, 20), outline=(*accent, 150), width=2)
    draw.text((CANVAS_W - 60 - bot_w + 20, header_y + 9), brand, fill=(255, 255, 255, 250), font=font_badge)

    # 6. Song Title & Channel
    title_lines = wrap_and_truncate(draw, str(title or "Unknown Track"), font_title, max_text_w, max_lines=2)
    title_y = header_y + 75
    for line in title_lines:
        draw.text((text_x + 2, title_y + 2), line, fill=(0, 0, 0, 190), font=font_title)
        draw.text((text_x, title_y), line, fill=(255, 255, 255, 255), font=font_title)
        title_y += 52

    chan_y = title_y + 15
    chan_line = wrap_and_truncate(draw, f"Artist : {str(channel or 'Unknown')}", font_sub, max_text_w, 1)[0]
    draw.text((text_x, chan_y), chan_line, fill=(*accent, 255), font=font_sub)

    # 7. Views & Duration Pills
    pill_y, pill_h, pill_w = chan_y + 80, 52, (max_text_w - 18) // 2
    draw.rounded_rectangle([text_x, pill_y, text_x + pill_w, pill_y + pill_h], radius=15, fill=(255, 255, 255, 18), outline=(255, 255, 255, 45), width=1)
    draw.text((text_x + 15, pill_y + 14), wrap_and_truncate(draw, f"Views : {str(views or 'YouTube')}", font_meta, pill_w - 26, 1)[0], fill=(235, 235, 245, 255), font=font_meta)

    dur_box_x = text_x + pill_w + 18
    draw.rounded_rectangle([dur_box_x, pill_y, dur_box_x + pill_w, pill_y + pill_h], radius=15, fill=(255, 255, 255, 18), outline=(255, 255, 255, 45), width=1)
    dur_str = format_duration(duration)
    draw.text((dur_box_x + 15, pill_y + 14), wrap_and_truncate(draw, f"Duration : {dur_str}", font_meta, pill_w - 26, 1)[0], fill=(235, 235, 245, 255), font=font_meta)

    # 8. Premium Progress Bar & Vector Controls
    bar_y, bar_w = pill_y + 90, max_text_w
    draw.rounded_rectangle([text_x, bar_y, text_x + bar_w, bar_y + 8], radius=4, fill=(255, 255, 255, 40))
    prog_w = int(bar_w * 0.35)
    draw.rounded_rectangle([text_x, bar_y, text_x + prog_w, bar_y + 8], radius=4, fill=(*accent, 255))
    draw.ellipse([text_x + prog_w - 5, bar_y - 1, text_x + prog_w + 5, bar_y + 9], fill=(*accent, 255))
    
    draw.text((text_x, bar_y + 16), "00:00", fill=(190, 190, 205, 255), font=font_badge)
    dur_w = draw.textbbox((0,0), dur_str, font=font_badge)[2]
    draw.text((text_x + bar_w - dur_w, bar_y + 16), dur_str, fill=(190, 190, 205, 255), font=font_badge)

    draw_player_controls(draw, text_x + (bar_w // 2), bar_y + 80, accent)

    output = CACHE_DIR / f"{videoid}_premium.png"
    bg.convert("RGB").save(output, format="PNG", optimize=True)
    return str(output)


async def gen_thumb(videoid: str):
    """Fetches song metadata and routes to the premium builder."""
    videoid = str(videoid or "").strip()
    if not videoid: return None

    title, duration, views, channel = "Music Stream", "LIVE", "1M+ Views", "Official Channel"

    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        search = VideosSearch(url, limit=1)
        response = await search.next()
        results = (response or {}).get("result") or []
        if results:
            result = results[0]
            title = result.get("title") or title
            duration = result.get("duration") or duration
            views = (result.get("viewCount") or {}).get("short") or views
            channel = (result.get("channel") or {}).get("name") or channel
    except Exception:
        pass

    try:
        # Load your fixed custom PFP for EVERY song
        thumb_path = await fetch_fixed_default_thumbnail()
        if thumb_path and Path(thumb_path).exists():
            with Image.open(thumb_path) as source:
                base_img = source.convert("RGBA")
        else:
            raise FileNotFoundError("PFP not found")
    except Exception:
        # Emergency ultimate fallback to blank canvas
        base_img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (20, 22, 35, 255))

    try:
        output_path = build_thumbnail(base_img, videoid, title, duration, views, channel)
        return output_path
    except Exception as exc:
        print(f"[gen_thumb] Rendering failed: {exc}")
        traceback.print_exc()
        return None
