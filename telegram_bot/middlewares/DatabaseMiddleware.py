import os

import asyncpg
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from dotenv import load_dotenv

load_dotenv()


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.pool = None

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
                database=os.environ["DB_NAME"],
                host=os.environ["DB_HOST"],
                port=os.environ["DB_PORT"],
            )
        data["pool"] = self.pool

        return await handler(event, data)

    def get_pool(self):
        return self.pool
