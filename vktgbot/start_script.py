from typing import Union

from aiogram import Bot, Dispatcher
from loguru import logger
import asyncio

import config
from api_requests import get_data_from_vk, get_user_name, get_group_name, get_last_id
from last_id import read_id, write_id, read_known_id, write_known_id
from parse_posts import parse_post
from send_posts import send_post
from tools import blacklist_check, prepare_temp_folder, whitelist_check


async def start_script():
    bot = Bot(token=config.TG_BOT_TOKEN)
    #dp = Dispatcher()

    last_known_id = read_known_id()
    last_wall_id = read_id()
    logger.info(f"Last known ID: {last_known_id}")

    if int(last_known_id) >= int(last_wall_id):
        last_wall_id = get_last_id(
            config.VK_TOKEN,
            config.REQ_VERSION,
            config.VK_DOMAIN,
            config.REQ_FILTER
        )
        if last_wall_id:
           write_id(last_wall_id)
        await bot.session.close()
        logger.info(f"Script went to sleep for {config.TIME_TO_SLEEP} seconds.")
        await asyncio.sleep(config.TIME_TO_SLEEP)
        return

    items: Union[dict, None] = get_data_from_vk(
        config.VK_TOKEN,
        config.REQ_VERSION,
        config.VK_DOMAIN,
        config.REQ_FILTER,
        config.REQ_COUNT,
        int(last_known_id)+1
    )
    if not items:
        new_last_id: int = int(last_known_id)+config.REQ_COUNT
        write_known_id(new_last_id)
        
        await bot.session.close()
        logger.info(f"Script went to sleep for {config.SHORT_TIME_TO_SLEEP} seconds.")
        await asyncio.sleep(config.SHORT_TIME_TO_SLEEP)
        return 1

    logger.info(f"Got a few posts with IDs: {items[0]['id']} - {items[-1]['id']}.")

    new_last_id: int = items[-1]["id"]

    if new_last_id > last_known_id:
        for item in items:
            item: dict
            if item["id"] <= last_known_id:
                continue
            logger.info(f"Working with post with ID: {item['id']}.")
            if item.get("is_deleted", False) == True:
                logger.info(f"Post was deleted: {item['deleted_reason']}.")
                continue
            if blacklist_check(config.BLACKLIST, item["text"]):
                continue
            if whitelist_check(config.WHITELIST, item["text"]):
                continue
            if config.SKIP_ADS_POSTS and item.get("marked_as_ads", False):
                logger.info("Post was skipped as an advertisement.")
                continue
            if config.SKIP_COPYRIGHTED_POST and item.get("copyright", None):
                logger.info("Post was skipped as an copyrighted post.")
                continue

            item_parts = {"post": item}
            group_name = ""
            if item.get("copy_history", None) and not config.SKIP_REPOSTS:
                item_parts["repost"] = item["copy_history"][0]
                if item_parts["repost"]["owner_id"] < 0:
                    group_name = get_group_name(
                        config.VK_TOKEN,
                        config.REQ_VERSION,
                        abs(item_parts["repost"]["owner_id"]),
                    )
                else:
                    group_name = get_user_name(
                        config.VK_TOKEN,
                        config.REQ_VERSION,
                        item_parts["repost"]["owner_id"],
                    )
                logger.info("Detected repost in the post.")

            for item_part in item_parts:
                prepare_temp_folder()
                repost_exists: bool = True if len(item_parts) > 1 else False

                logger.info(f"Starting parsing of the {item_part}")
                parsed_post = parse_post(item_parts[item_part], repost_exists, item_part, group_name)
                logger.info(f"Starting sending of the {item_part}")
                
                await send_post(
                        bot,
                        config.TG_CHANNEL,
                        parsed_post["text"],
                        parsed_post["photos"],
                        parsed_post["docs"],
                        avatar_update = parsed_post["avatar_update"]
                )
                
        write_known_id(new_last_id)
    await bot.session.close()
    logger.info(f"Script went to sleep for {config.TIME_TO_SLEEP} seconds.")
    await asyncio.sleep(config.TIME_TO_SLEEP)
