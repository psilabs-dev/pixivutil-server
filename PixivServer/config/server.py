import os
from typing import Literal


class ServerConfig:

    def __init__(self):
        self.db = ".pixivUtil2/db/db.sqlite"
        api_key = os.getenv("PIXIVUTIL_SERVER_API_KEY")
        self.api_key = api_key if api_key else None

        server_env = os.getenv("PIXIVUTIL_SERVER_ENV", "production")
        if server_env != "production" and server_env != "development":
            raise ValueError(f"Unrecognized environment: {server_env}")
        self.server_env: Literal["production", "development"] = server_env

config = ServerConfig()
