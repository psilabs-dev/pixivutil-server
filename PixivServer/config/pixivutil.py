import os

class PixivUtilConfig:

    def __init__(self):
        self.useragent: str = os.getenv("PIXIVUTIL_USERAGENT")

        self.filenameFormat: str = os.getenv("PIXIVUTIL_FILENAME_FORMAT")
        self.filenameMangaFormat: str = os.getenv("PIXIVUTIL_FILENAME_MANGA_FORMAT")
        self.filenameInfoFormat: str = os.getenv("PIXIVUTIL_FILENAME_INFO_FORMAT")
        self.mangaInfoFormat: str = os.getenv("PIXIVUTIL_MANGA_INFO_FORMAT`")

        # authentication
        self.cookie: str = os.getenv("PIXIVUTIL_COOKIE")

        # ffmpeg
        self.ffmpeg: str = os.getenv("PIXIVUTIL_FFMPEG")

        # ugoira
        self.writeUgoiraInfo: str = os.getenv("PIXIVUTIL_WRITE_UGOIRA_INFO")
        self.createUgoira: str = os.getenv("PIXIVUTIL_CREATE_UGOIRA")
        self.createMkv: str = os.getenv("PIXIVUTIL_CREATE_MKV")
        self.createWebm = os.getenv("PIXIVUTIL_CREATE_WEBM")
        self.createWebp = os.getenv("PIXIVUTIL_CREATE_WEBP")
        self.createGif = os.getenv("PIXIVUTIL_CREATE_GIF")
        self.createApng = os.getenv("PIXIVUTIL_CREATE_A_PNG")
        self.deleteUgoira = os.getenv("PIXIVUTIL_DELETE_UGOIRA")
        self.deleteZipFile = os.getenv("PIXIVUTIL_DELETE_ZIP_FILE")

config = PixivUtilConfig()