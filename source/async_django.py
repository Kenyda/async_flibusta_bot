import os
from typing import List, Union

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

application = get_wsgi_application()

from db.models import *

from aioify import aioify
from aiogram import types


def _update_user(msg: Union[types.Message, types.CallbackQuery]):
    if isinstance(msg, types.Message) or isinstance(msg, types.CallbackQuery):
        TelegramUser.objects.update_or_create(
            user_id=msg.from_user.id, 
            defaults={
                'first_name': msg.from_user.first_name,
                'last_name': msg.from_user.last_name,
                'username': msg.from_user.username
            }
        )

update_user = aioify(_update_user)


def _delete_posted_book(type_: str, id_: int):
    try:
        PostedBook.objects.filter(file_type=type_, book_id=id_).delete()
    except ObjectDoesNotExist:
        pass

delete_posted_book = aioify(_delete_posted_book)


def _get_allowed_langs(user_id: int) -> List[str]:
    user = TelegramUser.objects.get_or_create(user_id=user_id)[0]
    if user.settings is None:
        return ["uk", "be", "ru"]

    allowed_langs = []
    if user.settings.allow_uk:
        allowed_langs.append("uk")
    if user.settings.allow_be:
        allowed_langs.append("be")
    if user.settings.allow_ru:
        allowed_langs.append("ru")
    return allowed_langs

get_allowed_langs = aioify(_get_allowed_langs)


def _get_posted_book(book_id: int, file_type: str) -> None:
    try:
        return PostedBook.objects.get(book_id=book_id, file_type=file_type)
    except MultipleObjectsReturned:
        PostedBook.objects.filter(book_id=book_id, file_type=file_type).delete()
        raise ObjectDoesNotExist

get_posted_book = aioify(_get_posted_book)


def _create_posted_book(book_id: int, file_type: str, file_id: str) -> None:
    PostedBook.objects.create(book_id=book_id, file_type=file_type, file_id=file_id).save()

create_posted_book = aioify(_create_posted_book)


def _get_telegram_user_settings(user_id: int) -> Settings:
    user = TelegramUser.objects.get(user_id=user_id)
    if user.settings is None:
        user.settings = Settings.objects.create()
        user.settings.save()
        user.save()
    return user.settings


get_telegram_user_settings = aioify(_get_telegram_user_settings)


def _save_settings(settings) -> None:
    settings.save()

save_settings = aioify(_save_settings)
