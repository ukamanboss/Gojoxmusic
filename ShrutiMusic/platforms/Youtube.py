# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# All rights reserved.

import asyncio
import os
import re
import random
from datetime import datetime, timedelta
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch, Playlist
import aiohttp

API_URL = os.environ.get("SHRUTI_API_URL", "https://api.shrutibots.in")
API_KEY = os.environ.get("SHRUTI_API_KEY", "YOUR_API_KEY") 
DOWNLOAD_DIR = "downloads"

def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))

async def download_song(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3: return None
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0: return file_path
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/download", params={"url": video_id, "type": "audio", "api_key": API_KEY}, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                if resp.status != 200: return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072): f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0: return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
        return None

async def download_video(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3: return None
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0: return file_path
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/download", params={"url": video_id, "type": "video", "api_key": API_KEY}, timeout=aiohttp.ClientTimeout(total=600)) as resp:
                if resp.status != 200: return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072): f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0: return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
        return None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def get_autoplay(self, videoid: str, history: list):
        """Advanced AI Vibe Matcher: Mood, Anti-Trash, Time-Aware, and Artist Lock."""
        try:
            results = VideosSearch(videoid, limit=1)
            res_data = await results.next()
            current_title = res_data["result"][0]["title"].lower()
            
            # 1. MOOD & VIBE DETECTION
            vibe_addon = ""
            if "slowed" in current_title or "reverb" in current_title: vibe_addon = "slowed reverb"
            elif "lofi" in current_title: vibe_addon = "lofi"
            elif "sad" in current_title: vibe_addon = "sad"
            elif "mashup" in current_title: vibe_addon = "mashup"

            # 2. PUNJABI ARTIST LOCKING
            punjabi_artists = ["karan aujla", "shubh", "sidhu moose wala", "ap dhillon", "diljit"]
            is_punjabi = any(artist in current_title for artist in punjabi_artists)

            # 3. TIME-BASED CLOCK AI (IST Time)
            ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            if ist_now.hour >= 23 or ist_now.hour <= 4:
                # Sirf tab chill lagayega jab user ne specifically hard punjabi party song na chalaya ho
                if not vibe_addon and not is_punjabi: 
                    vibe_addon = "chill night vibes"

            # 4. TITLE CLEANING
            clean_title = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}|official|video|lyrical|audio|remix|4k', '', current_title, flags=re.IGNORECASE).strip()
            keywords = " ".join(clean_title.split()[:3])
            
            search_query = f"{keywords} {vibe_addon} hits".strip()
            if is_punjabi and "punjabi" not in search_query:
                search_query += " punjabi"

            rel_search = VideosSearch(search_query, limit=15)
            rel_data = await rel_search.next()
            
            # 5. ANTI-TRASH FILTER
            trash_keywords = ["8d", "cover", "karaoke", "instrumental", "live performance", "reaction"]

            for item in rel_data.get("result", []):
                vid = item["id"]
                item_title = item["title"].lower()

                if vid not in history and vid != videoid:
                    # Agar original gaana cover ya 8D nahi tha, toh auto-play mein bhi aisi cheezein reject karo
                    is_trash = any(trash in item_title for trash in trash_keywords)
                    if is_trash and not any(trash in current_title for trash in trash_keywords):
                        continue

                    dur_str = item.get("duration", "0:00")
                    sec = int(time_to_seconds(dur_str))
                    # Quality Control: Sirf 2 se 7 minute ke proper gaane
                    if 120 <= sec <= 420:
                        return vid, item["title"], dur_str
            return None, None, None
        except Exception:
            return None, None, None

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message: messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK: return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]: return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]: return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]: return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file: return 1, downloaded_file
            return 0, "Video download failed"
        except Exception as e: return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid: link = self.listbase + link
        if "&" in link: link = link.split("&")[0]
        try: plist = await Playlist.get(link)
        except Exception: return []
        videos = plist.get("videos") or []
        ids = []
        for data in videos[:limit]:
            if not data: continue
            vid = data.get("id")
            if not vid: continue
            ids.append(vid)
        return ids

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return {"title": title, "link": yturl, "vidid": vidid, "duration_min": duration_min, "thumb": thumbnail}, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        ydl = yt_dlp.YoutubeDL({"quiet": True})
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append({
                            "format": format["format"],
                            "filesize": format.get("filesize"),
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        })
                except Exception: continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        return result[query_type]["title"], result[query_type]["duration"], result[query_type]["thumbnails"][0]["url"].split("?")[0], result[query_type]["id"]

    async def download(self, link: str, mystic, video: Union[bool, str] = None, videoid: Union[bool, str] = None, songaudio: Union[bool, str] = None, songvideo: Union[bool, str] = None, format_id: Union[bool, str] = None, title: Union[bool, str] = None) -> str:
        if videoid: link = self.base + link
        try:
            downloaded_file = await download_video(link) if video else await download_song(link)
            if downloaded_file: return downloaded_file, True
            return None, False
        except Exception: return None, False

YouTube = YouTubeAPI()
