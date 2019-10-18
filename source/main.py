import re

from aiogram import Bot, Dispatcher, types, filters, exceptions
from aiogram.utils.executor import start_webhook

import analytics
import strings
from filters import CallbackDataRegExFilter, InlineQueryRegExFilter, IsTextMessageFilter
from config import Config
from flibusta_server import Book, NoContent
from send import Sender
from async_django import update_user, get_telegram_user_settings, save_settings
from utils import ignore, make_settings_keyboard


bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher(bot)

Sender.configure(bot)


@dp.message_handler(commands=["start"])
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def start_handler(msg: types.Message):
    await update_user(msg)
    try:
        await analytics.analyze(msg.text, "get_shared_book", msg.from_user.id)
        file_type, book_id = (msg["text"].split(' ')[1].split("_"))
        await Sender.send_book(msg, int(book_id), file_type)
    except (ValueError, IndexError):
        await analytics.analyze(msg.text, "start", msg.from_user.id)
        await msg.reply(strings.start_message.format(name=msg.from_user.first_name))


@dp.message_handler(commands=["help"])
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def help_handler(msg: types.Message):
    async with analytics.Analyze("help", msg):
        await msg.reply(strings.help_msg)


@dp.message_handler(commands=["info"])
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def info_handler(msg: types.Message):
    async with analytics.Analyze("info", msg):
        await msg.reply(strings.info_msg, disable_web_page_preview=True)


@dp.message_handler(commands=["vote"])
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def vote_handler(msg: types.Message):
    async with analytics.Analyze("vote", msg):
        await msg.reply(strings.vote_msg)


@dp.message_handler(commands=["settings"])
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def settings(msg: types.Message):
    async with analytics.Analyze("settings", msg):
        await update_user(msg)
        await msg.reply("Настройки: ", reply_markup=await make_settings_keyboard(msg.from_user.id))


@dp.callback_query_handler(CallbackDataRegExFilter(r"^(ru|uk|be)_(on|off)$"))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def lang_setup(query: types.CallbackQuery):
    async with analytics.Analyze("settings_change", query):
        await update_user(query)
        settings = await get_telegram_user_settings(query.message.chat.id)
        lang, set_ = query.data.split('_')
        if lang == "uk":
            settings.allow_uk = (set_ == "on")
        if lang == "be":
            settings.allow_be = (set_ == "on")
        if lang == "ru":
            settings.allow_ru = (set_ == "on")
        await save_settings(settings)
        keyboard = await make_settings_keyboard(query.from_user.id)
        await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                            reply_markup=keyboard)


@dp.message_handler(regexp=re.compile('^/a_([0-9]+)$'))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
@ignore(exceptions.MessageCantBeEdited)
async def search_books_by_author(msg: types.Message):
    async with analytics.Analyze("get_books_by_author", msg):
        await update_user(msg)
        await Sender.search_books_by_author(msg, int(msg.text.split('_')[1]), 1)


@dp.message_handler(regexp=re.compile('^/s_([0-9]+)$'))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.MessageCantBeEdited)
async def search_book_by_series(msg: types.Message):
    async with analytics.Analyze("get_book_by_series", msg):
        await update_user(msg)
        await Sender.search_books_by_series(msg, int(msg.text.split("_")[1]), 1)


@dp.message_handler(commands=['random_book'])
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def get_random_book(msg: types.Message):
    async with analytics.Analyze("get_random_book", msg):
        await update_user(msg)
        await Sender.get_random_book(msg)


@dp.message_handler(commands=['random_author'])
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def get_random_author(msg: types.Message):
    async with analytics.Analyze("get_random_author", msg):
        await update_user(msg)
        await Sender.get_random_author(msg)


@dp.message_handler(commands=["random_series"])
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def get_random_series(msg: types.Message):
    async with analytics.Analyze("get_random_series", msg):
        await update_user(msg)
        await Sender.get_random_sequence(msg)


@dp.message_handler(commands=['donate'])
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def donation(msg: types.Message):
    async with analytics.Analyze("donation", msg):
        await msg.reply(strings.donate_msg, parse_mode='HTML')


@dp.message_handler(regexp=re.compile('^/(fb2|epub|mobi|djvu|pdf|doc)_[0-9]+$'))
@ignore(exceptions.BotBlocked)
async def get_book_handler(msg: types.Message):
    async with analytics.Analyze("download", msg):
        file_type, book_id = msg.text.replace('/', '').split('_')
        await Sender.send_book(msg, int(book_id), file_type)


@dp.message_handler(regexp=re.compile("^/b_info_[0-9]+$"))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def get_book_annotation(msg: types.Message):
    async with analytics.Analyze("book_annotation", msg):
        book_id = int(msg.text.split("/b_info_")[1])
        await Sender.send_book_annotation(msg, book_id)


@dp.message_handler(regexp=re.compile("^/a_info_[0-9]+$"))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def get_author_annotation(msg: types.Message):
    async with analytics.Analyze("author_annotation", msg):
        author_id = int(msg.text.split("/a_info_")[1])
        await Sender.send_author_annotation(msg, author_id)


@dp.message_handler(IsTextMessageFilter())
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def search(msg: types.Message):
    async with analytics.Analyze("new_search_query", msg):
        await update_user(msg)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("По названию", callback_data="b_1")
        )
        keyboard.row(
            types.InlineKeyboardButton("По авторам", callback_data="a_1"),
            types.InlineKeyboardButton("По сериям", callback_data="s_1")
        )
    await msg.reply("Поиск: ", reply_markup=keyboard)

@dp.callback_query_handler(CallbackDataRegExFilter(r'^b_([0-9]+)'))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
@ignore(exceptions.MessageCantBeEdited)
async def search_books_by_title(callback: types.CallbackQuery):
    async with analytics.Analyze("search_book_by_title", callback):
        msg: types.Message = callback.message
        if not msg.reply_to_message or not msg.reply_to_message.text:
            return await msg.reply("Ошибка :( Попробуйте еще раз!")
        await Sender.search_books(msg, int(callback.data.split('_')[1]))


@dp.callback_query_handler(CallbackDataRegExFilter(r'^a_([0-9]+)'))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
@ignore(exceptions.MessageCantBeEdited)
async def search_authors(callback: types.CallbackQuery):
    async with analytics.Analyze("search_authors", callback):
        msg: types.Message = callback.message
        if not msg.reply_to_message or not msg.reply_to_message.text:
            return await msg.reply("Ошибка :( Попробуйте еще раз!")
        await Sender.search_authors(msg, int(callback.data.split('_')[1]))


@dp.callback_query_handler(CallbackDataRegExFilter('^s_([0-9]+)'))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
@ignore(exceptions.MessageCantBeEdited)
async def search_series(callback: types.CallbackQuery):
    async with analytics.Analyze("search_series", callback):
        msg: types.Message = callback.message
        if not msg.reply_to_message or not msg.reply_to_message.text:
            return await msg.reply("Ошибка :( Попробуйте еще раз!")
        await Sender.search_series(msg, int(callback.data.split('_')[1]))


@dp.callback_query_handler(CallbackDataRegExFilter(r'^ba_([0-9]+)'))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
@ignore(exceptions.MessageCantBeEdited)
async def get_books_by_author(callback: types.CallbackQuery):
    async with analytics.Analyze("get_books_by_author", callback):
        msg: types.Message = callback.message
        if not msg.reply_to_message or not msg.reply_to_message.text:
            return await msg.reply("Ошибка :( Попробуйте еще раз!")
        await update_user(msg.reply_to_message)
        await Sender.search_books_by_author(msg, int(msg.reply_to_message.text.split('_')[1]),
                                            int(callback.data.split('_')[1]))


@dp.callback_query_handler(CallbackDataRegExFilter(r'^bs_([0-9]+)'))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
@ignore(exceptions.MessageCantBeEdited)
async def get_books_by_series(callback: types.CallbackQuery):
    async with analytics.Analyze("get_books_by_series", callback):
        msg: types.Message = callback.message
        if not msg.reply_to_message or not msg.reply_to_message.text:
            return await msg.reply("Ошибка :( Попробуйте еще раз!")
        await update_user(msg.reply_to_message)
        await Sender.search_books_by_series(msg, int(msg.reply_to_message.text.split("_")[1]),
                                            int(callback.data.split('_')[1]))


@dp.callback_query_handler(CallbackDataRegExFilter('remove_cache'))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.BadRequest)
async def remove_cache(callback: types.CallbackQuery):
    async with analytics.Analyze("remove_cache", callback):
        await bot.send_message(callback.from_user.id, strings.cache_removed)
        reply_to: types.Message = callback.message.reply_to_message
        file_type, book_id = reply_to.text.replace('/', '').split('_')
        await Sender.remove_cache(file_type, int(book_id))
        await Sender.send_book(reply_to, int(book_id), file_type)


@dp.inline_handler(InlineQueryRegExFilter(r'^share_([\d]+)$'))
@ignore(exceptions.BotBlocked)
@ignore(exceptions.InvalidQueryID)
@ignore(NoContent)
async def share_book(query: types.InlineQuery):
    async with analytics.Analyze("share_book", query):
        book_id = int(query.query.split("_")[1])
        book = await Book.get_by_id(book_id)
        await bot.answer_inline_query(query.id, [types.InlineQueryResultArticle(
            id=str(query.query),
            title=strings.share,
            description=book.short_info,
            input_message_content=types.InputTextMessageContent(
                book.share_text,
                parse_mode="markdown",
                disable_web_page_preview=True
            )
        )])


async def on_startup(dp):
    await bot.set_webhook(Config.WEBHOOK_HOST + "/")


async def on_shutdown(dp):
    await bot.delete_webhook()


if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path="/",
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=False,
        host=Config.SERVER_HOST,
        port=Config.SERVER_PORT
    )
    # executor.start_polling(dp, skip_updates=False)
