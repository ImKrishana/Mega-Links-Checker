from asyncio import gather, sleep
from functools import wraps

from pyrogram.types import Message, ReplyParameters
from pyrogram.enums import ParseMode, ButtonStyle
from pyrogram.errors import (
    FloodWait,
    MessageNotModified,
    MessageEmpty,
    MessageTooLong,
    MessageDeleteForbidden,
    ReplyMarkupInvalid,
    PhotoInvalidDimensions,
    WebpageCurlFailed,
    WebpageMediaEmpty,
    MediaEmpty,
    MediaCaptionTooLong,
    EntityBoundsInvalid,
    PeerIdInvalid,
)

from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from bot import Zake, LOGGER, bot_loop, user_data


URL_SCHEMES = ("http://", "https://", "tg://")


def _btn_style(style=None):
    return style or ButtonStyle.DEFAULT


def valid_url(link):
    text = str(link or "").strip()

    if not text.lower().startswith(URL_SCHEMES):
        return ""

    rest = text.split("://", 1)[1]

    if not rest or rest.startswith(("/", "?", "#")):
        return ""

    if any(ch.isspace() for ch in text):
        return ""

    return text


class ButtonMaker:
    def __init__(self):
        self.buttons = {
            "default": [],
            "header": [],
            "f_body": [],
            "l_body": [],
            "footer": [],
        }

    def url_button(self, key, link, position=None, style=None):
        safe = valid_url(link)

        if not safe:
            LOGGER.warning(
                f"dropping button {key!r} with unusable url {link!r}"
            )
            return

        self.buttons[
            position if position in self.buttons else "default"
        ].append(
            InlineKeyboardButton(
                text=key,
                url=safe,
                style=_btn_style(style)
            )
        )

    def web_app_button(self, key, link, position=None, style=None):
        self.buttons[
            position if position in self.buttons else "default"
        ].append(
            InlineKeyboardButton(
                text=key,
                web_app=WebAppInfo(url=link),
                style=_btn_style(style)
            )
        )

    def data_button(self, key, data, position=None, style=None):
        self.buttons[
            position if position in self.buttons else "default"
        ].append(
            InlineKeyboardButton(
                text=key,
                callback_data=data,
                style=_btn_style(style)
            )
        )

    def build_menu(
        self,
        b_cols=1,
        h_cols=8,
        fb_cols=2,
        lb_cols=2,
        f_cols=8
    ):
        def chunk(lst, n):
            return [
                lst[i : i + n]
                for i in range(0, len(lst), n)
            ]

        menu = chunk(self.buttons["default"], b_cols)

        menu = (
            chunk(self.buttons["header"], h_cols)
            if self.buttons["header"]
            else []
        ) + menu

        for key, cols in (
            ("f_body", fb_cols),
            ("l_body", lb_cols),
            ("footer", f_cols),
        ):
            if self.buttons[key]:
                menu += chunk(self.buttons[key], cols)

        return InlineKeyboardMarkup(menu)

    def reset(self):
        for key in self.buttons:
            self.buttons[key].clear()


async def delete_message(*args):
    tasks = [
        msg.delete()
        for msg in args
        if isinstance(msg, Message)
    ]

    if not tasks:
        return

    results = await gather(
        *tasks,
        return_exceptions=True
    )

    for result in results:
        if isinstance(result, MessageDeleteForbidden):
            pass
        elif isinstance(result, Exception):
            LOGGER.error(result)


async def send_message(
    message,
    text,
    buttons=None,
    block=True,
    photo=None,
    **kwargs
):
    try:
        if photo:
            try:
                if isinstance(message, Message):
                    return await message.reply_photo(
                        photo=photo,
                        caption=text,
                        reply_parameters=ReplyParameters(
                            message_id=message.id
                        ),
                        reply_markup=buttons,
                        disable_notification=True,
                        **kwargs,
                    )

                return await Zake.send_photo(
                    chat_id=message,
                    photo=photo,
                    caption=text,
                    reply_markup=buttons,
                    disable_notification=True,
                    **kwargs,
                )

            except FloodWait as f:
                LOGGER.warning(str(f))

                if not block:
                    return str(f)

                await sleep(f.value * 1.2)

                return await send_message(
                    message,
                    text,
                    buttons,
                    block,
                    photo,
                    **kwargs
                )

            except MediaCaptionTooLong:
                return await send_message(
                    message,
                    text[:1024],
                    buttons,
                    block,
                    photo,
                    **kwargs
                )

            except (
                PhotoInvalidDimensions,
                WebpageCurlFailed,
                WebpageMediaEmpty,
                MediaEmpty,
            ):
                LOGGER.error(
                    "Error while sending photo",
                    exc_info=True
                )
                return

            except Exception:
                LOGGER.error(
                    "Error while sending photo",
                    exc_info=True
                )
                return

        if isinstance(message, Message):
            return await message.reply(
                text=text,
                reply_parameters=ReplyParameters(
                    message_id=message.id
                ),
                disable_web_page_preview=kwargs.pop("disable_web_page_preview", True),
                disable_notification=True,
                reply_markup=buttons,
                **kwargs,
            )

        return await Zake.send_message(
            chat_id=int(message),
            text=text,
            disable_web_page_preview=True,
            disable_notification=True,
            reply_markup=buttons,
            **kwargs,
        )

    except FloodWait as f:
        LOGGER.warning(str(f))

        if not block:
            return str(f)

        await sleep(f.value * 1.2)

        return await send_message(
            message,
            text,
            buttons,
            block,
            photo,
            **kwargs
        )

    except ReplyMarkupInvalid as rmi:
        LOGGER.warning(str(rmi))

        return await send_message(
            message,
            text,
            None,
            block,
            photo,
            **kwargs
        )

    except MessageTooLong:
        return await send_message(
            message,
            text[:4096],
            buttons,
            block,
            photo,
            **kwargs
        )

    except (MessageEmpty, EntityBoundsInvalid):
        return await send_message(
            message,
            text,
            buttons,
            block,
            photo,
            parse_mode=ParseMode.DISABLED,
            **kwargs
        )

    except PeerIdInvalid:
        LOGGER.warning(
            f"PeerIdInvalid {type(message)}"
        )

        if isinstance(message, (int, str)):
            return await send_message(
                int(message),
                text,
                buttons,
                block,
                photo,
                **kwargs
            )

    except ConnectionError:
        return

    except Exception as e:
        LOGGER.error(
            str(e),
            exc_info=True
        )
        return str(e)


async def edit_message(
    message,
    text,
    buttons=None,
    block=True
):
    try:
        if not isinstance(text, str):
            return await Zake.edit_message_text(
                message.chat.id,
                message.id,
                "",
                rich_text=text,
                reply_markup=buttons,
            )

        if message.media:
            return await message.edit_caption(
                caption=text,
                reply_markup=buttons
            )

        return await message.edit(
            text=text,
            disable_web_page_preview=True,
            reply_markup=buttons,
        )

    except (MessageNotModified, MessageEmpty):
        pass

    except ReplyMarkupInvalid as rmi:
        LOGGER.warning(str(rmi))

        return await edit_message(
            message,
            text,
            None,
            block
        )

    except FloodWait as f:
        LOGGER.warning(str(f))

        if not block:
            return str(f)

        await sleep(f.value * 1.2)

        return await edit_message(
            message,
            text,
            buttons,
            block
        )

    except OSError:
        return

    except Exception as e:
        LOGGER.error(
            str(e),
            exc_info=True
        )
        return str(e)


async def edit_reply_markup(message, buttons):
    try:
        return await message.edit_reply_markup(
            reply_markup=buttons
        )

    except MessageNotModified:
        pass

    except FloodWait as f:
        LOGGER.warning(str(f))

        await sleep(f.value * 1.2)

        return await edit_reply_markup(
            message,
            buttons
        )

    except OSError:
        return

    except Exception as e:
        LOGGER.error(
            str(e),
            exc_info=True
        )
        return str(e)


async def send_file(
    message,
    file,
    caption="",
    buttons=None
):
    try:
        if isinstance(message, Message):
            return await message.reply_document(
                document=file,
                reply_parameters=ReplyParameters(
                    message_id=message.id
                ),
                caption=caption,
                disable_notification=True,
                reply_markup=buttons,
            )

        return await Zake.send_document(
            chat_id=message,
            document=file,
            caption=caption,
            disable_notification=True,
            reply_markup=buttons,
        )

    except FloodWait as f:
        LOGGER.warning(str(f))

        await sleep(f.value * 1.2)

        return await send_file(
            message,
            file,
            caption,
            buttons
        )

    except ConnectionError:
        return

    except Exception as e:
        LOGGER.error(
            str(e),
            exc_info=True
        )
        return str(e)


def update_user_ldata(id_, key, value):
    user_data.setdefault(id_, {})
    user_data[id_][key] = value


def new_task(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        task = bot_loop.create_task(
            func(*args, **kwargs)
        )
        return task

    return wrapper