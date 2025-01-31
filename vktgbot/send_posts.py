import asyncio
import os
import requests

from aiogram import Bot, types
from aiogram.utils import exceptions
from loguru import logger

import tools


MAX_DOC_SIZE = 20971520 # 20 Mb


async def send_post(
    bot: Bot,
    tg_channel: str,
    text: str,
    photos: list[str],
    docs: list[dict[str, str]],
    num_tries: int = 0,
    avatar_update: bool = False
) -> None:
    num_tries += 1
    if num_tries > 3:
        logger.error("Post was not sent to Telegram. Too many tries.")
        return
    try:
        if len(photos) == 0 and len(docs) == 0:
            await send_text_post(bot, tg_channel, text)
        elif len(photos) == 1:
            await send_photo_post(bot, tg_channel, text, photos, avatar_update=avatar_update)
        elif len(photos) >= 2:
            await send_photos_post(bot, tg_channel, text, photos)
        if docs and len(photos) == 0:
            await send_docs_post(bot, tg_channel, docs, caption=text)
        elif docs:
            await send_docs_post(bot, tg_channel, docs)
    except exceptions.RetryAfter as ex:
        logger.warning(
            "Flood limit is exceeded. "
            f"Sleep {ex.timeout + 10} seconds. "
            f"Try: {num_tries}"
        )
        await asyncio.sleep(ex.timeout + 10)
        await send_post(bot, tg_channel, text, photos, docs, num_tries)
    except exceptions.BadRequest as ex:
        logger.warning(f"Bad request. Wait 60 seconds. Try: {num_tries}. {ex}")
        await asyncio.sleep(60)
        await send_post(bot, tg_channel, text, photos, docs, num_tries)


async def send_text_post(bot: Bot, tg_channel: str, text: str) -> None:
    if not text:
        return

    if len(text) < 4096:
        await bot.send_message(tg_channel, text, parse_mode=types.ParseMode.HTML)
    else:
        text_parts = tools.split_text(text, 4084)
        prepared_text_parts = (
            [text_parts[0] + " (...)"]
            + ["(...) " + part + " (...)" for part in text_parts[1:-1]]
            + ["(...) " + text_parts[-1]]
        )

        for part in prepared_text_parts:
            await bot.send_message(tg_channel, part, parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(0.5)
    logger.info("Text post sent to Telegram.")


async def send_photo_post(
    bot: Bot,
    tg_channel: str,
    text: str,
    photos: list[str],
    avatar_update: bool = False
) -> None:
    if avatar_update:
        await bot.set_chat_photo(
            tg_channel,
            types.InputFile(
                requests.get(photos[0], stream=True).raw,
                filename="avatar.jpg"
            )
        )
    if len(text) <= 1024:
        await bot.send_photo(tg_channel, photos[0], text, parse_mode=types.ParseMode.HTML)
        logger.info("Text post (<=1024) with photo sent to Telegram.")
    else:
        prepared_text = f'<a href="{photos[0]}"> </a>{text}'
        if len(prepared_text) <= 4096:
            await bot.send_message(tg_channel, prepared_text, parse_mode=types.ParseMode.HTML)
        else:
            await send_text_post(bot, tg_channel, text)
            await bot.send_photo(tg_channel, photos[0])
        logger.info("Text post (>1024) with photo sent to Telegram.")


async def send_photos_post(bot: Bot, tg_channel: str, text: str, photos: list[str]) -> None:
    media = types.MediaGroup()
    for photo in photos:
        media.attach_photo(types.InputMediaPhoto(photo))

    if (len(text) > 0) and (len(text) <= 1024):
        media.media[0].caption = text
        media.media[0].parse_mode = types.ParseMode.HTML
    elif len(text) > 1024:
        await send_text_post(bot, tg_channel, text)
    await bot.send_media_group(tg_channel, media)
    logger.info("Text post with photos sent to Telegram.")


async def send_docs_post(
    bot: Bot,
    tg_channel: str,
    docs: list[dict[str, str]],
    caption: str = ""
) -> None:
    media = types.MediaGroup()
    opened_docs = []
    for doc in docs:
        doc_filepath = f"./temp/{tools.slug_filename(doc['title'])}"
        if os.path.getsize(doc_filepath) > MAX_DOC_SIZE:
            caption = f"{caption}\n{doc['url']}"
        else:
            doc_file = open(doc_filepath, "rb")
            opened_docs.append(doc_file)
            media.attach_document(types.InputMediaDocument(doc_file))

    if caption:
        if media and (len(caption) > 0) and (len(caption) <= 1024):
            media.media[0].caption = caption
            media.media[0].parse_mode = types.ParseMode.HTML
        elif not media or len(caption) > 1024:
            await send_text_post(bot, tg_channel, caption)

    if media:
        await bot.send_media_group(tg_channel, media)
    for doc_file in opened_docs:
        doc_file.close()
    logger.info("Documents sent to Telegram.")
