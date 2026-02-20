from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from pyrogram.errors import FloodWait, MessageNotModified, MessageEmpty
import logging
import re
import asyncio
import aiohttp
from asyncio import sleep
from pyrogram.types import Message
from config import LOG_CHANNEL

SESSION = aiohttp.ClientSession()

class ButtonMaker:
    def __init__(self):
        self._button = []
        self._header_button = []
        self._footer_button = []

    def data_button(self, key, data, position=None):
        btn = InlineKeyboardButton(text=key, callback_data=data)
        if not position:
            self._button.append(btn)
        elif position == "header":
            self._header_button.append(btn)
        elif position == "footer":
            self._footer_button.append(btn)

    def url_button(self, key, url, position=None):
        btn = InlineKeyboardButton(text=key, url=url)
        if not position:
            self._button.append(btn)
        elif position == "header":
            self._header_button.append(btn)
        elif position == "footer":
            self._footer_button.append(btn)

    def new_row(self):
        self._button.append(None)

    def build_menu(self, b_cols=2, h_cols=8, f_cols=8):
        menu = []
        row = []
        for btn in self._button:
            if btn is None:
                if row:
                    menu.append(row)
                row = []
            else:
                row.append(btn)
                if len(row) == b_cols:
                    menu.append(row)
                    row = []
        if row:
            menu.append(row)
        if self._header_button:
            menu.insert(0, self._header_button)
        if self._footer_button:
            menu.append(self._footer_button)
        return InlineKeyboardMarkup(menu)

async def edit_message(message, text, buttons=None, markdown=False):
    parse_mode = enums.ParseMode.MARKDOWN if markdown else enums.ParseMode.HTML
    try:
        await message.edit(
            text=text,
            disable_web_page_preview=True,
            reply_markup=buttons,
            parse_mode=parse_mode
        )
    except FloodWait as f:
        await sleep(f.value * 1.2)
        return await edit_message(message, text, buttons, markdown)
    except (MessageNotModified, MessageEmpty):
        pass
    except Exception as e:
        logging.error(str(e))
        raise

async def send_message(message, text, buttons=None, photo=None, markdown=False, block=True):
    parse_mode = enums.ParseMode.MARKDOWN if markdown else enums.ParseMode.HTML
    try:
        if photo:
            return await message.reply_photo(
                photo=photo,
                caption=text,
                reply_markup=buttons,
                disable_notification=True,
                parse_mode=parse_mode
            )
        return await message.reply(
            text=text,
            quote=True,
            disable_web_page_preview=True,
            disable_notification=True,
            reply_markup=buttons,
            parse_mode=parse_mode
        )
    except FloodWait as f:
        await sleep(f.value * 1.2)
        if not block:
            return message
        return await send_message(message, text, buttons, photo, markdown)
    except Exception as e:
        logging.error(str(e))
        raise

CHECK_FORMAT = (
    "<blockquote><b>Name: {name}</b></blockquote>\n"
    "ᴛʏᴘᴇ : {type_}\n"
    "ᴛᴏᴛᴀʟ ғɪʟᴇs : {files}\n"
    "ᴛᴏᴛᴀʟ sᴜʙғᴏʟᴅᴇʀs : {folders}\n"
    "sɪᴢᴇ : {size}\n"
    'Lɪɴᴋ : <a href="{link}">Cʟɪᴄᴋ Hᴇʀᴇ</a>'
)

LINK_REGEX = r'https:\/\/(?:www\.)?(?:mega\.nz|mega\.co\.nz)\/(?:file|folder)\/[\w-]+(?:#[\w-]+)?'
API_URL = "https://mega-checker-api-9qj8.onrender.com/api"

def parse_mega_json(data, link):
    name = data.get("name", "-")
    type_ = data.get("type", "-")
    files = data.get("files", "-")
    folders = data.get("folders", "-")
    size = data.get("sizeFormatted", "-")
    return CHECK_FORMAT.format(name=name, type_=type_, files=files, folders=folders, size=size, link=link)

async def send_log(client, user, links, results):
    if not LOG_CHANNEL:
        return
    log_channel_id = LOG_CHANNEL[0]
    if user is None:
        user_display = "Unknown User"
    else:
        user_display = (
            f"@{user.username}"
            if getattr(user, "username", None)
            else f"{user.first_name} (<code>{user.id}</code>)"
        )
    log_text = (
        f"<b>Check Task Log</b>\n"
        f"User: {user_display}\n"
        f"Checked {len(links)} MEGA link(s):\n"
        + "\n".join([f"<code>{link}</code>" for link in links]) +
        "\n\n<b>Results:</b>\n"
        + ("\n".join(results) if results else "No valid MEGA info found.")
    )
    try:
        await client.send_message(chat_id=log_channel_id, text=log_text, disable_web_page_preview=True)
    except Exception:
        pass

async def check_single_link(link):
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with SESSION.post(API_URL, json={"url": link}, timeout=timeout) as resp:
            data = await resp.json()
    except:
        return None
    if "error" in data:
        return None
    return parse_mega_json(data, link)

async def check_cmd(client, message: Message):
    text = message.text or message.caption or ""
    links = list({x.strip() for x in re.findall(LINK_REGEX, text) if x.strip()})
    if not links:
        return
    wait_msg = await send_message(
        message,
        f"Checking {len(links)} MEGA link{'s' if len(links) > 1 else ''}...",
        block=True
    )
    tasks = [check_single_link(link) for link in links]
    results = await asyncio.gather(*tasks)
    valid_results = [res for res in results if res]
    await send_log(client, message.from_user, links, valid_results)
    if not valid_results:
        return await edit_message(wait_msg, "No valid MEGA info found.", markdown=False)
    text_output = "\n".join(valid_results)
    if message.from_user is None:
        user_display = "Unknown User"
    else:
        user_display = (
            f"@{message.from_user.username}"
            if getattr(message.from_user, "username", None)
            else f"{message.from_user.first_name} (<code>{message.from_user.id}</code>)"
        )
    text_output += f"\n\n<b>By : {user_display}</b>"
    bm = ButtonMaker()
    if len(valid_results) == 1:
        match = re.search(LINK_REGEX, valid_results[0])
        if match:
            bm.url_button("Open in MEGA", match.group(0))
        return await edit_message(
            wait_msg,
            text_output,
            buttons=bm.build_menu(1),
            markdown=False
        )
    await edit_message(wait_msg, text_output, markdown=False)
