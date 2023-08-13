import asyncio
import requests

from aiogram import Bot, types, exceptions
from loguru import logger

from tools import split_text


async def send_post(bot: Bot, tg_channel: str, text: str, photos: list, docs: list, num_tries: int = 0, avatar_update: bool = False) -> None:
    num_tries += 1
    if num_tries > 3:
        logger.error("Post was not sent to Telegram. Too many tries.")
        return
    try:
        if len(photos) == 0:
            await send_text_post(bot, tg_channel, text)
        elif len(photos) == 1:
            await send_photo_post(bot, tg_channel, text, photos, avatar_update=avatar_update)
        elif len(photos) >= 2:
            await send_photos_post(bot, tg_channel, text, photos)
        if docs:
            await send_docs_post(bot, tg_channel, docs)
    except exceptions.TelegramRetryAfter as ex:
        logger.warning(f"Flood limit is exceeded. Sleep {ex.retry_after} seconds. Try: {num_tries}")
        await asyncio.sleep(ex.retry_after)
        await send_post(bot, tg_channel, text, photos, docs, num_tries)
    except exceptions.TelegramBadRequest as ex:
        logger.warning(f"Bad request. Wait 60 seconds. Try: {num_tries}. {ex}")
        await asyncio.sleep(60)
        await send_post(bot, tg_channel, text, photos, docs, num_tries)


async def send_text_post(bot: Bot, tg_channel: str, text: str) -> None:
    if not text:
        return

    if len(text) < 4096:
        await bot.send_message(tg_channel, text, parse_mode="HTML")
    else:
        text_parts = split_text(text, 4084)
        prepared_text_parts = (
            [text_parts[0] + " (...)"]
            + ["(...) " + part + " (...)" for part in text_parts[1:-1]]
            + ["(...) " + text_parts[-1]]
        )

        for part in prepared_text_parts:
            await bot.send_message(tg_channel, part, parse_mode="HTML")
            await asyncio.sleep(0.5)
    logger.info("Text post sent to Telegram.")


async def send_photo_post(bot: Bot, tg_channel: str, text: str, photos: list, avatar_update: bool = False) -> None:
    if avatar_update:
        await bot.set_chat_photo(tg_channel, types.BufferedInputFile(requests.get(photos[0], stream=True).raw, filename="avatar.jpg"))
    if len(text) <= 1024:
        await bot.send_photo(tg_channel, photos[0], caption=text, parse_mode="HTML")
        logger.info("Text post (<=1024) with photo sent to Telegram.")
    else:
        prepared_text = f'<a href="{photos[0]}"> </a>{text}'
        if len(prepared_text) <= 4096:
            await bot.send_message(tg_channel, prepared_text, parse_mode="HTML")
        else:
            await send_text_post(bot, tg_channel, text)
            await bot.send_photo(tg_channel, photos[0])
        logger.info("Text post (>1024) with photo sent to Telegram.")


async def send_photos_post(bot: Bot, tg_channel: str, text: str, photos: list) -> None:
    media: list[types.InputMediaPhoto] = []
    for photo in photos:
        media.append(types.InputMediaPhoto(media=photo))

    if (len(text) > 0) and (len(text) <= 1024):
        media[0].parse_mode = "HTML"
        media[0].caption = text
    elif len(text) > 1024:
        await send_text_post(bot, tg_channel, text)
    await bot.send_media_group(tg_channel, media)
    logger.info("Text post with photos sent to Telegram.")


async def send_docs_post(bot: Bot, tg_channel: str, docs: list) -> None:
    media = []
    for doc in docs:
        media.append(types.InputMediaDocument(media = types.BufferedInputFile(open(f"./temp/{doc['title']}", "rb"), doc['title'])))
    await bot.send_media_group(tg_channel, media)
    logger.info("Documents sent to Telegram.")
