from typing import Union

from aiogram import Bot
from loguru import logger
import asyncio
import time

import config
import api_requests
from last_id import read_id, write_id, read_known_id, write_known_id
from parse_posts import parse_post
from send_posts import send_post
import tools


async def start_script():
    bot = Bot(token=config.TG_BOT_TOKEN)

    last_unixtime = read_known_id()
    last_wall_id = read_id()
    logger.info(f"Last check: {time.strftime('%d %b %Y %H:%M:%S', time.localtime(last_unixtime))}")

    items: Union[dict, None] = api_requests.get_data_from_vk(
        config.VK_TOKEN,
        int(last_wall_id),
        req_filter = config.REQ_FILTER,
        return_banned = config.REQ_RETURN_BANNED,
        start_time = int(last_unixtime),
        source_ids = config.REQ_SOURCE_IDS,
        count = config.REQ_COUNT,
        v = config.REQ_VERSION,
    )
    if not items:
        new_last_unixtime: int = max(int(time.time()) - 60, last_unixtime)
        write_known_id(new_last_unixtime)

        await bot.session.close()
        logger.info(f"Script went to sleep for {config.TIME_TO_SLEEP} seconds.")
        await asyncio.sleep(config.TIME_TO_SLEEP)
        return

    logger.info(f"Got a few posts with IDs: {items[-1]['source_id']}_{items[-1]['id']} - {items[0]['source_id']}_{items[0]['id']}.")

    new_last_unixtime: int = items[0]["date"]
    new_last_wall_id: int = items[0]["source_id"]

    if new_last_unixtime > last_unixtime or new_last_wall_id != last_wall_id:
        for item in items[::-1]:
            item: dict
            if item["date"] <= last_unixtime:
                continue
            logger.info(f"Working with post with ID: {item['source_id']}_{item['id']}.")
            if item.get("is_deleted", False) == True:
                logger.info(f"Post was deleted: {item['deleted_reason']}.")
                continue
            if tools.blacklist_check(config.BLACKLIST, item["text"]):
                continue
            if tools.whitelist_check(config.WHITELIST, item["text"]):
                continue
            if config.SKIP_ADS_POSTS and item.get("marked_as_ads", False):
                logger.info("Post was skipped as an advertisement.")
                continue
            if config.SKIP_COPYRIGHTED_POST and item.get("copyright", None):
                logger.info("Post was skipped as an copyrighted post.")
                continue

            #if item["type"] == "post":
            item_parts = {"post": item}
            group_name = ""
            if item.get("copy_history", None) and not config.SKIP_REPOSTS:
                item_parts["repost"] = item["copy_history"][0]
                if item_parts["repost"]["owner_id"] < 0:
                    group_name = api_requests.get_group_name(
                        config.VK_TOKEN,
                        config.REQ_VERSION,
                        abs(item_parts["repost"]["owner_id"]),
                    )
                else:
                    group_name = api_requests.get_user_name(
                        config.VK_TOKEN,
                        config.REQ_VERSION,
                        item_parts["repost"]["owner_id"],
                    )
                logger.info("Detected repost in the post.")

            for item_part in item_parts:
                tools.prepare_temp_folder()
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
                )

            write_known_id(item["date"])
            write_id(item["source_id"])
    await bot.session.close()
    logger.info(f"Script went to sleep for {config.TIME_TO_SLEEP} seconds.")
    await asyncio.sleep(config.TIME_TO_SLEEP)
