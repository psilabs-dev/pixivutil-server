import os


class ServerConfig:

    def __init__(self):
        self.db = ".pixivUtil2/db/db.sqlite"
        api_key = os.getenv("PIXIVUTIL_SERVER_API_KEY")
        self.api_key = api_key if api_key else None

config = ServerConfig()
