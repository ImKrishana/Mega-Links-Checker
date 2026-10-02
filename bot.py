from asyncio import new_event_loop, set_event_loop
from logging import (
    ERROR,
    INFO,
    WARNING,
    FileHandler,
    StreamHandler,
    basicConfig,
    getLogger,
)

from uvloop import install
from pyrogram import Client
from core.config_manager import Config
install()

bot_loop = new_event_loop()
set_event_loop(bot_loop)

getLogger("pyrogram").setLevel(ERROR)
getLogger("pymongo").setLevel(WARNING)
getLogger("aiohttp").setLevel(WARNING)

basicConfig(
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%d-%b-%y %I:%M:%S %p",
    handlers=[FileHandler("log.txt"), StreamHandler()],
    level=INFO,
)

LOGGER = getLogger(__name__)

auth_chats = {}
user_data = {}

Zake = Client(
    "TheZakeBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=50,
    in_memory=True
)
