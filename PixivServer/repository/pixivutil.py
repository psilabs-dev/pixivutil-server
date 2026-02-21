import logging
import sqlite3

from PixivServer.config.pixivutil import config as pixivutil_config
from PixivServer.models.pixiv_metadata import (
    PixivDateInfo,
    PixivImageComplete,
    PixivImageToSeries,
    PixivImageToTag,
    PixivMangaImage,
    PixivMasterImage,
    PixivMasterMember,
    PixivMasterSeries,
    PixivMasterTag,
    PixivMemberPortfolio,
    PixivSeriesInfo,
    PixivTagInfo,
    PixivTagTranslation,
)

logger = logging.getLogger(__name__)

class PixivUtilRepository:
    """
    Service layer for PixivUtil2 SQLite database.
    """

    def __init__(self):
        self.db_path = pixivutil_config.db_path
        self.connection: sqlite3.Connection = None

    def open(self):
        self.connection = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = self.connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")
        finally:
            cursor.close()

    def close(self):
        if self.connection is not None:
            self.connection.close()

    def get_member_data_by_id(self, member_id: int) -> PixivMemberPortfolio:
        """
        Get member data and their images from the database.

        Raises:
            KeyError: If member with the given ID is not found.
        """
        try:
            cursor = self.connection.cursor()

            # Get member data
            cursor.execute(
                """SELECT member_id, name, save_folder, created_date, last_update_date,
                          last_image, is_deleted, member_token
                   FROM pixiv_master_member
                   WHERE member_id = ?""",
                (member_id,)
            )
            member_row = cursor.fetchone()

            if member_row is None:
                raise KeyError(f"Member with ID {member_id} not found")

            member = PixivMasterMember(
                member_id=member_row[0],
                name=member_row[1],
                save_folder=member_row[2],
                created_date=member_row[3],
                last_update_date=member_row[4],
                last_image=member_row[5],
                is_deleted=member_row[6],
                member_token=member_row[7]
            )

            # Get images for this member
            cursor.execute(
                """SELECT image_id, member_id, title, save_name, created_date,
                          last_update_date, is_manga, caption
                   FROM pixiv_master_image
                   WHERE member_id = ?""",
                (member_id,)
            )
            image_rows = cursor.fetchall()
            images = [
                PixivMasterImage(
                    image_id=row[0],
                    member_id=row[1],
                    title=row[2],
                    save_name=row[3],
                    created_date=row[4],
                    last_update_date=row[5],
                    is_manga=row[6],
                    caption=row[7]
                )
                for row in image_rows
            ]

            return PixivMemberPortfolio(member=member, images=images)
        except Exception as e:
            logger.error(f"Error getting member data for {member_id}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def count_members(self) -> int:
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM pixiv_master_member")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def count_artworks(self) -> int:
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM pixiv_master_image")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def count_pages(self) -> int:
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM pixiv_manga_image")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def count_tags(self) -> int:
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM pixiv_master_tag")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def count_series(self) -> int:
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM pixiv_master_series")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def get_all_pixiv_member_ids(self) -> list[int]:
        """
        Get all member IDs from the database.

        Returns:
            List of member IDs. Empty list if no members found.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT member_id FROM pixiv_master_member ORDER BY member_id ASC")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Error getting all member IDs: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_all_pixiv_image_ids(self) -> list[int]:
        """
        Get all image IDs from the database.

        Returns:
            List of image IDs. Empty list if no images found.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT image_id FROM pixiv_master_image ORDER BY image_id ASC")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Error getting all image IDs: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_all_pixiv_tags(self) -> list[str]:
        """
        Get all tag IDs from the database.

        Returns:
            List of tag IDs. Empty list if no tags found.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT tag_id FROM pixiv_master_tag ORDER BY tag_id ASC")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Error getting all tag IDs: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_all_pixiv_series(self) -> list[str]:
        """
        Get all series IDs from the database.

        Returns:
            List of series IDs. Empty list if no series found.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT series_id FROM pixiv_master_series ORDER BY series_id ASC")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Error getting all series IDs: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_tag_info_by_id(self, tag_id: str) -> PixivTagInfo:
        """
        Get tag information including translations and associated images.

        Raises:
            KeyError: If tag with the given ID is not found.
        """
        try:
            cursor = self.connection.cursor()

            # Get tag data
            cursor.execute(
                """SELECT tag_id, created_date, last_update_date
                   FROM pixiv_master_tag
                   WHERE tag_id = ?""",
                (tag_id,)
            )
            tag_row = cursor.fetchone()

            if tag_row is None:
                raise KeyError(f"Tag with ID {tag_id} not found")

            tag = PixivMasterTag(
                tag_id=tag_row[0],
                created_date=tag_row[1],
                last_update_date=tag_row[2]
            )

            # Get tag translations
            cursor.execute(
                """SELECT tag_id, translation_type, translation, created_date, last_update_date
                   FROM pixiv_tag_translation
                   WHERE tag_id = ?""",
                (tag_id,)
            )
            translation_rows = cursor.fetchall()
            translations = [
                PixivTagTranslation(
                    tag_id=row[0],
                    translation_type=row[1],
                    translation=row[2],
                    created_date=row[3],
                    last_update_date=row[4]
                )
                for row in translation_rows
            ]

            # Get images with this tag
            cursor.execute(
                """SELECT image_id, tag_id, created_date, last_update_date
                   FROM pixiv_image_to_tag
                   WHERE tag_id = ?
                   ORDER BY image_id ASC""",
                (tag_id,)
            )
            image_rows = cursor.fetchall()
            images = [
                PixivImageToTag(
                    image_id=row[0],
                    tag_id=row[1],
                    created_date=row[2],
                    last_update_date=row[3]
                )
                for row in image_rows
            ]

            return PixivTagInfo(tag=tag, translations=translations, images=images)
        except Exception as e:
            logger.error(f"Error getting tag info for {tag_id}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_series_info_by_id(self, series_id: str) -> PixivSeriesInfo:
        """
        Get series information and associated images.

        Raises:
            KeyError: If series with the given ID is not found.
        """
        try:
            cursor = self.connection.cursor()

            # Get series data
            cursor.execute(
                """SELECT series_id, series_title, series_type, series_description,
                          created_date, last_update_date
                   FROM pixiv_master_series
                   WHERE series_id = ?""",
                (series_id,)
            )
            series_row = cursor.fetchone()

            if series_row is None:
                raise KeyError(f"Series with ID {series_id} not found")

            series = PixivMasterSeries(
                series_id=series_row[0],
                series_title=series_row[1],
                series_type=series_row[2],
                series_description=series_row[3],
                created_date=series_row[4],
                last_update_date=series_row[5]
            )

            # Get images in this series
            cursor.execute(
                """SELECT series_id, series_order, image_id, created_date, last_update_date
                   FROM pixiv_image_to_series
                   WHERE series_id = ?
                   ORDER BY series_order ASC""",
                (series_id,)
            )
            image_rows = cursor.fetchall()
            images = [
                PixivImageToSeries(
                    series_id=row[0],
                    series_order=row[1],
                    image_id=row[2],
                    created_date=row[3],
                    last_update_date=row[4]
                )
                for row in image_rows
            ]

            return PixivSeriesInfo(series=series, images=images)
        except Exception as e:
            logger.error(f"Error getting series info for {series_id}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_image_data_by_id(self, image_id: int) -> PixivImageComplete:
        """
        Get complete image data including member, pages, series, and tags.

        Raises:
            KeyError: If image with the given ID is not found.
        """
        try:
            cursor = self.connection.cursor()

            # Get image data
            cursor.execute(
                """SELECT image_id, member_id, title, save_name, created_date,
                          last_update_date, is_manga, caption
                   FROM pixiv_master_image
                   WHERE image_id = ?""",
                (image_id,)
            )
            image_row = cursor.fetchone()

            if image_row is None:
                raise KeyError(f"Image with ID {image_id} not found")

            image = PixivMasterImage(
                image_id=image_row[0],
                member_id=image_row[1],
                title=image_row[2],
                save_name=image_row[3],
                created_date=image_row[4],
                last_update_date=image_row[5],
                is_manga=image_row[6],
                caption=image_row[7]
            )

            # Get member data
            cursor.execute(
                """SELECT member_id, name, save_folder, created_date, last_update_date,
                          last_image, is_deleted, member_token
                   FROM pixiv_master_member
                   WHERE member_id = ?""",
                (image.member_id,)
            )
            member_row = cursor.fetchone()

            if member_row is None:
                raise KeyError(f"Member {image.member_id} not found for image {image_id}")

            member = PixivMasterMember(
                member_id=member_row[0],
                name=member_row[1],
                save_folder=member_row[2],
                created_date=member_row[3],
                last_update_date=member_row[4],
                last_image=member_row[5],
                is_deleted=member_row[6],
                member_token=member_row[7]
            )

            # Get manga pages
            cursor.execute(
                """SELECT image_id, page, save_name, created_date, last_update_date
                   FROM pixiv_manga_image
                   WHERE image_id = ?
                   ORDER BY page ASC""",
                (image_id,)
            )
            page_rows = cursor.fetchall()
            pages = [
                PixivMangaImage(
                    image_id=row[0],
                    page=row[1],
                    save_name=row[2],
                    created_date=row[3],
                    last_update_date=row[4]
                )
                for row in page_rows
            ]

            # Get series info
            cursor.execute(
                """SELECT its.series_id, its.series_order, its.image_id,
                          its.created_date, its.last_update_date,
                          ms.series_title, ms.series_type, ms.series_description,
                          ms.created_date, ms.last_update_date
                   FROM pixiv_image_to_series its
                   JOIN pixiv_master_series ms ON its.series_id = ms.series_id
                   WHERE its.image_id = ?""",
                (image_id,)
            )
            series_row = cursor.fetchone()
            series = None
            if series_row is not None:
                image_to_series = PixivImageToSeries(
                    series_id=series_row[0],
                    series_order=series_row[1],
                    image_id=series_row[2],
                    created_date=series_row[3],
                    last_update_date=series_row[4]
                )
                master_series = PixivMasterSeries(
                    series_id=series_row[0],
                    series_title=series_row[5],
                    series_type=series_row[6],
                    series_description=series_row[7],
                    created_date=series_row[8],
                    last_update_date=series_row[9]
                )
                series = (image_to_series, master_series)

            # Get tags with translations
            cursor.execute(
                """SELECT itt.image_id, itt.tag_id, itt.created_date, itt.last_update_date,
                          mt.tag_id, mt.created_date, mt.last_update_date,
                          tt.tag_id, tt.translation_type, tt.translation,
                          tt.created_date, tt.last_update_date
                   FROM pixiv_image_to_tag itt
                   JOIN pixiv_master_tag mt ON itt.tag_id = mt.tag_id
                   LEFT JOIN pixiv_tag_translation tt ON mt.tag_id = tt.tag_id
                   WHERE itt.image_id = ?""",
                (image_id,)
            )
            tag_rows = cursor.fetchall()
            tags = []
            for row in tag_rows:
                image_to_tag = PixivImageToTag(
                    image_id=row[0],
                    tag_id=row[1],
                    created_date=row[2],
                    last_update_date=row[3]
                )
                master_tag = PixivMasterTag(
                    tag_id=row[4],
                    created_date=row[5],
                    last_update_date=row[6]
                )
                tag_translation = None
                if row[7] is not None:
                    tag_translation = PixivTagTranslation(
                        tag_id=row[7],
                        translation_type=row[8],
                        translation=row[9],
                        created_date=row[10],
                        last_update_date=row[11]
                    )
                tags.append((image_to_tag, master_tag, tag_translation))

            # Get server-mode date metadata
            cursor.execute(
                """SELECT image_id, created_date_epoch, uploaded_date_epoch,
                          created_date, last_update_date
                   FROM pixiv_date_info
                   WHERE image_id = ?""",
                (image_id,)
            )
            date_row = cursor.fetchone()
            dates = None
            if date_row is not None:
                dates = PixivDateInfo(
                    image_id=date_row[0],
                    created_date_epoch=date_row[1],
                    uploaded_date_epoch=date_row[2],
                    created_date=date_row[3],
                    last_update_date=date_row[4]
                )

            return PixivImageComplete(
                image=image,
                member=member,
                pages=pages,
                series=series,
                tags=tags,
                dates=dates
            )
        except Exception as e:
            logger.error(f"Error getting image data for {image_id}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
