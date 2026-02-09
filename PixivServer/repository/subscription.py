import logging
import sqlite3
from typing import List, Tuple

from PixivServer.config.pixivutil import config as pixivutil_config

logger = logging.getLogger(__name__)

class SubscriptionRepository:

    def __init__(self):
        self.db_path = pixivutil_config.db_path
        self.connection: sqlite3.Connection = None
    
    def open(self):
        self.connection = sqlite3.connect(self.db_path)
        self.create_table()
        
    def create_table(self):
        c = self.connection.cursor()
        c.execute('''
                  CREATE TABLE IF NOT EXISTS pixiv_server_member_subscription (
                  member_id INTEGER PRIMARY KEY ON CONFLICT IGNORE,
                  name TEXT,
                  created_date DATE,
                  last_modified_date DATE)
                  ''')
        c.execute('''
                  CREATE TABLE IF NOT EXISTS pixiv_server_tag_subscription (
                  tag_id VARCHAR(255) PRIMARY KEY ON CONFLICT IGNORE,
                  bookmark_count INTEGER,
                  created_date DATE,
                  last_modified_date DATE)
                  ''')
        self.connection.commit()

    def check_member_id_exist(self, member_id: int) -> bool:
        result = False
        try:
            c = self.connection.cursor()
            c.execute(
                '''SELECT 1 FROM pixiv_server_member_subscription WHERE member_id = ?''',
                (member_id, )
            )
            result = c.fetchone()
        except Exception as e:
            logger.error(f'Failed to check existence of member ID: {member_id}')
            raise e
        finally:
            c.close()
        return result

    def select_member_name_by_id(self, member_id: int) -> str:
        result: str = None
        try:
            c = self.connection.cursor()
            c.execute(
                '''SELECT name FROM pixiv_server_member_subscription WHERE member_id = ?''',
                (member_id, )
            )
            result = c.fetchone()
        except Exception as e:
            logger.error(f'Failed to retrieve member name for ID {member_id}.')
            raise e
        finally:
            c.close()
        return result

    def select_member_subscriptions(self) -> List[Tuple[int, str]]:
        results: List = None

        try:
            c = self.connection.cursor()
            c.execute(
                '''SELECT member_id, name FROM pixiv_server_member_subscription ORDER BY member_id''',
            )
            results = c.fetchall()
        except Exception as e:
            logger.error('Failed to export member subscriptions: ', e)
            raise e
        finally:
            c.close()

        return results

    def add_member_subscription(self, member_id: int, member_name: str) -> bool:
        try:
            c = self.connection.cursor()
            c.execute(
                '''INSERT OR IGNORE INTO pixiv_server_member_subscription VALUES(?, ?, datetime('now'), datetime('now'))''',
                (member_id, member_name, )
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f'Failed to add member subscription: {member_id}', e)
            raise e
        finally:
            c.close()
        return True
    
    def remove_member_subscription(self, member_id: int) -> bool:
        try:
            c = self.connection.cursor()
            c.execute(
                '''DELETE FROM pixiv_server_member_subscription WHERE member_id = ?''',
                (member_id, )
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to remove member {member_id} from subscription: ", e)
            raise e
        finally:
            c.close()
        return True

    def check_tag_name_exist(self, tag_id: str) -> str:
        result = False
        try:
            c = self.connection.cursor()
            c.execute(
                '''SELECT 1 FROM pixiv_server_tag_subscription WHERE tag_id = ?''',
                (tag_id, )
            )
            result = c.fetchone()
        except Exception as e:
            logger.error(f"Failed to check existence of tag name: {tag_id}")
            raise e
        finally:
            c.close()
        return result

    def select_tag_subscriptions(self) -> List[Tuple[str]]:
        results: List = None

        try:
            c = self.connection.cursor()
            c.execute(
                '''SELECT tag_id FROM pixiv_server_tag_subscription''',
            )
            results = c.fetchall()
        except Exception as e:
            logger.error("Failed to export tag encoded subscriptions: ", e)
            raise e
        finally:
            c.close()
        
        return results

    def add_tag_subscription(self, tag_id: str, bookmark_count: int) -> bool:
        try:
            c = self.connection.cursor()
            c.execute(
                '''INSERT INTO pixiv_server_tag_subscription (tag_id, bookmark_count, created_date, last_modified_date) 
                VALUES(?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(tag_id)
                DO UPDATE SET
                    bookmark_count = excluded.bookmark_count,
                    created_date = excluded.created_date,
                    last_modified_date = datetime('now')
                ''',
                (tag_id, bookmark_count, )
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f'Failed to add encoded tag subscription: {tag_id}', e)
            raise e
        finally:
            c.close()
        return True

    def remove_tag_subscription(self, tag_id: int) -> bool:
        try:
            c = self.connection.cursor()
            c.execute(
                '''DELETE FROM pixiv_server_tag_subscription WHERE tag_id = ?''',
                (tag_id, )
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to remove tag {tag_id} from subscription: ", e)
            raise e
        finally:
            c.close()
        return True

    def close(self):
        if self.connection is not None:
            self.connection.close()
