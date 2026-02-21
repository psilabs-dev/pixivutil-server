import os


class PixivUtilConfig:

    def __init__(self):
        self.db_path: str = "./.pixivUtil2/db/db.sqlite"
        self.cookie: str = os.getenv("PIXIVUTIL_COOKIE")
config = PixivUtilConfig()
