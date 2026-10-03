from asyncio import sleep
from html import escape
from secrets import token_hex
from time import time

from pyrogram.enums import ButtonStyle
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    UserIsBlocked,
)

from bot import LOGGER, Zake, user_data
from core.config_manager import Config
from helpers.db import database
from helpers.xtra import (
    delete_message,
    edit_message,
    edit_reply_markup,
    send_file,
    send_message,
    ButtonMaker,
    new_task,
    update_user_ldata,
)

bc_cache = {}


def get_readable_time(seconds: int):
    periods = [("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
    result = ""
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f"{int(period_value)}{period_name}"
    return result


def _parse_time(time_str):
    time_str = time_str.strip().lower()
    mult = {"d": 86400, "h": 3600, "m": 60}

    for suffix, factor in mult.items():
        if time_str.endswith(suffix):
            try:
                return int(time_str[:-len(suffix)]) * factor
            except ValueError:
                return None

    return None


def _format_remaining(seconds):
    if seconds >= 86400:
        d = seconds // 86400
        h = (seconds % 86400) // 3600
        return f"{d}d {h}h" if h else f"{d}d"

    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m" if m else f"{h}h"

    m = seconds // 60
    return f"{m}m"


def _get_blacklist_info(bl_value):
    if not bl_value:
        return False, None

    if bl_value is True:
        return True, "Permanent"

    if isinstance(bl_value, (int, float)):
        remaining = bl_value - time()

        if remaining > 0:
            return True, _format_remaining(int(remaining))

    return False, None


@new_task
async def authorize(_, message):
    msg = message.text.split()
    thread_id = None

    if len(msg) > 1:
        if "|" in msg[1]:
            chat_id, thread_id = list(map(int, msg[1].split("|")))
        else:
            chat_id = int(msg[1].strip())

    elif (
        reply_to := message.reply_to_message
    ) and reply_to.id != message.message_thread_id:
        chat_id = (reply_to.from_user or reply_to.sender_chat).id

    else:
        if message.is_topic_message:
            thread_id = message.message_thread_id

        chat_id = message.chat.id

    if chat_id in user_data and user_data[chat_id].get("AUTH"):
        if (
            thread_id is not None
            and thread_id in user_data[chat_id].get("thread_ids", [])
            or thread_id is None
        ):
            msg = "<b>Aʟʀᴇᴀᴅʏ Aᴜᴛʜᴏʀɪᴢᴇᴅ!</b>"

        else:
            if "thread_ids" in user_data[chat_id]:
                user_data[chat_id]["thread_ids"].append(thread_id)
            else:
                user_data[chat_id]["thread_ids"] = [thread_id]

            await database.update_user_data(chat_id)
            msg = "<b>Aᴜᴛʜᴏʀɪᴢᴇᴅ</b>"

    else:
        update_user_ldata(chat_id, "AUTH", True)

        if thread_id is not None:
            update_user_ldata(chat_id, "thread_ids", [thread_id])

        await database.update_user_data(chat_id)
        msg = "<b>Aᴜᴛʜᴏʀɪᴢᴇᴅ</b>"

    await send_message(message, msg)


@new_task
async def unauthorize(_, message):
    msg = message.text.split()
    thread_id = None

    if len(msg) > 1:
        if "|" in msg[1]:
            chat_id, thread_id = list(map(int, msg[1].split("|")))
        else:
            chat_id = int(msg[1].strip())

    elif (
        reply_to := message.reply_to_message
    ) and reply_to.id != message.message_thread_id:
        chat_id = (reply_to.from_user or reply_to.sender_chat).id

    else:
        if message.is_topic_message:
            thread_id = message.message_thread_id

        chat_id = message.chat.id

    if chat_id in user_data and user_data[chat_id].get("AUTH"):
        if (
            thread_id
            and thread_id in user_data[chat_id].get("thread_ids", [])
        ):
            user_data[chat_id]["thread_ids"].remove(thread_id)

            if not user_data[chat_id].get("thread_ids"):
                update_user_ldata(chat_id, "AUTH", False)

        else:
            update_user_ldata(chat_id, "AUTH", False)

        await database.update_user_data(chat_id)
        msg = "<b>Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ</b>"

    else:
        msg = "<b>Aʟʀᴇᴀᴅʏ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ!</b>"

    await send_message(message, msg)


@new_task
async def add_blacklist(_, message):
    msg = message.text.split()
    id_ = None
    time_str = None

    i = 1

    while i < len(msg):
        arg = msg[i].lower()

        if arg.startswith("-t") and len(arg) > 2:
            time_str = arg[2:]
            i += 1

        elif arg == "-t" and i + 1 < len(msg):
            time_str = msg[i + 1]
            i += 2

        else:
            try:
                id_ = int(msg[i])
            except ValueError:
                pass

            i += 1

    if id_ is None and message.reply_to_message:
        id_ = (
            message.reply_to_message.from_user
            or message.reply_to_message.sender_chat
        ).id

    if id_ is None:
        help_msg = (
            "<b>Bʟᴀᴄᴋʟɪsᴛ Uѕᴀɢᴇ</b>\n\n"
            "<b>Pᴇʀᴍᴀɴᴇɴᴛ:</b> <code>/bl {user_id}</code>\n"
            "<b>Tᴇᴍᴘᴏʀᴀʀʏ:</b> <code>/bl {user_id} -t 1d</code>\n"
            "<b>Rᴇᴘʟʏ:</b> <code>/bl -t 2h</code> "
            "<i>(Rᴇᴘʟʏ Tᴏ Uѕᴇʀ)</i>\n"
            "<b>Tɪᴍᴇ Fᴏʀᴍᴀᴛ:</b> <code>3d</code> | "
            "<code>12h</code> | <code>20m</code> "
            "<i>(Aɴʏ Dɪɢɪᴛ)</i>"
        )

        return await send_message(message, help_msg)

    if id_ in user_data and _get_blacklist_info(
        user_data[id_].get("BLACKLIST")
    )[0]:
        return await send_message(
            message,
            f"<b>Uѕᴇʀ Aʟʀᴇᴀᴅʏ Bʟᴀᴄᴋʟɪsᴛᴇᴅ!</b>\n"
            f"<code>{id_}</code>"
        )

    if time_str:
        seconds = _parse_time(time_str)

        if seconds is None:
            return await send_message(
                message,
                "<b>Iɴᴠᴀʟɪᴅ Tɪᴍᴇ Fᴏʀᴍᴀᴛ!</b>\n"
                "Uѕᴇ <code>1d</code>, <code>2h</code>, "
                "ᴏʀ <code>30m</code>."
            )

        bl_value = time() + seconds
        remaining = _format_remaining(seconds)

        update_user_ldata(
            id_,
            "BLACKLIST",
            bl_value
        )

        await database.update_user_data(id_)

        msg = (
            "<b>Bʟᴀᴄᴋʟɪsᴛ Aᴘᴘʟɪᴇᴅ</b>\n\n"
            f"<b>Uѕᴇʀ:</b> <code>{id_}</code>\n"
            "<b>Tʏᴘᴇ:</b> Tᴇᴍᴘᴏʀᴀʀʏ\n"
            f"<b>Dᴜʀᴀᴛɪᴏɴ:</b> <code>{remaining}</code>\n"
            f"<b>Eхᴘɪʀᴇs:</b> <i>{remaining} Fʀᴏᴍ Nᴏᴡ</i>"
        )

    else:
        update_user_ldata(
            id_,
            "BLACKLIST",
            True
        )

        await database.update_user_data(id_)

        msg = (
            "<b>Bʟᴀᴄᴋʟɪsᴛ Aᴘᴘʟɪᴇᴅ</b>\n\n"
            f"<b>Uѕᴇʀ:</b> <code>{id_}</code>\n"
            "<b>Tʏᴘᴇ:</b> Pᴇʀᴍᴀɴᴇɴᴛ\n"
            "<b>Sᴛᴀᴛᴜs:</b> "
            "<i>Rᴇsᴛʀɪᴄᴛᴇᴅ ғʀᴏᴍ Bᴏᴛ</i>"
        )

    await send_message(message, msg)


@new_task
async def remove_blacklist(_, message):
    msg = message.text.split()
    id_ = None

    if len(msg) > 1:
        try:
            id_ = int(msg[1].strip())
        except ValueError:
            pass

    if id_ is None and message.reply_to_message:
        id_ = (
            message.reply_to_message.from_user
            or message.reply_to_message.sender_chat
        ).id

    if id_ is None:
        return await send_message(
            message,
            "<b>Gɪᴠᴇ Uѕᴇʀ ID ᴏʀ Rᴇᴘʟʏ Tᴏ Tʜᴇ Uѕᴇʀ's Mᴇssᴀɢᴇ</b>"
        )

    bl_value = user_data.get(id_, {}).get("BLACKLIST")
    is_bl, remaining = _get_blacklist_info(bl_value)

    if not is_bl:
        return await send_message(
            message,
            f"<b>Uѕᴇʀ Aʟʀᴇᴀᴅʏ Fʀᴇᴇ</b>\n"
            f"<code>{id_}</code>"
        )

    update_user_ldata(
        id_,
        "BLACKLIST",
        False
    )

    await database.update_user_data(id_)

    await send_message(
        message,
        (
            "<b>Bʟᴀᴄᴋʟɪsᴛ Rᴇᴍᴏᴠᴇᴅ</b>\n\n"
            f"<b>Uѕᴇʀ:</b> <code>{id_}</code>\n"
            "<b>Sᴛᴀᴛᴜs:</b> <i>Uѕᴇʀ Sᴇᴛ Fʀᴇᴇ</i>"
        )
    )


@new_task
async def black_listed(_, message):
    await send_message(
        message,
        "<b>Bʟᴀᴄᴋʟɪsᴛᴇᴅ Dᴇᴛᴇᴄᴛᴇᴅ</b>\n"
        "<i>Rᴇsᴛʀɪᴄᴛᴇᴅ ғʀᴏᴍ Bᴏᴛ</i>"
    )


@new_task
async def log(_, message):
    uid = message.from_user.id

    buttons = ButtonMaker()

    buttons.data_button(
        "Lᴏɢ Dɪsᴘ",
        f"log {uid} disp"
    )

    buttons.data_button(
        "Cʟᴏsᴇ",
        f"log {uid} close",
        style=ButtonStyle.DANGER
    )

    await send_file(
        message,
        "log.txt",
        buttons=buttons.build_menu(2)
    )


@new_task
async def log_cb(_, query):
    data = query.data.split()
    message = query.message
    user_id = query.from_user.id

    if user_id != int(data[1]):
        await query.answer(
            "Nᴏᴛ Yᴏᴜʀs!",
            show_alert=True
        )
        return

    if data[2] == "close":
        await query.answer()

        await delete_message(
            message,
            message.reply_to_message
        )

    elif data[2] == "disp":
        await query.answer("Fᴇᴛᴄʜɪɴɢ Lᴏɢ...")

        try:
            with open("log.txt", "r") as f:
                content = f.read()

            def parse(line):
                parts = line.split("] [", 1)
                return f"[{parts[1]}" if len(parts) > 1 else line

            res = []
            total = 0

            for line in reversed(content.splitlines()):
                line = parse(line)
                res.append(line)
                total += len(line) + 1

                if total > 3500:
                    break

            text = (
                f"<b>Sʜᴏᴡɪɴɢ Lᴀsᴛ {len(res)} Lɪɴᴇs "
                "ғʀᴏᴍ log.txt:</b>\n\n"
                "----------<b>Sᴛᴀʀᴛ Lᴏɢ</b>----------\n\n"
                "<blockquote expandable>"
                f"{escape(chr(10).join(reversed(res)))}"
                "</blockquote>\n"
                "----------<b>Eɴᴅ Lᴏɢ</b>----------"
            )

            buttons = ButtonMaker()

            buttons.data_button(
                "Cʟᴏsᴇ",
                f"log {user_id} close",
                style=ButtonStyle.DANGER
            )

            await send_message(
                message,
                text,
                buttons.build_menu(1)
            )

            await edit_reply_markup(
                message,
                None
            )

        except Exception as e:
            LOGGER.error(
                f"TG Log Display : {e}",
                exc_info=True
            )


async def delete_broadcast(bc_id, message):
    if bc_id not in bc_cache:
        return await send_message(message, "Iɴᴠᴀʟɪᴅ Bʀᴏᴀᴅᴄᴀsᴛ ID!")

    temp_wait = await send_message(
        message,
        "<i>Dᴇʟᴇᴛɪɴɢ Tʜᴇ Bʀᴏᴀᴅᴄᴀsᴛᴇᴅ Mᴇssᴀɢᴇ! Pʟᴇᴀsᴇ Wᴀɪᴛ ...</i>"
    )
    total, success, failed = 0, 0, 0
    msgs = bc_cache.get(bc_id, [])
    for uid, msg_id in msgs:
        try:
            await (await Zake.get_messages(uid, msg_id)).delete()
            success += 1
        except FloodWait as e:
            await sleep(e.value)
            await (await Zake.get_messages(uid, msg_id)).delete()
            success += 1
        except Exception as e:
            print(f"Error deleting message for user {uid}: {e}")
            failed += 1
        total += 1
    return await edit_message(
        temp_wait,
        f"""<b><i>Bʀᴏᴀᴅᴄᴀsᴛ Dᴇʟᴇᴛᴇᴅ Sᴛᴀᴛs :</i></b>

<b>Tᴏᴛᴀʟ Uѕᴇʀs:</b> <code>{total}</code>
<b>Sᴜᴄᴄᴇss:</b> <code>{success}</code>
<b>Fᴀɪʟᴇᴅ Aᴛᴛᴇᴍᴘᴛs:</b> <code>{failed}</code>

<b>Bʀᴏᴀᴅᴄᴀsᴛ ID:</b> <code>{bc_id}</code>""",
    )


async def edit_broadcast(bc_id, message, rply):
    if bc_id not in bc_cache:
        return await send_message(message, "Iɴᴠᴀʟɪᴅ Bʀᴏᴀᴅᴄᴀsᴛ ID!")

    temp_wait = await send_message(
        message,
        "<i>Eᴅɪᴛɪɴɢ Tʜᴇ Bʀᴏᴀᴅᴄᴀsᴛᴇᴅ Mᴇssᴀɢᴇ! Pʟᴇᴀsᴇ Wᴀɪᴛ ...</i>"
    )
    total, success, failed = 0, 0, 0
    for uid, msg_id in bc_cache[bc_id]:
        msg = await Zake.get_messages(uid, msg_id)
        if hasattr(msg, "forward_from"):
            return await edit_message(
                temp_wait,
                "<i>Fᴏʀᴡᴀʀᴅᴇᴅ Mᴇssᴀɢᴇs Cᴀɴ'ᴛ Bᴇ Eᴅɪᴛᴇᴅ, Oɴʟʏ Cᴀɴ Bᴇ Dᴇʟᴇᴛᴇᴅ!</i>",
            )
        try:
            await msg.edit(
                text=rply.text,
                entities=rply.entities,
                reply_markup=rply.reply_markup,
            )
            await sleep(0.3)
            success += 1
        except FloodWait as e:
            await sleep(e.value)
            await msg.edit(
                text=rply.text,
                entities=rply.entities,
                reply_markup=rply.reply_markup,
            )
            success += 1
        except Exception as e:
            print(f"Error editing message for user {uid}: {e}")
            failed += 1
        total += 1
    return await edit_message(
        temp_wait,
        f"""<b><i>Bʀᴏᴀᴅᴄᴀsᴛ Eᴅɪᴛᴇᴅ Sᴛᴀᴛs :</i></b>

<b>Tᴏᴛᴀʟ Uѕᴇʀs:</b> <code>{total}</code>
<b>Sᴜᴄᴄᴇss:</b> <code>{success}</code>
<b>Fᴀɪʟᴇᴅ Aᴛᴛᴇᴍᴘᴛs:</b> <code>{failed}</code>

<b>Bʀᴏᴀᴅᴄᴀsᴛ ID:</b> <code>{bc_id}</code>""",
    )


@new_task
async def broadcast(_, message):
    bc_id, forwarded, quietly, deleted, edited = "", False, False, False, False
    if not Config.DATABASE_URL:
        return await send_message(
            message, "DATABASE_URL Nᴏᴛ Pʀᴏᴠɪᴅᴇᴅ Tᴏ Fᴇᴛᴄʜ PM Uѕᴇʀs!"
        )
    rply = message.reply_to_message
    if len(message.command) > 1:
        if not message.command[1].startswith("-"):
            bc_id = (
                message.command[1] if bc_cache.get(message.command[1], False) else ""
            )
            if not bc_id:
                return await send_message(
                    message,
                    "<i>Bʀᴏᴀᴅᴄᴀsᴛ ID Nᴏᴛ Fᴏᴜɴᴅ! Aғᴛᴇʀ Rᴇsᴛᴀʀᴛ, Yᴏᴜ Cᴀɴ'ᴛ Eᴅɪᴛ Oʀ Dᴇʟᴇᴛᴇ Bʀᴏᴀᴅᴄᴀsᴛᴇᴅ Mᴇssᴀɢᴇs...</i>",
                )
        for arg in message.command:
            if arg in ["-f", "-forward"] and rply:
                forwarded = True
            if arg in ["-q", "-quiet"] and rply:
                quietly = True
            elif arg in ["-d", "-delete"] and bc_id:
                deleted = True
            elif arg in ["-e", "-edit"] and bc_id and rply:
                edited = True
    if not bc_id and not rply:
        return await send_message(
            message,
            """<b>Bʏ Rᴇᴘʟʏɪɴɢ Tᴏ Mᴇssᴀɢᴇ Tᴏ Bʀᴏᴀᴅᴄᴀsᴛ:</b>
/broadcast bc_id -d -e -f -q

<b>Fᴏʀᴡᴀʀᴅ Bʀᴏᴀᴅᴄᴀsᴛ Wɪᴛʜ Tᴀɢ:</b> -f Oʀ -forward
/cmd [reply_msg] -f

<b>Qᴜɪᴇᴛʟʏ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ:</b> -q Oʀ -quiet
/cmd [reply_msg] -q -f

<b>Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ:</b> -e Oʀ -edit
/cmd [reply_edited_msg] broadcast_id -e

<b>Dᴇʟᴇᴛᴇ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ:</b> -d Oʀ -delete
/bc broadcast_id -d

<b>Nᴏᴛᴇs:</b>
1. Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇs Cᴀɴ Bᴇ Oɴʟʏ Eᴅɪᴛᴇᴅ Oʀ Dᴇʟᴇᴛᴇᴅ Uɴᴛɪʟ Rᴇsᴛᴀʀᴛ.
2. Fᴏʀᴡᴀʀᴅᴇᴅ Mᴇssᴀɢᴇs Cᴀɴ'ᴛ Bᴇ Eᴅɪᴛᴇᴅ""",
        )
    if deleted:
        return await delete_broadcast(bc_id, message)
    elif edited:
        return await edit_broadcast(bc_id, message, rply)

    start_time = time()
    status = """<b><i>Bʀᴏᴀᴅᴄᴀsᴛ Sᴛᴀᴛs :</i></b>

<b>Tᴏᴛᴀʟ Uѕᴇʀs:</b> <code>{t}</code>
<b>Sᴜᴄᴄᴇss:</b> <code>{s}</code>
<b>Bʟᴏᴄᴋᴇᴅ Uѕᴇʀs:</b> <code>{b}</code>
<b>Dᴇʟᴇᴛᴇᴅ Aᴄᴄᴏᴜɴᴛs:</b> <code>{d}</code>
<b>Uɴsᴜᴄᴄᴇss Aᴛᴛᴇᴍᴘᴛ:</b> <code>{u}</code>"""
    updater = time()
    bc_hash, bc_msgs = token_hex(5), []
    pls_wait = await send_message(message, status.format(t=0, s=0, b=0, d=0, u=0))
    t, s, b, d, u = 0, 0, 0, 0, 0
    for uid in await database.get_pm_uids():
        bc_msg = None
        try:
            bc_msg = (
                await rply.forward(uid, disable_notification=quietly)
                if forwarded
                else await rply.copy(uid, disable_notification=quietly)
            )
            s += 1
        except FloodWait as e:
            await sleep(e.value * 1.1)
            bc_msg = (
                await rply.forward(uid, disable_notification=quietly)
                if forwarded
                else await rply.copy(uid, disable_notification=quietly)
            )
            s += 1
        except UserIsBlocked:
            await database.rm_pm_user(uid)
            b += 1
        except InputUserDeactivated:
            await database.rm_pm_user(uid)
            d += 1
        except Exception as e:
            print(f"Error broadcasting message to user {uid}: {e}")
            u += 1
        if bc_msg:
            bc_msgs.append((uid, bc_msg.id))
        t += 1
        if (time() - updater) > 10:
            await edit_message(pls_wait, status.format(t=t, s=s, b=b, d=d, u=u))
            updater = time()
    bc_cache[bc_hash] = bc_msgs
    await edit_message(
        pls_wait,
        f"{status.format(t=t, s=s, b=b, d=d, u=u)}\n\n<b>Eʟᴀᴘsᴇᴅ Tɪᴍᴇ:</b> <code>{get_readable_time(time() - start_time)}</code>\n<b>Bʀᴏᴀᴅᴄᴀsᴛ ID:</b> <code>{bc_hash}</code>",
    )
