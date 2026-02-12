import logging
import time
from typing import Dict, List, Tuple

from PixivServer.service.pixiv import service as pixiv_service
from PixivServer.repository.subscription import SubscriptionRepository
from PixivServer.repository.pixivutil import PixivUtilRepository

logger = logging.getLogger(__name__)

class SubscriptionService:

    def __init__(self):
        self.subscription_db = SubscriptionRepository()
        self.pixivutil_db = PixivUtilRepository()

    def open(self):
        # establish connection to database
        self.subscription_db.open()
        self.pixivutil_db.open()

    def close(self):
        # close connection to database
        self.subscription_db.close()
        self.pixivutil_db.close()

    def run_tag_subscription_job(self) -> Dict[str, List[str]]:
        logger.info("Triggering automated tag download job...")
        subscribed_tags = self.get_subscribed_tags()

        # num_new_artworks = 0
        # new_artwork_titles_by_tag_id = dict()

        for tag in subscribed_tags:
            tag_id = tag[0]
            pixiv_service.download_artworks_by_tag(tag_id)
            logger.info(f"Downloaded artworks by tag: {tag_id}")

    def run_member_subscription_job(self) -> Dict[str, List[str]]:
        logger.info("Triggering automated artist download job...")
        subscribed_members = self.get_subscribed_members()

        num_new_artworks = 0
        new_artwork_titles_by_member_id = dict()

        for member in subscribed_members:
            member_id, member_name = member[0], member[1]
            image_id_list = self.pixivutil_db.select_image_id_list_by_member_id(member_id)
            if not image_id_list:
                image_id_list = list()

            image_id_pool = set(image_id_list)
            member_data = pixiv_service.get_member_data(member_id)[0]
            updated_image_id_list = member_data.imageList

            if not updated_image_id_list:
                logger.info(f"No images found in member with ID {member_id}.")
                continue

            for image_id in updated_image_id_list:
                image_id = int(image_id)

                if image_id not in image_id_pool:
                    print(f'Image id {image_id} is not in {image_id_pool}')
                    if member_name not in new_artwork_titles_by_member_id:
                        new_artwork_titles_by_member_id[member_name] = list()
                    new_artwork_titles_by_member_id[member_name].append(image_id)
                    pixiv_service.download_artwork_by_id(image_id)
                    num_new_artworks += 1
                    time.sleep(1)

            time.sleep(1)
        return new_artwork_titles_by_member_id

    def get_subscribed_members(self) -> List[Tuple[int, str]]:
        logger.info("Getting members subscribed to.")
        subscribed_members = self.subscription_db.select_member_subscriptions()
        if subscribed_members is None:
            logger.error("Failed to get member subscriptions.")
            return list()
        return subscribed_members

    def add_member_subscription(self, member_id: str) -> Dict[str, str]:
        if not member_id.isdigit():
            raise TypeError(f'Member ID {member_id} cannot be converted to integer.')
        member_id = int(member_id)
        member_name = ""

        self.subscription_db.open()
        self.pixivutil_db.open()
        try:
            try:
                member_data = self.pixivutil_db.get_member_data_by_id(member_id)
                member_name = member_data.member.name or member_name
            except KeyError:
                logger.info(
                    f"Member metadata not found in SQLite for {member_id}; subscribing with empty name."
                )
            self.subscription_db.add_member_subscription(member_id, member_name)
        finally:
            self.pixivutil_db.close()
            self.subscription_db.close()

        logger.info(f"Successfully added subscription for: {member_name}")
        return {
            'member_id': member_id,
            'member_name': member_name,
        }

    def delete_member_subscription(self, member_id: str):
        if not member_id.isdigit():
            raise TypeError(f'Member ID {member_id} cannot be converted to integer.')
        member_id = int(member_id)
        if self.subscription_db.check_member_id_exist(member_id):
            member_name = self.subscription_db.select_member_name_by_id(member_id)
            self.subscription_db.remove_member_subscription(member_id)
            logger.info(f'Deleted subscription for: {member_id}')
            return {
                'member_id': member_id,
                'member_name': member_name
            }
        else:
            logger.info(f"Subscription for member ID {member_id} does not exist.")
            return dict()

    def get_subscribed_tags(self) -> List[Tuple[str]]:
        logger.info("Getting tags subscribed to.")
        subscribed_tags = self.subscription_db.select_tag_subscriptions()
        if subscribed_tags is None:
            logger.error("Failed to get tag subscriptions.")
            return list()
        return subscribed_tags

    def add_tag_subscription(self, tag_id: str, bookmark_count: int) -> Dict[str, str]:
        self.subscription_db.add_tag_subscription(tag_id, bookmark_count)
        logger.info(f"Successfully added subscription for tag: {tag_id}")
        return {
            'tag_id': tag_id
        }

    def delete_tag_subscription(self, tag_id: str):
        if self.subscription_db.check_tag_name_exist(tag_id):
            self.subscription_db.remove_tag_subscription(tag_id)
            return {
                'tag_id': tag_id
            }
        else:
            logger.info(f"Subscription for tag ID {tag_id} does not exist.")
            return dict()

service = SubscriptionService()
