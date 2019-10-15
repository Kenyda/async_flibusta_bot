import re

from aiogram import filters
from aiogram.types import Message, CallbackQuery


class CallbackDataRegExFilter(filters.Filter):
    def __init__(self, reg_exp_query: str):
        self.pattern = re.compile(reg_exp_query)

    async def check(self, callback) -> bool:
        return self.pattern.match(callback.data) is not None


class InlineQueryRegExFilter(filters.Filter):
    def __init__(self, reg_exp_query: str):
        self.pattern = re.compile(reg_exp_query)

    async def check(self, query: CallbackQuery) -> bool:
        return self.pattern.match(query.query) is not None


class IsTextMessageFilter(filters.Filter):
    async def check(self, message: Message) -> bool:
        return message.text is not None
