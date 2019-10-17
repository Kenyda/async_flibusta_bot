import pathlib

import asyncpg

from config import Config


SQL_FOLDER = pathlib.Path("./sql")


class Requests:
    create_telegram_user_table = open(SQL_FOLDER / "create_telegram_user_table.sql").read().format(Config.DB_USER)
    create_setting_table = open(SQL_FOLDER / "create_setting_table.sql").read().format(Config.DB_USER)
    create_posted_book_table = open(SQL_FOLDER / "create_posted_book_table.sql").read().format(Config.DB_USER)


async def create_telegram_user_table(pool: asyncpg.pool.Pool):
    async with pool.acquire() as conn:
        await conn.execute(Requests.create_telegram_user_table)


async def create_setting_table(pool: asyncpg.pool.Pool):
    async with pool.acquire() as conn:
        await conn.execute(Requests.create_setting_table)


async def create_posted_book_table(pool: asyncpg.pool.Pool):
    async with pool.acquire() as conn:
        await conn.execute(Requests.create_posted_book_table)


async def create_tables(pool: asyncpg.pool.Pool):
    await create_telegram_user_table(pool)
    await create_setting_table(pool)
    await create_posted_book_table(pool)


class TelegramUserDB:
    pass


class SettingDB:
    pass


class PostedBookDB:
    pass
