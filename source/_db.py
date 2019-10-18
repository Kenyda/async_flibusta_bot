import pathlib
from abc import ABC
from typing import Type, Union

import asyncpg
from aiogram.types import User, CallbackQuery

from config import Config


async def prepare_db():
    pool = await asyncpg.create_pool()  # TODO: add args

    for _class in [TablesCreator, TelegramUserDB, SettingDB, PostedBookDB]:  # type: Type[ConfugrableDB]
        _class.configurate(pool)

SQL_FOLDER = pathlib.Path("./sql")


class ConfigurableDB(ABC):
    pool: asyncpg.pool.Pool

    @classmethod
    def configurate(cls, pool: asyncpg.pool.Pool):
        cls.pool = pool


class TablesCreator(ConfigurableDB):
    CREATE_TELEGRAM_USER_TABLE = open(SQL_FOLDER / "create_telegram_user_table.sql").read().format(Config.DB_USER)
    CREATE_SETTING_TABLE = open(SQL_FOLDER / "create_setting_table.sql").read().format(Config.DB_USER)
    CREATE_POSTED_BOOK_TABLE = open(SQL_FOLDER / "create_posted_book_table.sql").read().format(Config.DB_USER)

    @classmethod
    async def create_telegram_user_table(cls):
        async with cls.pool.acquire() as conn:
            await conn.execute(cls.CREATE_TELEGRAM_USER_TABLE)

    @classmethod
    async def create_setting_table(cls):
        async with cls.pool.acquire() as conn:
            await conn.execute(cls.CREATE_SETTING_TABLE)

    @classmethod
    async def create_posted_book_table(cls):
        async with cls.pool.acquire() as conn:
            await conn.execute(cls.CREATE_POSTED_BOOK_TABLE)

    @classmethod
    async def create_tables(cls):
        await cls.create_telegram_user_table()
        await cls.create_setting_table()
        await cls.create_posted_book_table()


class TelegramUserDB(ConfigurableDB):
    @classmethod
    async def create_or_update(cls, obj: Union[User, CallbackQuery]):
        pass


class SettingDB(ConfigurableDB):
    @classmethod
    async def get_or_create(cls):
        pass

    @classmethod
    async def update(cls):
        pass


class PostedBookDB(ConfigurableDB):
    @classmethod
    async def get(cls):
        pass

    @classmethod
    async def create_or_update(cls):
        pass
