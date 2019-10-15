from django.db import models


class Settings(models.Model):
    allow_be = models.BooleanField(default=True)
    allow_uk = models.BooleanField(default=True)
    allow_ru = models.BooleanField(default=True)


class TelegramUser(models.Model):
    user_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=64, null=False)
    last_name = models.CharField(max_length=64, null=True)
    username = models.CharField(max_length=32, null=True)
    settings = models.ForeignKey(Settings, on_delete=models.DO_NOTHING, null=True)


class PostedBook(models.Model):
    book_id = models.IntegerField(default=False, null=False)
    file_type = models.CharField(max_length=4, default=False, null=False)
    file_id = models.CharField(primary_key=True, max_length=64, default=False, null=False)
