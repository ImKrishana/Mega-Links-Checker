from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError
from pymongo.server_api import ServerApi

from core.config_manager import Config
from bot import LOGGER, user_data


class DbManager:
    def __init__(self):
        self._return = True
        self._conn = None
        self.db = None

    async def connect(self):
        try:
            if self._conn is not None:
                await self._conn.close()

            self._conn = AsyncMongoClient(
                Config.DATABASE_URL,
                server_api=ServerApi("1")
            )
            self.db = self._conn.thezake
            self._return = False

        except PyMongoError as e:
            LOGGER.error(f"Error in DB connection: {e}")
            self.db = None
            self._return = True
            self._conn = None

    async def disconnect(self):
        self._return = True

        if self._conn is not None:
            await self._conn.close()

        self._conn = None

    async def set_pm_users(self, user_id):
        if self._return:
            return

        if not bool(await self.db.pm_users.find_one({"_id": user_id})):
            await self.db.pm_users.insert_one({"_id": user_id})
            LOGGER.info(f"New PM User Added : {user_id}")

    async def get_pm_uids(self):
        if self._return:
            return

        return [doc["_id"] async for doc in self.db.pm_users.find({})]

    async def rm_pm_user(self, user_id):
        if self._return:
            return

        await self.db.pm_users.delete_one({"_id": user_id})

    async def update_user_data(self, user_id):
        if self._return:
            return

        data = user_data.get(user_id, {}).copy()

        await self.db.users.update_one(
            {"_id": user_id},
            {"$set": data},
            upsert=True
        )


database = DbManager()
