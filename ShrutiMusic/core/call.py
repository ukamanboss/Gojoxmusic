# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# All rights reserved.

import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import AlreadyJoinedError, NoActiveGroupCall, TelegramServerError
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import MediumQualityAudio, MediumQualityVideo
from pytgcalls.types.stream import StreamAudioEnded

import config
from ShrutiMusic import LOGGER, YouTube, app
from ShrutiMusic.misc import db
from ShrutiMusic.utils.database import (add_active_chat, add_active_video_chat, get_lang, get_loop, group_assistant, is_autoend, music_on, remove_active_chat, remove_active_video_chat, set_loop)
from ShrutiMusic.utils.exceptions import AssistantErr
from ShrutiMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from ShrutiMusic.utils.inline.play import stream_markup
from ShrutiMusic.utils.stream.autoclear import auto_clean
from ShrutiMusic.utils.thumbnails import gen_thumb
from strings import get_string

autoend = {}
counter = {}

# ⚡ SMART AUTO-PLAY RAM TRACKERS (To save API Limits)
autoplay_limits = {} 
last_played_song = {}

async def _clear_(chat_id):
    db[chat_id] = []
    autoplay_limits.pop(chat_id, None)
    last_played_song.pop(chat_id, None)
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)

class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(name="NandAss1", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING1))
        self.one = PyTgCalls(self.userbot1, cache_duration=100)
        self.userbot2 = Client(name="NandAss2", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING2))
        self.two = PyTgCalls(self.userbot2, cache_duration=100)
        self.userbot3 = Client(name="NandAss3", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING3))
        self.three = PyTgCalls(self.userbot3, cache_duration=100)
        self.userbot4 = Client(name="NandAss4", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING4))
        self.four = PyTgCalls(self.userbot4, cache_duration=100)
        self.userbot5 = Client(name="NandAss5", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING5))
        self.five = PyTgCalls(self.userbot5, cache_duration=100)

    # (Keep all your existing pause_stream, stop_stream, etc. identical until change_stream)
    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except Exception:
            pass

    async def stop_stream_force(self, chat_id: int):
        try:
            if config.STRING1: await self.one.leave_group_call(chat_id)
            if config.STRING2: await self.two.leave_group_call(chat_id)
            if config.STRING3: await self.three.leave_group_call(chat_id)
            if config.STRING4: await self.four.leave_group_call(chat_id)
            if config.STRING5: await self.five.leave_group_call(chat_id)
            await _clear_(chat_id)
        except Exception: pass

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except Exception: pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try: await assistant.leave_group_call(chat_id)
        except Exception: pass

    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None):
        assistant = await group_assistant(self, chat_id)
        stream = AudioVideoPiped(link, audio_parameters=MediumQualityAudio(), video_parameters=MediumQualityVideo()) if video else AudioPiped(link, audio_parameters=MediumQualityAudio())
        await assistant.change_stream(chat_id, stream)

    async def join_call(self, chat_id: int, original_chat_id: int, link, video: Union[bool, str] = None, image: Union[bool, str] = None):
        assistant = await group_assistant(self, chat_id)
        stream = AudioVideoPiped(link, audio_parameters=MediumQualityAudio(), video_parameters=MediumQualityVideo()) if video else AudioPiped(link, audio_parameters=MediumQualityAudio())
        try:
            await assistant.join_group_call(chat_id, stream, stream_type=StreamType().pulse_stream)
        except NoActiveGroupCall: raise AssistantErr("No Active VC")
        except AlreadyJoinedError: raise AssistantErr("Already joined")
        except TelegramServerError: raise AssistantErr("Telegram Server Error")
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video: await add_active_video_chat(chat_id)

    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
                popped = check[0]

            if popped:
                last_played_song[chat_id] = popped.get("vidid")
                
            await auto_clean(popped)

            # ⚡ SMART AUTO-PLAY LOGIC IMPLEMENTATION
            if not check:
                auto_count = autoplay_limits.get(chat_id, 0)
                last_vid = last_played_song.get(chat_id)
                
                # Limit: 5 auto-play songs per VC session to save 100/day API limit
                if auto_count < 5 and last_vid:
                    rel_id, rel_title, rel_dur = await YouTube.get_related(last_vid)
                    if rel_id:
                        db[chat_id] = [{
                            "vidid": rel_id,
                            "title": rel_title,
                            "dur": rel_dur,
                            "by": "AutoPlay 🤖",
                            "chat_id": chat_id,
                            "streamtype": "audio",
                            "file": f"vid_{rel_id}",
                            "seconds": 0
                        }]
                        autoplay_limits[chat_id] = auto_count + 1
                        check = db.get(chat_id)
                    else:
                        await _clear_(chat_id)
                        return await client.leave_group_call(chat_id)
                else:
                    await _clear_(chat_id)
                    return await client.leave_group_call(chat_id)

        except Exception:
            try:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            except Exception: return
        
        # Continuation of streaming logic
        queued = check[0]["file"]
        language = await get_lang(chat_id)
        _ = get_string(language)
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        original_chat_id = check[0]["chat_id"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        db[chat_id][0]["played"] = 0
        video = True if str(streamtype) == "video" else False

        if "vid_" in queued:
            mystic = await app.send_message(original_chat_id, "🎵 **Fᴇᴛᴄʜɪɴɢ Nᴇxᴛ Tʀᴀᴄᴋ...**")
            try:
                file_path, direct = await YouTube.download(
                    videoid, mystic, videoid=True, video=video
                )
            except Exception:
                return await mystic.edit_text("❌ **Fᴀɪʟᴇᴅ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴇxᴛ sᴏɴɢ.**")
            
            stream = AudioVideoPiped(file_path, audio_parameters=MediumQualityAudio(), video_parameters=MediumQualityVideo()) if video else AudioPiped(file_path, audio_parameters=MediumQualityAudio())
            
            try:
                await client.change_stream(chat_id, stream)
            except Exception:
                return await app.send_message(original_chat_id, text="❌ **VC Eʀʀᴏʀ.**")
                
            img = await gen_thumb(videoid)
            button = stream_markup(_, chat_id)
            await mystic.delete()
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

    async def ping(self):
        pings = []
        if config.STRING1: pings.append(await self.one.ping)
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1: await self.one.start()
        if config.STRING2: await self.two.start()

    async def decorators(self):
        @self.one.on_kicked()
        @self.one.on_closed_voice_chat()
        @self.one.on_left()
        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        @self.one.on_stream_end()
        async def stream_end_handler1(client, update: Update):
            if not isinstance(update, StreamAudioEnded): return
            await self.change_stream(client, update.chat_id)

Nand = Call()
