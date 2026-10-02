from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

from bot import Zake, LOGGER
from modules import *
from helpers.filters import CustomFilters


async def add_handlers():
    Zake.add_handler(
        MessageHandler(
            start_cmd,
            filters.command("start")
        )
    )

    Zake.add_handler(
        MessageHandler(
            restart,
            filters.command("restart") & CustomFilters.owner
        )
    )

    Zake.add_handler(
        MessageHandler(
            authorize,
            filters.command("authorize") & CustomFilters.owner
        )
    )

    Zake.add_handler(
        MessageHandler(
            unauthorize,
            filters.command("unauthorize") & CustomFilters.owner
        )
    )

    Zake.add_handler(
        MessageHandler(
            add_blacklist,
            filters.command(["bl", "blacklist"])
            & CustomFilters.owner
        )
    )

    Zake.add_handler(
        MessageHandler(
            remove_blacklist,
            filters.command(["unbl", "unblacklist"])
            & CustomFilters.owner
        )
    )

    Zake.add_handler(
        MessageHandler(
            black_listed,
            filters.regex(r"^/")
            & CustomFilters.blacklisted
        )
    )

    Zake.add_handler(
        MessageHandler(
            ping,
            filters.command("ping")
        )
    )

    Zake.add_handler(
        MessageHandler(
            log,
            filters.command("log")
            & CustomFilters.owner
        )
    )

    Zake.add_handler(
        CallbackQueryHandler(
            log_cb,
            filters.regex(r"^log ")
        )
    )
    
    Zake.add_handler(
    MessageHandler(
        broadcast,
        filters.command("broadcast") & CustomFilters.owner
    )
    )

    Zake.add_handler(
        MessageHandler(
            auto_check_mega,
            (filters.text | filters.caption)
            & ~filters.regex(r"^/")
        )
    )

    LOGGER.info("handlers registered !")
