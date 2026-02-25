import logging
import os
import sqlite3
import sys
import traceback
from urllib.error import HTTPError

sys.path.append('PixivUtil2')

from PixivServer.config.pixivutil import config as pixivutil_config
from PixivServer.models.pixiv_worker import (
    DeleteArtworkByIdRequest,
    DownloadArtworkByIdRequest,
    DownloadArtworkMetadataByIdRequest,
    DownloadArtworksByMemberIdRequest,
    DownloadArtworksByTagsRequest,
    DownloadMemberMetadataByIdRequest,
    DownloadSeriesMetadataByIdRequest,
    DownloadTagMetadataByIdRequest,
)
from PixivServer.utils import clear_folder
from PixivUtil2 import (
    PixivArtistHandler,
    PixivBrowserFactory,
    PixivConfig,
    PixivConstant,
    PixivDBManager,
    PixivException,
    PixivHelper,
    PixivImageHandler,
    PixivTagsHandler,
    set_console_title,  # noqa: F401,
)

logger = logging.getLogger(__name__)

# ------ START CALLER ITEMS ------

__config__ = PixivConfig.PixivConfig()
configfile = ".pixivUtil2/conf/config.ini"
__dbManager__ = None
__br__: PixivBrowserFactory.PixivBrowser = None
__blacklistTags = []
__suppressTags = []
__log__ = None
__errorList = []
__blacklistMembers = []
__blacklistTitles = []
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
        pixiv_retry = os.getenv("PIXIVUTIL2_NETWORK_RETRY")
        if pixiv_retry is not None:
            __config__.retry = int(pixiv_retry)
        pixiv_retry_wait = os.getenv("PIXIVUTIL2_NETWORK_RETRY_WAIT")
        if pixiv_retry_wait is not None:
            __config__.retryWait = int(pixiv_retry_wait)

        return

    def open(self, validate_pixiv_login: bool = True):

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

        if __br__ is None:
            __br__ = PixivBrowserFactory.getBrowser(config=__config__)

        # Worker may validate login at startup. API server should not.
        if validate_pixiv_login:
            cookie = __config__.cookie
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
        self.configure_database_connection(__dbManager__.conn)
        __dbManager__.createDatabase()

    def configure_database_connection(self, connection: sqlite3.Connection) -> None:
        """Apply server-side SQLite pragmas to reduce lock contention."""
        cursor = connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")
        finally:
            cursor.close()

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
        except (HTTPError, PixivException, AssertionError, ValueError) as e:
            logger.error(f'Error at doLogin(): {sys.exc_info()}')
            logger.error(traceback.format_exc())
            raise PixivException("Cannot Login!", PixivException.CANNOT_LOGIN) from e
        return result

    def get_pixiv_cookie(self):
        return __config__.cookie

    def update_pixiv_cookie(self, new_cookie: str) -> bool:
        __config__.cookie = new_cookie
        __config__.writeConfig(path=configfile)
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

    def _raise_metadata_process_image_failure(
        self,
        *,
        artwork_id: int,
        process_result: int,
        previous_error_list_len: int,
        previous_error_code: int,
    ) -> None:
        if process_result == PixivConstant.PIXIVUTIL_OK:
            return

        error_list = globals()["__errorList"]
        new_errors = error_list[previous_error_list_len:] if len(error_list) >= previous_error_list_len else error_list
        pixiv_error: PixivException | None = None
        for item in reversed(new_errors):
            if not isinstance(item, dict):
                continue
            exc = item.get("exception")
            if isinstance(exc, PixivException):
                pixiv_error = exc
                break

        if pixiv_error is not None:
            if pixiv_error.errorCode in (PixivException.DOWNLOAD_FAILED_NETWORK, PixivException.SERVER_ERROR):
                raise ConnectionError(
                    f"Artwork metadata fetch failed due to network/server error for artwork_id={artwork_id}"
                ) from pixiv_error
            raise RuntimeError(
                f"Artwork metadata fetch failed for artwork_id={artwork_id} "
                f"(pixiv_error_code={pixiv_error.errorCode}, result={process_result})"
            ) from pixiv_error

        current_error_code = ERROR_CODE
        error_code = current_error_code if current_error_code != previous_error_code else -1
        if error_code in (PixivException.DOWNLOAD_FAILED_NETWORK, PixivException.SERVER_ERROR):
            raise ConnectionError(
                f"Artwork metadata fetch failed due to network/server error for artwork_id={artwork_id} "
                f"(pixiv_error_code={error_code}, result={process_result})"
            )
        # Metadata fetch failures can be swallowed by PixivUtil2 without a stable error code.
        # Treat unclassified failures as transient so worker retry/DLQ policy can recover them.
        raise ConnectionError(
            f"Artwork metadata fetch failed with unclassified error for artwork_id={artwork_id} "
            f"(pixiv_error_code={error_code}, result={process_result})"
        )

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

    def delete_artwork_by_id(self, request: DeleteArtworkByIdRequest):
        """Delete artwork by ID from database and filesystem."""
        PixivHelper.print_and_log("info", f"Deleting artwork by ID: {request.artwork_id} (delete_metadata={request.delete_metadata})")
        db_path: str = __config__.dbPath
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")

        conn = sqlite3.connect(db_path, timeout=30.0)
        files_to_delete = []

        try:
            cursor = conn.cursor()

            # Collect file paths
            master_image_row = cursor.execute(
                "SELECT save_name FROM pixiv_master_image WHERE image_id = ?",
                (request.artwork_id,)
            ).fetchone()

            if master_image_row is None:
                PixivHelper.print_and_log("warning", f"Artwork with ID {request.artwork_id} not found in database.")
                return

            master_image_save_name: str | None = master_image_row[0]
            is_archive_mode = master_image_save_name and master_image_save_name.endswith('.zip')

            if master_image_save_name is not None:
                files_to_delete.append(master_image_save_name)

            # In archive mode, manga images are stored inside the zip file as basenames only
            # In non-archive mode, manga images are individual files with full paths
            if not is_archive_mode:
                manga_image_rows = cursor.execute(
                    "SELECT save_name FROM pixiv_manga_image WHERE image_id = ?",
                    (request.artwork_id,)
                ).fetchall()

                for manga_image_row in manga_image_rows:
                    manga_image_save_name: str | None = manga_image_row[0]
                    if manga_image_save_name is not None and manga_image_save_name != master_image_save_name:
                        files_to_delete.append(manga_image_save_name)

            # Delete from database
            cursor.execute("DELETE FROM pixiv_master_image WHERE image_id = ?", (request.artwork_id,))
            cursor.execute("DELETE FROM pixiv_manga_image WHERE image_id = ?", (request.artwork_id,))
            cursor.execute("DELETE FROM pixiv_image_to_tag WHERE image_id = ?", (request.artwork_id,))

            if request.delete_metadata:
                cursor.execute("DELETE FROM pixiv_date_info WHERE image_id = ?", (request.artwork_id,))
                cursor.execute("DELETE FROM pixiv_ai_info WHERE image_id = ?", (request.artwork_id,))
                cursor.execute("DELETE FROM pixiv_image_to_series WHERE image_id = ?", (request.artwork_id,))
                PixivHelper.print_and_log("info", f"Deleted artwork and metadata from database: {request.artwork_id}")
            else:
                PixivHelper.print_and_log("info", f"Deleted artwork from database (metadata preserved): {request.artwork_id}")

            conn.commit()

        except Exception as e:
            conn.rollback()
            PixivHelper.print_and_log("error", f"Database error in delete_artwork_by_id: {str(e)}")
            PixivHelper.print_and_log("error", traceback.format_exc())
            raise
        finally:
            conn.close()

        # Delete files from filesystem
        file_deletion_errors = []
        for file_path in files_to_delete:
            if not os.path.exists(file_path):
                PixivHelper.print_and_log("warning", f"File not found: {file_path}")
                continue

            try:
                os.remove(file_path)
                PixivHelper.print_and_log("info", f"Deleted file: {file_path}")
            except OSError as os_error:
                error_msg = f"Error deleting file {file_path}: {str(os_error)}"
                PixivHelper.print_and_log("error", error_msg)
                file_deletion_errors.append(error_msg)

        if file_deletion_errors:
            PixivHelper.print_and_log("warning", f"Completed with {len(file_deletion_errors)} file deletion error(s)")
        else:
            mode = "archive" if is_archive_mode else "directory"
            PixivHelper.print_and_log("info", f"Successfully deleted artwork ({mode} mode): {request.artwork_id}")

    def download_member_metadata_by_id(self, request: DownloadMemberMetadataByIdRequest):
        PixivHelper.print_and_log("info", f"Download member metadata by ID: {request.member_id}")
        PixivArtistHandler.process_member_metadata(
            sys.modules[__name__],
            __config__,
            request.member_id,
        )

    def download_artwork_metadata_by_id(self, request: DownloadArtworkMetadataByIdRequest):
        PixivHelper.print_and_log("info", f"Download artwork metadata by ID: {request.artwork_id}")
        previous_error_list_len = len(globals()["__errorList"])
        previous_error_code = ERROR_CODE
        result = PixivImageHandler.process_image(
            sys.modules[__name__],
            __config__,
            artist=None,
            image_id=request.artwork_id,
            useblacklist=False,
            metadata_only=True,
        )
        self._raise_metadata_process_image_failure(
            artwork_id=request.artwork_id,
            process_result=result,
            previous_error_list_len=previous_error_list_len,
            previous_error_code=previous_error_code,
        )

    def download_series_metadata_by_id(self, request: DownloadSeriesMetadataByIdRequest):
        PixivHelper.print_and_log("info", f"Download series metadata by ID: {request.series_id}")
        PixivImageHandler.process_manga_series_metadata(
            sys.modules[__name__],
            __config__,
            request.series_id,
        )

    def download_tag_metadata_by_id(self, request: DownloadTagMetadataByIdRequest):
        PixivHelper.print_and_log("info", f"Download tag metadata: {request.tag} (filter_mode={request.filter_mode})")
        PixivTagsHandler.process_tag_metadata(
            sys.modules[__name__],
            __config__,
            request.tag,
            filter_mode=request.filter_mode,
        )

service = PixivUtilService()
