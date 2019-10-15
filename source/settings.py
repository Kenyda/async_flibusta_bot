import os
import fire
from config import Config


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '$^brfavtsdes0&-_**1vy8+7g_)*c)%k%7%a#irr-fg6jvpyk#'

INSTALLED_APPS = (
    'db',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': Config.DB_NAME,
        'USER': Config.DB_USER,
        'PASSWORD': Config.DB_PASSWORD,
        'HOST': Config.DB_HOST,
        'PORT': Config.DB_PORT
    }
}
