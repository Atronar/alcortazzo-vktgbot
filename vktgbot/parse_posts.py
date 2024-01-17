import re
from typing import Union
import time

import requests
from loguru import logger

import api_requests
from config import REQ_VERSION, VK_TOKEN, SHOW_ORIGINAL_POST_LINK, SHOW_COPYRIGHT_POST_LINK
import tools


def parse_post(
    post: dict,
    repost_exists: bool,
    post_type: str,
    group_name: str
) -> dict:
    text = tools.prepare_text_for_html(post["text"])
    if repost_exists:
        text = tools.prepare_text_for_reposts(text, post, post_type, group_name)
    if post_type == 'post':
        if post["owner_id"] < 0:
            group_name = api_requests.get_group_name(
                VK_TOKEN,
                REQ_VERSION,
                abs(post["owner_id"]),
            )
        else:
            group_name = api_requests.get_user_name(
                VK_TOKEN,
                REQ_VERSION,
                post["owner_id"],
            )
        post_link = f'https://vk.com/wall{post["owner_id"]}_{post["id"]}'
        text = f'<a href="{post_link}"><b>{group_name}</b>\n' \
               f'<i>{time.strftime("%d %b %Y %H:%M:%S", time.localtime(post["date"]))}</i></a>' \
               f'\n\n{text}'

    if SHOW_COPYRIGHT_POST_LINK:
        copyright_link = post.get("copyright", {}).get("link", "")
        copyright_name = post.get("copyright", {}).get("name", copyright_link)
        if copyright_link:
            text = f'{text}\n\n' \
                   f'<a href="{copyright_link}">{copyright_name}</a>' \

    text = tools.reformat_vk_links(text)

    urls: list = []
    videos: list = []
    photos: list = []
    docs: list = []

    if "attachments" in post:
        parse_attachments(post["attachments"], text, urls, videos, photos, docs)

    text = tools.add_urls_to_text(text, urls, videos)
    logger.info(f"{post_type.capitalize()} parsing is complete.")
    return {"text": text, "photos": photos, "docs": docs}


def parse_attachments(
    attachments, text, urls, videos, photos, docs
):
    for attachment in attachments:
        if attachment["type"] == "link":
            url = get_url(attachment, text)
            if url:
                urls.append(url)
        elif attachment["type"] == "video":
            video = get_video(attachment)
            if video:
                videos.append(video)
        elif attachment["type"] == "photo":
            photo = get_photo(attachment)
            if photo:
                photos.append(photo)
        elif attachment["type"] == "doc":
            doc = get_doc(attachment["doc"])
            if doc:
                docs.append(doc)


def get_url(attachment: dict, text: str) -> Union[str, None]:
    url = attachment["link"]["url"]
    return url if url not in text else None


def get_video(attachment: dict) -> str:
    owner_id = attachment["video"]["owner_id"]
    video_id = attachment["video"]["id"]
    video_type = attachment["video"]["type"]
    access_key = attachment["video"].get("access_key", "")

    video = api_requests.get_video_url(VK_TOKEN, REQ_VERSION, owner_id, video_id, access_key)
    if video:
        return video
    elif video_type == "short_video":
        return f"https://vk.com/clip{owner_id}_{video_id}"
    else:
        return f"https://vk.com/video{owner_id}_{video_id}"


def get_photo(attachment: dict) -> Union[str, None]:
    sizes = attachment["photo"]["sizes"]
    types = ["w", "z", "y", "x", "r", "q", "p", "o", "m", "s"]

    for type_ in types:
        if next(
            (item for item in sizes if item["type"] == type_),
            False,
        ):
            return re.sub(
                "&([a-zA-Z]+(_[a-zA-Z]+)+)=([a-zA-Z0-9-_]+)",
                "",
                next(
                    (item for item in sizes if item["type"] == type_)
                )["url"],
            )
    else:
        return None


def get_doc(doc: dict) -> Union[dict, None]:
    if doc["size"] > 50000000:
        logger.info(f"The document was skipped due to its size exceeding the 50MB limit: {doc['size']=}.")
        return None
    else:
        response = requests.get(doc["url"])

        with open(f'./temp/{tools.slug_filename(doc["title"])}', "wb") as file:
            file.write(response.content)

    return {"title": doc["title"], "url": doc["url"]}
