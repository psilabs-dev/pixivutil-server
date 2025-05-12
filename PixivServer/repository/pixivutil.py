import logging
import sqlite3
from typing import List

from PixivServer.config.pixivutil import config as pixivutil_config

logger = logging.getLogger(__name__)

class PixivUtilRepository:

    def __init__(self):
        self.db_path = pixivutil_config.db_path
        self.connection: sqlite3.Connection = None

    def open(self):
        self.connection = sqlite3.connect(self.db_path)

    def close(self):
        if self.connection is not None:
            self.connection.close()

    def select_image_id_list_by_member_id(self, member_id: int) -> List[int]:
        result = list()
        try:
            c = self.connection.cursor()
            c.execute(
                '''SELECT image_id FROM pixiv_master_image WHERE member_id = ?''',
                (member_id, )
            )
            result = c.fetchall()
        except Exception:
            logger.error(f"Failed to get image ID by member ID: {member_id}.")
            raise
        finally:
            c.close()
        result = list(map(lambda x:x[0], result))
        return result

    def select_image_title_by_id(self, image_id: int) -> str:
        title = ''
        try:
            c = self.connection.cursor()
            c.execute(
                '''SELECT * FROM pixiv_master_image WHERE image_id = ?''',
                (image_id, )
            )
            row = c.fetchone()
            title = row[0]
        except Exception:
            logger.error(f'Failed to select image ID by title')
            raise
        finally:
            c.close()
        return title
