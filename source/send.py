import typing
from typing import Optional
from functools import wraps
from datetime import date

import transliterate as transliterate
from aiogram import Bot, types, exceptions
from aiogram.bot import api
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, base
from aiogram.utils.payload import prepare_file, prepare_arg, generate_payload
import aioredis
from flibusta_server import Book, Author, Sequence, BookAnnotation, NoContent, AuthorAnnotation, UpdateLog
from notifier import Notifier

from config import Config

from db import *

ELEMENTS_ON_PAGE = 7
BOOKS_CHANGER = 5


async def get_keyboard(page: int, pages_count: int, keyboard_type: str) -> Optional[InlineKeyboardMarkup]:
    if pages_count == 1:
        return None
    keyboard = InlineKeyboardMarkup()

    first_row = []
    second_row = []

    if page > 1:
        prev_page = max(1, page - BOOKS_CHANGER)
        if prev_page != page - 1:
            second_row.append(InlineKeyboardButton(f'<< {prev_page}',
                                                   callback_data=f'{keyboard_type}_{prev_page}'))
        first_row.append(InlineKeyboardButton('<', callback_data=f'{keyboard_type}_{page - 1}'))

    if page != pages_count:
        next_page = min(pages_count, page + BOOKS_CHANGER)
        if next_page != page + 1:
            second_row.append(InlineKeyboardButton(f'>> {next_page}',
                                                   callback_data=f'{keyboard_type}_{next_page}'))
        first_row.append(InlineKeyboardButton('>', callback_data=f'{keyboard_type}_{page + 1}'))

    keyboard.row(*first_row)
    keyboard.row(*second_row)

    return keyboard


async def normalize(book: Book, file_type: str) -> str:  # remove chars that don't accept in Telegram Bot API
    filename = '_'.join([a.short for a in book.authors]) + '_-_' if book.authors else ''
    filename += book.title if book.title[-1] != ' ' else book.title[:-1]
    filename = transliterate.translit(filename, 'ru', reversed=True)

    for c in "(),….’!\"?»«':":
        filename = filename.replace(c, '')

    for c, r in (('—', '-'), ('/', '_'), ('№', 'N'), (' ', '_'), ('–', '-'), ('á', 'a'), (' ', '_')):
        filename = filename.replace(c, r)

    return filename + '.' + file_type


def need_one_or_more_langs(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        msg = None
        for a in args:
            if isinstance(a, Message):
                msg = a
                break
        if msg is None:
            raise Exception("Message not found!")
        allowed_langs = (await SettingsDB.get(msg.chat.id)).get()
        if not allowed_langs:
            return await Sender.try_reply_or_send_message(msg.chat.id, "Нужно выбрать хотя бы один язык! /settings",
                                                          reply_to_message_id=msg.message_id)
        return await fn(*args, **kwargs)
    return wrapper


class Sender:
    bot: Bot
    redis_connection: aioredis.Redis

    @classmethod
    def configure(cls, bot: Bot):
        cls.bot = bot
        cls.redis_connection = None

    @classmethod
    async def get_redis_connection(cls):
        if not cls.redis_connection:
            cls.redis_connection = await aioredis.create_redis(Config.REDIS_HOST, password=Config.REDIS_PASSWORD)
        return cls.redis_connection

    @classmethod
    async def send_document(cls, chat_id: typing.Union[base.Integer, base.String],
                            document: typing.Union[base.InputFile, base.String],
                            filename: str = 'document',
                            thumb: typing.Union[base.InputFile, base.String, None] = None,
                            caption: typing.Union[base.String, None] = None,
                            parse_mode: typing.Union[base.String, None] = None,
                            disable_notification: typing.Union[base.Boolean, None] = None,
                            reply_to_message_id: typing.Union[base.Integer, None] = None,
                            reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                       types.ReplyKeyboardMarkup,
                                                       types.ReplyKeyboardRemove,
                                                       types.ForceReply, None] = None) -> types.Message:
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=[filename])
        if cls.bot.parse_mode:
            payload.setdefault('parse_mode', cls.bot.parse_mode)

        files = {filename: document}
        prepare_file(payload, files, filename, document)

        result = await cls.bot.request(api.Methods.SEND_DOCUMENT, payload, files)
        return types.Message(**result)
    
    @classmethod
    async def try_reply_or_send_message(cls, *args, **kwargs):
        try:
            return await cls.bot.send_message(*args, **kwargs)
        except exceptions.BadRequest:
            kwargs.pop('reply_to_message_id')
            return await cls.bot.send_message(*args, **kwargs)

    @classmethod
    async def try_reply_or_send_photo(cls, *args, **kwargs):
        try:
            return await cls.bot.send_photo(*args, **kwargs)
        except exceptions.BadRequest:
            kwargs.pop('reply_to_message_id')
            return await cls.bot.send_photo(*args, **kwargs)

    @staticmethod
    async def remove_cache(type_: str, id_: int):
        await PostedBookDB.delete(id_, type_)

    @classmethod
    async def send_book(cls, msg: Message, book_id: int, file_type: str):
        async with Notifier(cls.bot, msg.chat.id, "upload_document"):
            try:
                book = await Book.get_by_id(book_id)
            except NoContent:
                await msg.reply("Книга не найдена!")
                return
            redis = await cls.get_redis_connection()
            msg_id = await redis.hget(book_id, file_type)
            if msg_id:
                try:
                    book_msg = await cls.bot.forward_message(chat_id=msg.chat.id,
                                                   from_chat_id=Config.FLIBUSTA_BOOKS_CHANNEL_ID,
                                                   message_id=int(msg_id))
                    return await book_msg.reply(book.caption, reply_markup=book.share_markup_without_cache)
                except exceptions.MessageToForwardNotFound:
                    pass  # ToDO: remove message from redis
            pb = await PostedBookDB.get(book_id, file_type)
            if pb:
                try:
                    await cls.bot.send_document(msg.chat.id, pb.file_id, reply_to_message_id=msg.message_id,
                                                 caption=book.caption, reply_markup=book.share_markup)
                except exceptions.BadRequest:
                    await cls.bot.send_document(msg.chat.id, pb.file_id,
                                                 caption=book.caption, reply_markup=book.share_markup)
            else:
                book_bytes = await Book.download(book_id, file_type)
                if not book_bytes:
                    return await cls.try_reply_or_send_message(msg.chat.id, 
                                                               "Ошибка! Попробуйте позже :(",
                                                               reply_to_message_id=msg.message_id)
                if book_bytes.size > 50_000_000:
                    return await cls.try_reply_or_send_message(
                        msg.chat.id, 
                        book.download_caption(file_type), parse_mode="HTML",
                        reply_to_message_id=msg.message_id
                    )
                book_bytes.name = await normalize(book, file_type)
                try:
                    send_response = await cls.bot.send_document(msg.chat.id, book_bytes,
                                                                reply_to_message_id=msg.message_id,
                                                                caption=book.caption, reply_markup=book.share_markup)
                except exceptions.TelegramAPIError:
                    return await cls.try_reply_or_send_message(msg.chat.id,
                                                               "Ошибка! Попробуйте позже :(",
                                                               reply_to_message_id=msg.message_id)
                except exceptions.BadRequest:
                    book_bytes = book_bytes.get_copy()
                    send_response = await cls.bot.send_document(msg.chat.id, book_bytes,
                                                                caption=book.caption, reply_markup=book.share_markup)
                await PostedBookDB.create_or_update(book_id, file_type, send_response.document.file_id)

    @classmethod
    @need_one_or_more_langs
    async def search_books(cls, msg: Message, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        search_result = await Book.search(msg.reply_to_message.text,
                                          (await SettingsDB.get(msg.chat.id)).get(), 
                                          ELEMENTS_ON_PAGE, page)
        if not search_result:
            await cls.bot.edit_message_text('Книги не найдены!', chat_id=msg.chat.id, message_id=msg.message_id)
            return
        page_count = search_result.count // ELEMENTS_ON_PAGE + (1 if search_result.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = ''.join(book.to_send_book for book in search_result.books) \
                   + f'<code>Страница {page}/{page_count}</code>'
        await cls.bot.edit_message_text(msg_text, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='HTML',
                                         reply_markup=await get_keyboard(page, page_count, 'b'))

    @classmethod
    @need_one_or_more_langs
    async def search_authors(cls, msg: Message, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        search_result = await Author.search(msg.reply_to_message.text, 
                                            (await SettingsDB.get(msg.chat.id)).get(), 
                                            ELEMENTS_ON_PAGE, page)
        if not search_result:
            await cls.bot.edit_message_text('Автор не найден!', chat_id=msg.chat.id, message_id=msg.message_id)
            return
        page_max = search_result.count // ELEMENTS_ON_PAGE + (1 if search_result.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = ''.join(author.to_send for author in search_result.authors) \
                   + f'<code>Страница {page}/{page_max}</code>'
        await cls.bot.edit_message_text(msg_text, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='HTML',
                                        reply_markup=await get_keyboard(page, page_max, 'a'))

    @classmethod
    @need_one_or_more_langs
    async def search_books_by_author(cls, msg: Message, author_id: int, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        try:
            author = await Author.by_id(author_id, (await SettingsDB.get(msg.chat.id)).get(), ELEMENTS_ON_PAGE, page)
        except NoContent:
            return await msg.reply("Автор не найден!")
        books = author.books
        if not books:
            await msg.reply('Ошибка! Книги не найдены!')
            return
        page_max = author.count // ELEMENTS_ON_PAGE + (1 if author.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = f"<b>{author.normal_name}:</b>"
        if author.annotation_exists:
            msg_text += f"\nОб авторе: /a_info_{author.id}\n\n"
        else:
            msg_text += "\n\n"
        msg_text += ''.join([book.to_send_book_without_author for book in books]) + \
            f'<code>Страница {page}/{page_max}</code>'                   
        if not msg.reply_to_message:
            await cls.try_reply_or_send_message(msg.chat.id, msg_text, parse_mode='HTML', 
                                                reply_markup=await get_keyboard(1, page_max, 'ba'),
                                                reply_to_message_id=msg.message_id
            )
        else:
            await cls.bot.edit_message_text(msg_text, msg.chat.id, msg.message_id, parse_mode='HTML',
                                             reply_markup=await get_keyboard(page, page_max, 'ba'))

    @classmethod
    @need_one_or_more_langs
    async def search_series(cls, msg: Message, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        sequences_result = await Sequence.search(msg.reply_to_message.text, 
                                                 (await SettingsDB.get(msg.chat.id)).get(), 
                                                 ELEMENTS_ON_PAGE, page)
        if not sequences_result:
            return await cls.try_reply_or_send_message(msg.chat.id, 'Ошибка! Серии не найдены!',
                                                       reply_to_message_id=msg.message_id)
        page_max = sequences_result.count // ELEMENTS_ON_PAGE + (
            1 if sequences_result.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = ''.join([sequence.to_send for sequence in sequences_result.sequences[:5]]) \
                   + f'<code>Страница {page}/{page_max}</code>'
        await cls.bot.edit_message_text(msg_text, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='HTML',
                                         reply_markup=await get_keyboard(page, page_max, 's'))

    @classmethod
    @need_one_or_more_langs
    async def search_books_by_series(cls, msg: Message, series_id: int, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        search_result = await Sequence.get_by_id(series_id, (await SettingsDB.get(msg.chat.id)).get(), ELEMENTS_ON_PAGE, page)
        books = search_result.books
        if not books:
            return await cls.try_reply_or_send_message(msg.chat.id, 'Ошибка! Книги в серии не найдены!',
                                                       reply_to_message_id=msg.message_id)
        page_max = search_result.count // ELEMENTS_ON_PAGE + (1 if search_result.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = f"<b>{search_result.name}:</b>\n\n" + \
                   ''.join([book.to_send_book for book in books]
                           ) + f'<code>Страница {page}/{page_max}</code>'
        if not msg.reply_to_message:
            await cls.try_reply_or_send_message(msg.chat.id, msg_text, parse_mode='HTML', 
                                                reply_markup=await get_keyboard(1, page_max, 'bs'),
                                                reply_to_message_id=msg.message_id)
        else:
            await cls.bot.edit_message_text(msg_text, msg.chat.id, msg.message_id, parse_mode='HTML',
                                             reply_markup=await get_keyboard(page, page_max, 'bs'))

    @classmethod
    @need_one_or_more_langs
    async def get_random_book(cls, msg: Message):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        try:
            book = await Book.get_random((await SettingsDB.get(msg.chat.id)).get())
            await cls.try_reply_or_send_message(msg.chat.id, book.to_send_book, parse_mode='HTML',
                                                reply_to_message_id=msg.message_id)
        except NoContent:
            await cls.try_reply_or_send_message(msg.chat.id, "Пока бот не может это сделать, но скоро это исправят!")

    @classmethod
    @need_one_or_more_langs
    async def get_random_author(cls, msg: Message):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        try:
            author = await Author.get_random((await SettingsDB.get(msg.chat.id)).get())
            await cls.try_reply_or_send_message(msg.chat.id, author.to_send, parse_mode='HTML',
                                                reply_to_message_id=msg.message_id)
        except NoContent:
            await cls.try_reply_or_send_message(msg.chat.id, "Пока бот не может это сделать, но скоро это исправят!")

    @classmethod
    @need_one_or_more_langs
    async def get_random_sequence(cls, msg: Message):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        try:
            sequence = await Sequence.get_random((await SettingsDB.get(msg.chat.id)).get())
            await cls.try_reply_or_send_message(msg.chat.id, sequence.to_send, parse_mode="HTML",
                                                reply_to_message_id=msg.message_id)
        except NoContent:
            await cls.try_reply_or_send_message(msg.chat.id, "Пока бот не может это сделать, но скоро это исправят!")

    @classmethod
    @need_one_or_more_langs
    async def send_book_annotation(cls, msg: Message, book_id: int):
        try:
            await cls.bot.send_chat_action(msg.chat.id, 'typing')
            annotation = await BookAnnotation.get_by_book_id(book_id)
            if annotation.photo_link:
                msg = await cls.bot.send_photo(msg.chat.id, annotation.photo_link,
                                               caption=annotation.to_send[:1024], parse_mode="HTML",
                                               reply_to_message_id=msg.message_id)
                if len(annotation.to_send) > 1024:
                    i = 1024
                    while annotation.to_send[i:i + 4096]:
                        msg = await cls.try_reply_or_send_message(msg.chat.id, annotation.to_send[i:i+4096], parse_mode="HTML",
                                                                  reply_to_message_id=msg.message_id)
                        i += len(msg.text)
            else:
                msg = await cls.try_reply_or_send_message(msg.chat.id, annotation.to_send[:4096], parse_mode="HTML",
                                                          reply_to_message_id=msg.message_id)
                if len(annotation.to_send) > 4096:
                    i = 4096
                    while annotation.to_send[i:i + 4096]:
                        msg = await cls.try_reply_or_send_message(msg.chat.id, annotation.to_send[i:i+4096], parse_mode="HTML",
                                                                  reply_to_message_id=msg.message_id)
                        i += len(msg.text)
        except NoContent:
            await cls.try_reply_or_send_message(msg.chat.id, "Нет аннотации для этой книги!",
                                                reply_to_message_id=msg.message_id)


    @classmethod
    @need_one_or_more_langs
    async def send_author_annotation(cls, msg: Message, author_id: int):
        try:
            await cls.bot.send_chat_action(msg.chat.id, 'typing')
            annotation = await AuthorAnnotation.get_by_author_id(author_id)
            if annotation.photo_link:
                await cls.try_reply_or_send_photo(msg.chat.id, annotation.photo_link,
                                                  caption=annotation.to_send[:1024], parse_mode="HTML",
                                                  reply_to_message_id=msg.message_id)
                if len(annotation.to_send) > 1024:
                    i = 1024
                    while annotation.to_send[i:i + 4096]:
                        msg = await cls.try_reply_or_send_message(msg.chat.id, annotation.to_send[i:i+4096], parse_mode="HTML",
                                                                  reply_to_message_id=msg.message_id)
                        i += len(msg.text)
            else:
                await cls.try_reply_or_send_message(msg.chat.id, annotation.to_send[:4096], parse_mode="HTML",
                                                    reply_to_message_id=msg.message_id)
                if len(annotation.to_send) > 4096:
                    i = 4096
                    while annotation.to_send[i:i + 4096]:
                        msg = await cls.try_reply_or_send_message(msg.chat.id, annotation.to_send[i:i+4096], parse_mode="HTML",
                                                                  reply_to_message_id=msg.message_id)
                        i += len(msg.text)
        except NoContent:
            await cls.try_reply_or_send_message(msg.chat.id, "Нет информации для этого автора!",
                                                reply_to_message_id=msg.message_id)


    @classmethod
    @need_one_or_more_langs
    async def send_day_update_log(cls, msg: types.Message, day: date, page: int):
        update_log = await UpdateLog.get_by_day(day, (await SettingsDB.get(msg.chat.id)).get(), 7, page)
        if not update_log:
            await cls.bot.edit_message_text('Обновления не найдены!', chat_id=msg.chat.id, message_id=msg.message_id)
            return
        page_count = update_log.count // ELEMENTS_ON_PAGE + (1 if update_log.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = f'Обновления за {day.isoformat()}\n\n'
        msg_text += ''.join(book.to_send_book for book in update_log.books) \
                   + f'<code>Страница {page}/{page_count}</code>'
        await cls.bot.edit_message_text(msg_text, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='HTML',
                                        reply_markup=await get_keyboard(page, page_count, f'ul_d_{day.isoformat()}'))
