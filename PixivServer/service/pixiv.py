import os
import sqlite3
import sys
import traceback

import logging

sys.path.append('PixivUtil2')

from PixivServer.models.pixiv import DownloadArtworkByIdRequest, DownloadArtworksByMemberIdRequest, DownloadArtworksByTagsRequest
from PixivUtil2 import (
    PixivConfig, 
    PixivBrowserFactory, 
    PixivHelper, 
    PixivImageHandler, 
    PixivArtistHandler, 
    PixivDBManager, 
    PixivTagsHandler, 
    PixivException, 
    set_console_title,  # noqa: F401,
)

from PixivServer.config.pixivutil import config as pixivutil_config
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
DEBUG_SKIP_PROCESS_IMAGE = False
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

class PixivUtilService:

    def __init__(self) -> None:
        self.downloads_folder = "./downloads"

        pass

    def load_environment_variables(self):
        "environment variable configuration"
        
        if pixivutil_config.cookie:
            __config__.cookie = pixivutil_config.cookie

        return

    def open(self):

        global __br__
        global __config__
        global __dbManager__
        global __log__        
        # download control
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
        pass

    def close(self):
        PixivHelper.print_and_log("info", "Closing...")
        # self.remove_database()
        __config__.writeConfig(path=configfile)
        __dbManager__.close()

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
        data, response = self.get_artwork_data(artwork_id)
        if data is None:
            raise PixivException("Cannot get artwork name; response: " + str(response))
        return data.imageTitle

    def download_artwork_by_id(self, request: DownloadArtworkByIdRequest):
        PixivHelper.print_and_log("info", f"Download by artwork ID: {request.artwork_id}")
        return PixivImageHandler.process_image(
            sys.modules[__name__],
            __config__,
            image_id=request.artwork_id,
            useblacklist=False,
            user_dir=self.downloads_folder
        )

    def download_artworks_by_member_id(self, request: DownloadArtworksByMemberIdRequest):
        PixivHelper.print_and_log("info", f"Downloading by artist ID: {request.member_id}")
        PixivArtistHandler.process_member(
            sys.modules[__name__],
            __config__,
            member_id=request.member_id,
            user_dir=self.downloads_folder,
            include_sketch=request.include_sketch,
        )

    def download_artworks_by_tag(self, request: DownloadArtworksByTagsRequest):
        logger.info(f"Before calling PixivTagsHandler.process_tags with tag: {request.tags}")
        try:
            logger.info(f"Parameters: wild_card={request.wildcard}, bookmark_count={request.bookmark_count}, sort_order={request.sort_order}")
            PixivHelper.print_and_log("info", f"Downloading by tag: {request.tags}")
            PixivTagsHandler.process_tags(
                sys.modules[__name__],
                __config__,
                request.tags.rstrip(),
                bookmark_count=request.bookmark_count,
                start_date=request.start_date,
                end_date=request.end_date,
                sort_order=request.sort_order,
                type_mode=request.type_mode,
                wild_card=request.wildcard,
            )
            logger.info(f"Successfully completed process_tags for tag: {request.tags}")
        except Exception as e:
            logger.error(f"Error in download_artworks_by_tag: {str(e)}")
            logger.error(traceback.format_exc())
            raise

service = PixivUtilService()
