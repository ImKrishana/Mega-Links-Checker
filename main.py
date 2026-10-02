import os

from pyrogram.types import BotCommand

from bot import Zake, LOGGER, bot_loop
from core.config_manager import Config
from core.handlers import add_handlers
from core.startup import load_user_data
from helpers.db import database
from web import start_web


async def restart():
    if os.path.exists(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)

        try:
            await Zake.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text="<b><i>Restarted !</i></b>"
            )
        except Exception as e:
            LOGGER.error(f"Restarting ERROR - {e}")

        try:
            os.remove(".restartmsg")
        except OSError:
            pass


try:
    bot_loop.run_until_complete(database.connect())
    bot_loop.run_until_complete(load_user_data())
    bot_loop.run_until_complete(add_handlers())
    web_runner = bot_loop.run_until_complete(start_web(Config.PORT))
    LOGGER.info(f"Wserver started - {Config.PORT}")
    bot_loop.run_until_complete(Zake.start())
    Zake.me = bot_loop.run_until_complete(Zake.get_me())
    LOGGER.info(f"TheZake Client Started - @{Zake.me.username}")
    bot_loop.run_until_complete(Zake.set_bot_commands([BotCommand("start", "Start the bot"), BotCommand("ping", "Check bot ping"), BotCommand("broadcast", "Broadcast message"), BotCommand("authorize", "Authorize chat"), BotCommand("unauthorize", "Unauthorize chat"), BotCommand("blacklist", "Blacklist user"), BotCommand("unblacklist", "Remove blacklist"), BotCommand("log", "Get bot logs"), BotCommand("restart", "Restart bot")]))
    bot_loop.run_until_complete(restart())
    bot_loop.run_forever()

except Exception as e:
    LOGGER.error(e, exc_info=True)
    LOGGER.info("Bot Stopped !")
    bot_loop.run_until_complete(Zake.stop())
