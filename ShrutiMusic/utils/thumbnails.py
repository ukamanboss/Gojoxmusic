# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Original project attribution retained. Modify/use according to the original license
# and permission terms supplied with the source.
#
# Improved thumbnail generator:
# - Fixes the SyntaxError caused by a malformed return/if line.
# - Keeps the public async gen_thumb(videoid) interface.
# - Uses a clean, readable music-player thumbnail layout.
# - Adds safer metadata/font/image fallbacks and robust download handling.

import os
import math
import random
import traceback
from pathlib import Path

import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from ShrutiMusic import app

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CANVAS_W, CANVAS_H = 1320, 760
FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"
DEFAULT_THUMB_URL = "https://graph.org/file/8900e3ff2d522b0a72fde-85a16f08cdf35e4b93.jpg"
DEFAULT_THUMB_CACHE = CACHE_DIR / "default_music_thumb.jpg"

# Muted premium palettes; one palette is chosen per generated thumbnail.
PALETTES = [
    ((10, 15, 28), (31, 44, 72), (96, 165, 250)),
    ((15, 12, 24), (55, 35, 76), (192, 132, 252)),
    ((8, 20, 24), (24, 64, 66), (94, 234, 212)),
    ((22, 14, 18), (74, 35, 47), (251, 146, 60)),
    ((12, 15, 20), (42, 48, 62), (226, 232, 240)),
]


def load_font(path, size):
    """Load a project font, falling back safely if it is missing."""
    try:
        return ImageFont.truetype(path, size=size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf" if "font3" in path else "DejaVuSans.ttf", size=size)
        except (OSError, IOError):
            return ImageFont.load_default()


def fit_text(draw, text, font_path, start_size, max_width, min_size=20):
    """Return a font sized so a single line fits max_width."""
    size = start_size
    while size > min_size:
        font = load_font(font_path, size)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
        size -= 2
    return load_font(font_path, min_size)


def wrap_text(draw, text, font, max_width, max_lines=2):
    """Wrap text without allowing it to overflow the information panel."""
    words = str(text or "").split()
    if not words:
        return ["Unknown title"]

    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
        current = word

        if len(lines) >= max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    # If text remains after the final allowed line, add an ellipsis.
    consumed = " ".join(lines).split()
    if len(consumed) < len(words) and lines:
        last = lines[-1]
        while last and draw.textbbox((0, 0), last + "…", font=font)[2] > max_width:
            last = last[:-1].rstrip()
        lines[-1] = (last + "…") if last else "…"

    return lines[:max_lines]


def make_gradient(size, top, bottom):
    """Create a vertical RGB gradient."""
    width, height = size
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line((0, y, width, y), fill=color)
    return image.convert("RGBA")


def cover_crop(image, size):
    """Scale and center-crop an image to fill a square."""
    image = image.convert("RGB")
    target_w, target_h = size
    ratio = max(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (max(1, int(image.width * ratio)), max(1, int(image.height * ratio))),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h)).convert("RGBA")


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255
    )
    return mask


def format_duration(duration):
    duration = str(duration or "Unknown")
    parts = duration.split(":")
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        return f"{int(parts[0])}:{parts[1].zfill(2)}"
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return f"{int(parts[0])}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
    return duration


async def fetch_thumbnail(url, videoid):
    """Download thumbnail and return its cache path, or None."""
    if not url:
        return None

    path = CACHE_DIR / f"thumb_{videoid}.jpg"
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                content = await response.read()
                if not content:
                    return None
                async with aiofiles.open(path, "wb") as file:
                    await file.write(content)
        return path
    except Exception as exc:
        print(f"[gen_thumb] Thumbnail download failed: {exc}")
        return None



async def fetch_fixed_default_thumbnail():
    """Download/cache the user's chosen artwork; use it for every song."""
    if DEFAULT_THUMB_CACHE.exists() and DEFAULT_THUMB_CACHE.stat().st_size > 0:
        return DEFAULT_THUMB_CACHE

    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(DEFAULT_THUMB_URL) as response:
                if response.status != 200:
                    raise RuntimeError(f"Default image returned HTTP {response.status}")
                content = await response.read()
                if not content:
                    raise RuntimeError("Default image response was empty")
                async with aiofiles.open(DEFAULT_THUMB_CACHE, "wb") as file:
                    await file.write(content)
        # Validate the downloaded file before relying on it.
        with Image.open(DEFAULT_THUMB_CACHE) as image:
            image.verify()
        return DEFAULT_THUMB_CACHE
    except Exception as exc:
        print(f"[gen_thumb] Fixed default image download failed: {exc}")
        try:
            if DEFAULT_THUMB_CACHE.exists():
                DEFAULT_THUMB_CACHE.unlink()
        except OSError:
            pass
        return Path(DEFAULT_THUMB) if Path(DEFAULT_THUMB).exists() else None


def draw_pill(draw, xy, text, fill, font):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=(y2 - y1) // 2, fill=fill)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_h = bbox[3] - bbox[1]
    draw.text(
        (x1 + 18, y1 + ((y2 - y1) - text_h) // 2 - bbox[1]),
        text,
        font=font,
        fill=(255, 255, 255, 255),
    )


def build_thumbnail(base_img, videoid, title, duration, views, channel):
    """Render the final premium-style 1320x760 thumbnail."""
    bg_top, bg_bottom, accent = random.choice(PALETTES)
    canvas = make_gradient((CANVAS_W, CANVAS_H), bg_top, bg_bottom)

    # Use the cover as a subtle blurred background to add depth.
    try:
        backdrop = cover_crop(base_img, (CANVAS_W, CANVAS_H)).filter(
            ImageFilter.GaussianBlur(34)
        )
        backdrop = ImageEnhance.Brightness(backdrop).enhance(0.24)
        shade = Image.new("RGBA", canvas.size, (*bg_top, 150))
        canvas = Image.alpha_composite(backdrop, shade)
        canvas = Image.alpha_composite(canvas, make_gradient(
            (CANVAS_W, CANVAS_H), (*bg_top, 205), (*bg_bottom, 175)
        ))
    except Exception:
        pass

    draw = ImageDraw.Draw(canvas, "RGBA")

    # Gentle accent blobs and a restrained border.
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((70, 80, 620, 630), fill=(*accent, 45))
    gd.ellipse((900, 200, 1450, 750), fill=(*accent, 25))
    glow = glow.filter(ImageFilter.GaussianBlur(75))
    canvas = Image.alpha_composite(canvas, glow)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle(
        (20, 20, CANVAS_W - 21, CANVAS_H - 21),
        radius=30, outline=(*accent, 105), width=2
    )

    # Artwork panel with a shadow and a rounded cover image.
    art_size = 510
    art_x, art_y = 70, (CANVAS_H - art_size) // 2 + 15
    shadow = Image.new("RGBA", (art_size + 50, art_size + 50), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (20, 20, art_size + 20, art_size + 20),
        radius=34, fill=(0, 0, 0, 175)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(shadow, (art_x - 25, art_y - 25))

    art = cover_crop(base_img, (art_size, art_size))
    art.putalpha(rounded_mask((art_size, art_size), 30))
    canvas.alpha_composite(art, (art_x, art_y))

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle(
        (art_x, art_y, art_x + art_size, art_y + art_size),
        radius=30, outline=(*accent, 220), width=4
    )

    # Text panel.
    panel_x = 650
    panel_right = CANVAS_W - 70
    max_width = panel_right - panel_x

    brand = str(getattr(app, "username", None) or "ShrutiMusic").lstrip("@")
    brand_font = fit_text(draw, brand, FONT_BOLD_PATH, 38, max_width, 24)
    draw.text((panel_x + 2, 48 + 3), brand, font=brand_font, fill=(0, 0, 0, 170))
    draw.text((panel_x, 48), brand, font=brand_font, fill=(255, 255, 255, 245))
    brand_bbox = draw.textbbox((panel_x, 48), brand, font=brand_font)
    underline_y = brand_bbox[3] + 12
    draw.rounded_rectangle(
        (panel_x, underline_y, panel_x + 95, underline_y + 5),
        radius=3, fill=(*accent, 255)
    )

    pill_font = load_font(FONT_BOLD_PATH, 23)
    draw_pill(
        draw, (panel_x, 145, panel_x + 245, 195),
        "♫  NOW PLAYING", (*accent, 220), pill_font
    )

    title = str(title or "Unknown title").strip()
    title_font = load_font(FONT_BOLD_PATH, 49)
    title_lines = wrap_text(draw, title, title_font, max_width, max_lines=3)
    title_y = 225
    line_gap = 13
    for line in title_lines:
        # Reduce the font if a single unbroken word is too long.
        line_font = fit_text(draw, line, FONT_BOLD_PATH, 49, max_width, 27)
        draw.text((panel_x + 2, title_y + 3), line, font=line_font, fill=(0, 0, 0, 175))
        draw.text((panel_x, title_y), line, font=line_font, fill=(255, 255, 255, 255))
        bbox = draw.textbbox((panel_x, title_y), line, font=line_font)
        title_y = bbox[3] + line_gap

    # Metadata divider and three compact rows.
    divider_y = min(max(title_y + 14, 425), 500)
    draw.line(
        (panel_x, divider_y, panel_right, divider_y),
        fill=(255, 255, 255, 65), width=2
    )

    duration = format_duration(duration)
    metadata = [
        ("VIEWS", str(views or "Unknown")),
        ("DURATION", duration),
        ("CHANNEL", str(channel or "Unknown channel")),
    ]
    label_font = load_font(FONT_BOLD_PATH, 17)
    value_font = load_font(FONT_REGULAR_PATH, 24)
    row_y = divider_y + 22
    row_gap = 61

    for label, value in metadata:
        # Avoid a long channel name running beyond the right edge.
        value_font_fit = fit_text(draw, value, FONT_REGULAR_PATH, 24, max_width, 17)
        draw.text((panel_x, row_y), label, font=label_font, fill=(*accent, 255))
        value_y = row_y + 22
        draw.text((panel_x + 1, value_y + 1), value, font=value_font_fit, fill=(0, 0, 0, 140))
        draw.text((panel_x, value_y), value, font=value_font_fit, fill=(232, 237, 245, 255))
        row_y += row_gap

    # Small decorative equalizer at bottom right.
    eq_x = panel_right - 100
    eq_base = CANVAS_H - 58
    for i, height in enumerate((18, 34, 24, 46, 28, 38, 16)):
        x = eq_x + i * 13
        draw.rounded_rectangle(
            (x, eq_base - height, x + 7, eq_base),
            radius=3, fill=(*accent, 200 if i in (1, 3, 5) else 100)
        )

    output = CACHE_DIR / f"{videoid}_final.png"
    canvas.convert("RGB").save(output, format="PNG", optimize=True)
    return str(output)


async def gen_thumb(videoid: str):
    """
    Generate a music thumbnail and return its local path.
    This keeps the original function signature expected by the bot.
    """
    videoid = str(videoid or "").strip()
    if not videoid:
        print("[gen_thumb] Empty video ID")
        return None

    thumb_path = None
    base_img = None
    title = "Unknown title"
    duration = "Unknown"
    views = "Unknown"
    channel = "Unknown channel"

    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        search = VideosSearch(url, limit=1)
        response = await search.next()
        results = (response or {}).get("result") or []
        if not results:
            raise ValueError("No YouTube search result returned")

        result = results[0]
        title = result.get("title") or title
        duration = result.get("duration") or duration
        views = (result.get("viewCount") or {}).get("short") or views
        channel = (result.get("channel") or {}).get("name") or channel

        # Always use the same artwork URL supplied by the user for every song.
        # YouTube thumbnails are intentionally ignored.
        thumb_path = await fetch_fixed_default_thumbnail()
        if thumb_path and Path(thumb_path).exists():
            with Image.open(thumb_path) as source:
                base_img = source.convert("RGBA")
        else:
            raise FileNotFoundError(
                "Could not load the configured default thumbnail image."
            )

    except Exception as exc:
        print(f"[gen_thumb] YouTube metadata/image fallback: {exc}")
        if base_img is None and Path(DEFAULT_THUMB).exists():
            try:
                with Image.open(DEFAULT_THUMB) as source:
                    base_img = source.convert("RGBA")
            except Exception:
                traceback.print_exc()

        if base_img is None:
            print("[gen_thumb] No usable thumbnail image; returning None")
            return None

    try:
        output_path = build_thumbnail(
            base_img=base_img,
            videoid=videoid,
            title=title,
            duration=duration,
            views=views,
            channel=channel,
        )
        return output_path
    except Exception as exc:
        print(f"[gen_thumb] Rendering failed: {exc}")
        traceback.print_exc()
        return None
    finally:
        # Keep the fixed default image cached so every song uses it without
        # downloading it again. Do not remove DEFAULT_THUMB_CACHE here.
        pass
