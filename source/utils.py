import asyncio
from aiogram import types
from async_django import get_telegram_user_settings

from functools import wraps


def ignore(exception):
    def ignore(fn):
        if asyncio.iscoroutinefunction(fn):
            @wraps(fn)
            async def wrapper(*args, **kwargs):
                try:
                    return await fn(*args, **kwargs)
                except exception:
                    pass
            return wrapper
        else:
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except exception:
                    pass
            return wrapper
    return ignore


async def make_settings_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
    settings = await get_telegram_user_settings(user_id)
    keyboard = types.InlineKeyboardMarkup()
    if not settings.allow_ru:
        keyboard.row(types.InlineKeyboardButton("Русский: 🅾 выключен!", callback_data="ru_on"))
    else:
        keyboard.row(types.InlineKeyboardButton("Русский: ✅ включен!", callback_data="ru_off"))
    if not settings.allow_uk:
        keyboard.row(types.InlineKeyboardButton("Украинский: 🅾 выключен!", callback_data="uk_on"))
    else:
        keyboard.row(types.InlineKeyboardButton("Украинский: ✅ включен!", callback_data="uk_off"))
    if not settings.allow_be:
        keyboard.row(types.InlineKeyboardButton("Белорусский: 🅾 выключен!", callback_data="be_on"))
    else:
        keyboard.row(types.InlineKeyboardButton("Белорусский: ✅ включен!", callback_data="be_off"))
    return keyboard
