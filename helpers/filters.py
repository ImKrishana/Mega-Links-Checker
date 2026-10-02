from time import time

from pyrogram.filters import create

from bot import auth_chats, user_data
from core.config_manager import Config

def _source_message(update):
    return getattr(update, "message", None) or update


def _chat_context(update):
    message = _source_message(update)
    chat = getattr(message, "chat", None)

    if chat is None:
        return None, None

    thread_id = (
        message.message_thread_id
        if getattr(message, "is_topic_message", False)
        else None
    )

    return chat.id, thread_id


class CustomFilters:

    async def owner_filter(self, _, update):
        user = update.from_user or update.sender_chat
        return user.id == Config.OWNER_ID

    owner = create(owner_filter)

    async def authorized_user(self, _, update):
        uid = (update.from_user or update.sender_chat).id
        chat_id, thread_id = _chat_context(update)

        return bool(
            uid == Config.OWNER_ID
            or (
                uid in user_data
                and (
                    user_data[uid].get("AUTH", False)
                    or user_data[uid].get("SUDO", False)
                )
            )
            or (
                chat_id in user_data
                and user_data[chat_id].get("AUTH", False)
                and (
                    thread_id is None
                    or thread_id in user_data[chat_id].get("thread_ids", [])
                )
            )
            or uid in auth_chats
            or (
                chat_id in auth_chats
                and (
                    (
                        auth_chats[chat_id]
                        and thread_id
                        and thread_id in auth_chats[chat_id]
                    )
                    or not auth_chats[chat_id]
                )
            )
        )

    authorized = create(authorized_user)

    async def blacklisted_user(self, _, update):
        uid = (update.from_user or update.sender_chat).id

        if uid not in user_data:
            return False

        bl = user_data[uid].get("BLACKLIST", False)

        if not bl:
            return False

        if bl is True:
            return True

        if isinstance(bl, (int, float)):
            if bl > time():
                return True

            user_data[uid]["BLACKLIST"] = False

        return False

    blacklisted = create(blacklisted_user)
