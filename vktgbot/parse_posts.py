import re
from typing import Iterable, Union

import requests
from loguru import logger

import api_requests
from config import REQ_VERSION, VK_TOKEN, SHOW_ORIGINAL_POST_LINK
import tools


def parse_post(
    post: dict,
    repost_exists: bool,
    post_type: str,
    group_name: str
) -> dict[str, str|list[str|dict[str, str]]|bool]:
    text = tools.prepare_text_for_html(post["text"])
    if repost_exists:
        text = tools.prepare_text_for_reposts(text, post, post_type, group_name)
    elif SHOW_ORIGINAL_POST_LINK:
        post_link = f'https://vk.com/wall{post["owner_id"]}_{post["id"]}'
        text = f'<a href="{post_link}"><b>Original post</b></a>\n\n{text}'

    text = tools.reformat_vk_links(text)

    urls: list[str] = []
    videos: list[str] = []
    photos: list[str] = []
    docs: list[dict[str, str]] = []

    if "attachments" in post:
        parse_attachments(post["attachments"], text, urls, videos, photos, docs)

    avatar_update = False
    if photos and post.get("post_source", {}).get("data", "")=="profile_photo":
        avatar_update = True

    text = tools.add_urls_to_text(text, urls, videos)
    logger.info(f"{post_type.capitalize()} parsing is complete.")
    return {"text": text, "photos": photos, "docs": docs, "avatar_update": avatar_update}


def parse_attachments(
    attachments: Iterable[dict[str]],
    text: str,
    urls: list[str],
    videos: list[str],
    photos: list[str],
    docs: list[dict[str, str]]
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


def get_url(attachment: dict[str, dict[str, str]], text: str) -> Union[str, None]:
    url = attachment.get("link", {}).get("url", "")
    return url if url not in text else None


def get_video(attachment: dict[str, dict[str, str]]) -> str:
    owner_id = attachment["video"]["owner_id"]
    video_id = attachment["video"]["id"]
    video_type = attachment["video"]["type"]
    access_key = attachment["video"].get("access_key", "")

    video = api_requests.get_video_url(VK_TOKEN, REQ_VERSION, owner_id, video_id, access_key)
    if video:
        return video
    if video_type == "short_video":
        return f"https://vk.com/clip{owner_id}_{video_id}"
    return f"https://vk.com/video{owner_id}_{video_id}"


def get_photo(attachment: dict[str, dict[str, list[dict[str, str]]]]) -> Union[str, None]:
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
    return None


def get_doc(doc: dict[str, str|int]) -> Union[dict[str, str], None]:
    if doc["size"] > 50000000:
        logger.info(
            "The document was skipped due to its size exceeding the 50MB limit: "
            f"{doc['size']=}."
        )
        return None

    response = requests.get(doc["url"])

    with open(f'./temp/{tools.slug_filename(doc["title"])}', "wb") as file:
        file.write(response.content)

    return {"title": doc["title"], "url": doc["url"]}
