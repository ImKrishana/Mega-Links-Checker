import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from xtra import check_cmd, LINK_REGEX

WELCOME = "Hello! Send me any MEGA link and I will check it."
IMG = "https://i.ibb.co/xK56gh8W/photo-2025-11-14-13-10-23-7572567765697953804.jpg"
EFCT = 5104841245755180586

btns = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Repo", url="https://github.com/Imkrishana/Mega-Links-Checker")]]
)

@Client.on_message((filters.text | filters.caption) & ~filters.command(["start"]))
async def auto_check_mega(client, message):
    text = message.text or message.caption or ""
    if not re.search(LINK_REGEX, text):
        return
    await check_cmd(client, message)

@Client.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_photo(
        IMG,
        caption=WELCOME,
        reply_markup=btns,
        message_effect_id=EFCT, 
        quote=True,
        has_spoiler=True
    )
