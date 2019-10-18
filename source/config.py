import fire


class Config:
    BOT_TOKEN: str

    BOT_NAME: str

    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int

    FLIBUSTA_SERVER: str
    FLIBUSTA_SERVER_PUBLIC: str

    WEBHOOK_PORT: int
    WEBHOOK_HOST: str

    SERVER_HOST: str
    SERVER_PORT: int

    REDIS_HOST: str
    REDIS_PASSWORD: str
    
    FLIBUSTA_BOOKS_CHANNEL_ID: str

    CHATBASE_API_KEY: str

    def __init__(self, token: str, bot_name: str,
                 db_password: str,
                 flibusta_server_public: str,
                 server_port: int,
                 redis_host: str,
                 redis_password: str,
                 chatbase_api_key: str,
                 webhook_port: int = 8443, server_host: str = "localhost",
                 flibusta_server: str = "http://localhost:7770",
                 db_host: str = "localhost", db_port: int = 5432,
                 flibusta_books_channel_id=None):
        Config.BOT_TOKEN = token

        Config.BOT_NAME = bot_name

        Config.DB_NAME = Config.BOT_NAME
        Config.DB_USER = Config.BOT_NAME
        Config.DB_PASSWORD = db_password
        Config.DB_HOST = db_host
        Config.DB_PORT = db_port

        Config.FLIBUSTA_SERVER = flibusta_server
        Config.FLIBUSTA_SERVER_PUBLIC = flibusta_server_public

        Config.WEBHOOK_HOST = f"https://kurbezz.ru:{self.WEBHOOK_PORT}/{self.BOT_NAME}"
        Config.WEBHOOK_PORT = webhook_port

        Config.SERVER_HOST = server_host
        Config.SERVER_PORT = server_port

        Config.REDIS_HOST = redis_host
        Config.REDIS_PASSWORD = redis_password

        Config.FLIBUSTA_BOOKS_CHANNEL_ID = flibusta_books_channel_id

        Config.CHATBASE_API_KEY = chatbase_api_key


fire.Fire(Config)
