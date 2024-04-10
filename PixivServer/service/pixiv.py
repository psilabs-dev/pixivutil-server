import asyncio
import os
import sqlite3
import sys
import traceback

import logging
from typing import List

from PixivServer.client.notification.matrix import MatrixNotificationClient

sys.path.append('PixivUtil2')

from PixivServer.client.notification.default import NotificationClient
from PixivUtil2 import *

from PixivServer.config import pixivutil
from PixivServer.service.default import FastAPIService
from PixivServer.utils import clear_folder

logger = logging.getLogger(__name__)

# ------ START CALLER ITEMS ------

__config__ = PixivConfig.PixivConfig()
configfile = ".pixivUtil2/conf/config.ini"
__dbManager__ = None
__br__: PixivBrowserFactory.PixivBrowser = None
__blacklistTags = list()
__suppressTags = list()
__log__ = None
__errorList = list()
__blacklistMembers = list()
__blacklistTitles = list()
__valid_options = ()
__seriesDownloaded = []

script_path = PixivHelper.module_path()

op = ''
ERROR_CODE = 0
UTF8_FS = None
DEBUG_SKIP_DOWNLOAD_IMAGE = False

start_iv = False
dfilename = ""
platform_encoding = 'utf-8'

# ------ END CALLER ITEMS -------

class PixivDBManagerMultiThread(PixivDBManager):

    # override initialization.
    def __init__(self, root_directory, target='', timeout=5 * 60):
        if target is None or len(target) == 0:
            target = script_path + os.sep + "db.sqlite"
            PixivHelper.print_and_log(
                'info', "Using default DB Path: " + target)
        else:
            PixivHelper.print_and_log(
                'info', "Using custom DB Path: " + target)
        self.rootDirectory = root_directory

        # allow sqlite connection on different threads
        self.conn = sqlite3.connect(target, timeout, check_same_thread=False)

class PixivUtilService(FastAPIService):

    def __init__(self) -> None:
        self.downloads_folder = "./downloads"
        self.notification_clients: List[NotificationClient] = list()

        if MatrixNotificationClient.is_available():
            logger.info("Adding Matrix notification client.")
            self.notification_clients.append(MatrixNotificationClient())

        pass

    def send_notification(self, message):
        for client in self.notification_clients:
            client.send_notification(message)

    def load_environment_variables(self):
        "environment variable configuration"
        
        if pixivutil.config.cookie:
            __config__.cookie = pixivutil.config.cookie

        if pixivutil.config.ffmpeg:
            __config__.ffmpeg = pixivutil.config.ffmpeg

        if pixivutil.config.filenameFormat:
            __config__.filenameFormat = pixivutil.config.filenameFormat
        if pixivutil.config.filenameInfoFormat:
            __config__.filenameInfoFormat = pixivutil.config.filenameInfoFormat
        if pixivutil.config.filenameMangaFormat:
            __config__.filenameMangaFormat = pixivutil.config.filenameMangaFormat

        if pixivutil.config.writeUgoiraInfo:
            __config__.writeUgoiraInfo = pixivutil.config.writeUgoiraInfo
        if pixivutil.config.createUgoira:
            __config__.createUgoira = pixivutil.config.createUgoira
        if pixivutil.config.createMkv:
            __config__.createMkv = pixivutil.config.createMkv
        if pixivutil.config.createWebm:
            __config__.createWebm = pixivutil.config.createWebm
        if pixivutil.config.createWebp:
            __config__.createWebp = pixivutil.config.createWebp
        if pixivutil.config.createGif:
            __config__.createGif = pixivutil.config.createGif
        if pixivutil.config.createApng:
            __config__.createApng = pixivutil.config.createApng
        if pixivutil.config.deleteUgoira:
            __config__.deleteUgoira = pixivutil.config.deleteUgoira
        if pixivutil.config.deleteZipFile:
            __config__.deleteZipFile = pixivutil.config.deleteZipFile

        return

    def open(self):

        global __br__
        global __config__
        global __dbManager__
        global __log__

        # default configuration (overridden by existing config)

        # settings
        __config__.downloadListDirectory = "./downloads"
        __config__.rootDirectory = "."
        __config__.dbPath = ".pixivUtil2/db/db.sqlite"
        __config__.useragent = "Mozilla/5.0"
        __config__.verifyimage = True
        
        __config__.ffmpeg = "/usr/bin/ffmpeg"

        __config__.filenameFormat = '{%member_id%} %artist%' + os.sep + '{%image_id%} %title%' + os.sep + 'p_0%page_number%'
        __config__.filenameMangaFormat = '{%member_id%} %artist%' + os.sep + '{%image_id%} %title%' + os.sep + 'p_0%page_number%'
        
        # download control
        __config__.alwaysCheckFileSize = True

        if not os.path.exists(configfile):
            os.makedirs(os.path.dirname(configfile), exist_ok=True)
            __config__.writeConfig(path=configfile)
            # raise KeyboardInterrupt

        __config__.loadConfig(path=configfile)
        PixivHelper.set_config(__config__)
        __log__ = PixivHelper.get_logger(reload=True)

        self.load_environment_variables()
        # setup database
        os.makedirs(os.path.dirname(__config__.dbPath), exist_ok=True)
        self.open_database()
        
        # check if Pixiv cookie is installed / validate login capability.
        cookie = __config__.cookie
        if __br__ is None:
            __br__ = PixivBrowserFactory.getBrowser(config=__config__)
        self.login_pixiv(cookie)
        self.send_notification("Started PixivUtil Server.")
        pass

    def close(self):
        PixivHelper.print_and_log("info", "Closing...")
        self.send_notification("Closing PixivUtil Server...")
        # self.remove_database()
        __config__.writeConfig(path=configfile)

    def open_database(self):
        global __dbManager__
        __dbManager__ = PixivDBManagerMultiThread(root_directory=__config__.rootDirectory, target=__config__.dbPath)
        __dbManager__.createDatabase()

    def remove_database(self):
        __dbManager__.close()
        os.remove(__config__.dbPath)

    def reset_database(self):
        self.remove_database()
        self.open_database()

    def reset_downloads(self):
        clear_folder(self.downloads_folder)

    def login_pixiv(self, cookie) -> bool:
        result = False
        try:
            result = __br__.loginUsingCookie(login_cookie=cookie)
        except BaseException:
            logger.error(f'Error at doLogin(): {sys.exc_info()}')
            logger.error(traceback.format_exc())
            raise PixivException("Cannot Login!", PixivException.CANNOT_LOGIN)
        return result

    def get_pixiv_cookie(self):
        return __config__.cookie
    
    def update_pixiv_cookie(self, new_cookie: str) -> bool:
        __config__.cookie = new_cookie
        __config__.writeConfig(path=configfile)
        self.login_pixiv(new_cookie)
        return True

    def get_member_data(self, member_id: int):
        (data, response) = PixivBrowserFactory.getBrowser().getMemberPage(member_id)
        return data, response

    def get_artwork_data(self, artwork_id: int):
        (data, response) = PixivBrowserFactory.getBrowser().getImagePage(image_id=artwork_id)
        return data, response

    def get_member_name(self, member_id: int) -> str:
        data = self.get_member_data(member_id)[0]
        return data.artistName
    
    def get_artwork_name(self, artwork_id: int) -> str:
        data = self.get_artwork_data(artwork_id)[0]
        return data.imageTitle

    def download_artwork_by_id(self, artwork_id: int, artwork_name: str=None):
        logger.info(f"Download by artwork ID: {artwork_id}")
        artwork_name = self.get_artwork_name(artwork_id)
        # self.send_notification(f"Downloading artwork: {artwork_name}")
        PixivImageHandler.process_image(
            sys.modules[__name__],
            __config__,
            image_id=artwork_id,
            useblacklist=False,
            user_dir=self.downloads_folder
        )
        self.send_notification(f"Download complete: {artwork_name}")

    def download_artworks_by_member_id(self, member_id: int, member_name: str=None):
        logger.info(f"Downloading by artist ID: {member_id}")
        member_name = self.get_member_name(member_id)
        # self.send_notification(f"Downloading artworks from: {member_name}")
        PixivArtistHandler.process_member(
            sys.modules[__name__],
            __config__,
            member_id=member_id,
            user_dir=self.downloads_folder,
        )
        self.send_notification(f"Download artworks complete: {member_name}")

service = PixivUtilService()
