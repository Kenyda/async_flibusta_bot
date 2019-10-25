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

    DSN: str

    @classmethod
    def configurate(cls, token: str, bot_name: str,
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
        cls.BOT_TOKEN = token
        cls.BOT_NAME = bot_name
        
        cls.DB_NAME = cls.DB_USER = bot_name
        cls.DB_PASSWORD = db_password
        cls.DB_HOST = db_host
        cls.DB_PORT = db_port
        cls.DSN = f"postgresql://{cls.DB_HOST}:5432/{cls.DB_USER}"

        cls.FLIBUSTA_SERVER = flibusta_server
        cls.FLIBUSTA_SERVER_PUBLIC = flibusta_server_public

        cls.WEBHOOK_PORT = webhook_port
        cls.WEBHOOK_HOST = f"https://kurbezz.ru:{cls.WEBHOOK_PORT}/{cls.BOT_NAME}"

        cls.SERVER_HOST = server_host
        cls.SERVER_PORT = server_port

        cls.REDIS_HOST = redis_host
        cls.REDIS_PASSWORD = redis_password

        cls.FLIBUSTA_BOOKS_CHANNEL_ID = flibusta_books_channel_id

        cls.CHATBASE_API_KEY = chatbase_api_key


fire.Fire(Config.configurate)
