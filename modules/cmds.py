import asyncio
import os
import re
import sys
from time import monotonic
import aiohttp

from pyrogram.enums import ButtonStyle
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    LinkPreviewOptions,
)

from core.config_manager import Config
from bot import LOGGER
from helpers.db import database
from helpers.xtra import ButtonMaker, edit_message, send_message, new_task

WELCOME = (
    "<b>Hᴇʟʟᴏ!</b>\n\n"
    "Sᴇɴᴅ Mᴇ Aɴʏ <b>MEGA Lɪɴᴋ</b> "
    "ᴀɴᴅ I'ʟʟ Cʜᴇᴄᴋ Iᴛ Fᴏʀ Yᴏᴜ."
)

IMG = (
    "https://i.ibb.co/xK56gh8W/"
    "photo-2025-11-14-13-10-23-7572567765697953804.jpg"
)

CHECK_FORMAT = (
    "<blockquote><b>Nᴀᴍᴇ: {name}</b></blockquote>\n"
    "Tʏᴘᴇ : {type_}\n"
    "Tᴏᴛᴀʟ Fɪʟᴇs : {files}\n"
    "Tᴏᴛᴀʟ Sᴜʙғᴏʟᴅᴇʀs : {folders}\n"
    "Sɪᴢᴇ : {size}\n"
    'Lɪɴᴋ : <a href="{link}">Cʟɪᴄᴋ Hᴇʀᴇ</a>'
)

FOOTER = "\n\n<i>Cʜᴇᴄᴋᴇᴅ ʙʏ @MegaLinksCheckBot</i>"

LINK_REGEX = (
    r"https:\/\/(?:www\.)?(?:mega\.nz|mega\.co\.nz)"
    r"\/(?:file|folder)\/[\w-]+(?:#[\w-]+)?"
)

API_URL = "https://mega-checker-api-9qj8.onrender.com/api"

SESSION = None


def get_sender(message):
    return message.from_user or message.sender_chat


def parse_mega_json(data, link):
    return CHECK_FORMAT.format(
        name=data.get("name", "-"),
        type_=data.get("type", "-"),
        files=data.get("files", "-"),
        folders=data.get("folders", "-"),
        size=data.get("sizeFormatted", "-"),
        link=link,
    )


async def get_session():
    global SESSION

    if SESSION is None or SESSION.closed:
        SESSION = aiohttp.ClientSession()

    return SESSION


async def close_session():
    global SESSION

    if SESSION and not SESSION.closed:
        await SESSION.close()

    SESSION = None


async def send_log(client, sender, links, results):
    if not Config.LOG_CHANNEL:
        return

    try:
        LOGGER.info(
            f"Sending MEGA log - Links: {len(links)} | "
            f"Valid: {len(results)}"
        )

        if sender is None:
            name, uid = "Unknown", 0
        else:
            uid = sender.id
            name = (
                getattr(sender, "mention", None)
                or getattr(sender, "title", None)
                or "Unknown"
            )

        text = (
            "<b>MEGA Cʜᴇᴄᴋ Lᴏɢ</b>\n\n"
            f"<b>Uѕᴇʀ:</b> {name}\n"
            f"<b>Uѕᴇʀ ID:</b> <code>{uid}</code>\n"
            f"<b>Lɪɴᴋs:</b> <code>{len(links)}</code>\n"
            f"<b>Vᴀʟɪᴅ:</b> <code>{len(results)}</code>\n\n"
            + "\n\n".join(results)
            + FOOTER
        )

        await client.send_message(
            Config.LOG_CHANNEL[0],
            text,
            disable_web_page_preview=True,
        )

        LOGGER.info("MEGA log sent")

    except Exception as e:
        LOGGER.error(
            f"MEGA log error - {e}",
            exc_info=True
        )


async def auto_check_mega(client, message):
    text = message.text or message.caption or ""

    links = list(dict.fromkeys(
        re.findall(LINK_REGEX, text)
    ))

    if not links:
        return

    sender = get_sender(message)
    sender_id = sender.id if sender else 0

    LOGGER.info(
        f"MEGA check started - User: {sender_id} | "
        f"Links: {len(links)}"
    )

    wait = await send_message(
        message,
        f"<i>Cʜᴇᴄᴋɪɴɢ {len(links)} MEGA Lɪɴᴋ(s)...</i>"
    )

    session = await get_session()
    timeout = aiohttp.ClientTimeout(total=60)

    async def check(link):
        try:
            LOGGER.info(f"Checking MEGA link - {link}")

            async with session.post(
                API_URL,
                json={"url": link},
                timeout=timeout,
            ) as resp:
                data = await resp.json()

            if "error" in data:
                LOGGER.warning(
                    f"MEGA check failed - {link} | {data.get('error')}"
                )
                return None

            LOGGER.info(f"MEGA check successful - {link}")
            return parse_mega_json(data, link)

        except Exception as e:
            LOGGER.error(
                f"MEGA check error - {link} | {e}",
                exc_info=True
            )
            return None

    results = await asyncio.gather(
        *(check(link) for link in links)
    )

    results = [
        result
        for result in results
        if result
    ]

    LOGGER.info(
        f"MEGA check completed - User: {sender_id} | "
        f"Valid: {len(results)}/{len(links)}"
    )

    await send_log(
        client,
        sender,
        links,
        results,
    )

    if not results:
        await edit_message(
            wait,
            "<b>Nᴏ Vᴀʟɪᴅ MEGA Iɴғᴏ Fᴏᴜɴᴅ.</b>" + FOOTER
        )
        return

    buttons = None

    if len(results) == 1:
        match = re.search(
            LINK_REGEX,
            results[0]
        )

        if match:
            maker = ButtonMaker()
            maker.url_button(
                "Oᴘᴇɴ Iɴ MEGA",
                match.group(0),
                style=ButtonStyle.PRIMARY,
            )
            buttons = maker.build_menu(1)

    await edit_message(
        wait,
        "\n\n".join(results) + FOOTER,
        buttons,
    )


@new_task
async def start_cmd(client, message):
    try:
        buttons = ButtonMaker()
        buttons.url_button(
            "Rᴇᴘᴏ",
            "https://github.com/Imkrishana/Mega-Links-Checker",
            style=ButtonStyle.PRIMARY,
        )

        await send_message(
            message,
            WELCOME + FOOTER,
            buttons.build_menu(1),
            disable_web_page_preview=False,
            link_preview_options=LinkPreviewOptions(
                url=IMG,
                prefer_large_media=True,
                show_above_text=True,
            ),
        )

        if message.from_user:
            await database.set_pm_users(message.from_user.id)

    except Exception as e:
        LOGGER.error(e, exc_info=True)


@new_task
async def restart(_, message):
    try:
        msg = await send_message(
            message,
            "<b>Rᴇsᴛᴀʀᴛɪɴɢ...</b>"
        )

        with open(".restartmsg", "w") as f:
            f.write(f"{msg.chat.id}\n{msg.id}\n")

        os.execl(
            sys.executable,
            sys.executable,
            "-B",
            "main.py",
        )

    except Exception as e:
        LOGGER.error(e, exc_info=True)


@new_task
async def ping(_, message):
    start_time = monotonic()

    reply = await send_message(
        message,
        "<i>Sᴛᴀʀᴛɪɴɢ Pɪɴɢ...</i>"
    )

    end_time = monotonic()

    await edit_message(
        reply,
        (
            "<i>Pᴏɴɢ!</i>\n"
            f"<code>{int((end_time - start_time) * 1000)} ms</code>"
        )
    )
