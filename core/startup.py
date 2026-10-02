from bot import LOGGER, user_data
from helpers.db import database


async def load_user_data():
    if database._return:
        LOGGER.warning("Database is not connected. Skipping user data.")
        return

    if database.db is None:
        LOGGER.warning("Database is unavailable. Skipping user data.")
        return

    try:
        users = database.db.users.find({})

        count = 0

        async for data in users:
            user_id = data.pop("_id", None)

            if user_id is None:
                continue

            user_data[user_id] = data
            count += 1

        LOGGER.info(f"Users Data imported from MongoDB: {count}")

    except Exception as e:
        LOGGER.error(
            f"Error loading users data from MongoDB: {e}",
            exc_info=True
        )