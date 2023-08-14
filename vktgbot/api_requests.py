from typing import Union

import re
import requests
from loguru import logger


def get_data_from_vk(
    vk_token: str,
    last_wall_owner_id: int,
    *,
    req_filter: str | None = None,
    return_banned: int | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    max_photos: int | None = None,
    source_ids: str | None = None,
    count: int | None = None,
    v: float,
) -> Union[dict, None]:
    logger.info("Trying to get posts from VK.")

    response = requests.get(
        "https://api.vk.com/method/newsfeed.get",
        params=dict(
            {
                "access_token": vk_token,
                "filters": req_filter,
                "return_banned": return_banned,
                "start_time": start_time,
                "end_time": end_time,
                "max_photos": max_photos,
                "source_ids": source_ids,
                "count": count,
                "v": v,
            },
        ),
    )
    data: dict = response.json()
    if "response" in data:
        return data["response"]["items"]
    elif "error" in data:
        logger.error("Error was detected when requesting data from VK: " f"{data['error']['error_msg']}")
    return None


def get_last_id(
    vk_token: str, req_version: float, vk_domain: str, req_filter: str
) -> Union[int, None]:
    logger.info("Trying to get posts from VK.")

    match = re.search(r"^(club|public)(\d+)$", vk_domain)
    if match:
        source_param = {"owner_id": "-" + match.groups()[1]}
    else:
        source_param = {"domain": vk_domain}

    response = requests.get(
        "https://api.vk.com/method/wall.get",
        params=dict(
            {
                "access_token": vk_token,
                "v": req_version,
                "filter": req_filter,
                "count": 2,
            },
            **source_param,
        ),
    )
    data = response.json()
    if "response" in data and data["response"]["items"]:
        items = data["response"]["items"]
        if "is_pinned" in items[0]:
            return items[1]["id"]
        return items[0]["id"]
    elif "error" in data:
        logger.error("Error was detected when requesting data from VK: " f"{data['error']['error_msg']}")
    return None


def get_video_url(vk_token: str, req_version: float, owner_id: str, video_id: str, access_key: str) -> str:
    response = requests.get(
        "https://api.vk.com/method/video.get",
        params={
            "access_token": vk_token,
            "v": req_version,
            "videos": f"{owner_id}_{video_id}{'' if not access_key else f'_{access_key}'}",
        },
    )
    data = response.json()
    if "response" in data and data["response"]["items"]:
        return data["response"]["items"][0]["files"].get("external", "")
    elif "error" in data:
        logger.error(f"Error was detected when requesting data from VK: {data['error']['error_msg']}")
    return ""


def get_group_name(vk_token: str, req_version: float, owner_id) -> str:
    response = requests.get(
        "https://api.vk.com/method/groups.getById",
        params={
            "access_token": vk_token,
            "v": req_version,
            "group_id": owner_id,
        },
    )
    data = response.json()
    if "response" in data:
        return data["response"][0]["name"]
    elif "error" in data:
        logger.error(f"Error was detected when requesting data from VK: {data['error']['error_msg']}")
    return ""


def get_group_id(vk_token: str, req_version: float, domain) -> int | None:
    response = requests.get(
        "https://api.vk.com/method/groups.getById",
        params={
            "access_token": vk_token,
            "v": req_version,
            "group_id": domain,
        },
    )
    data = response.json()
    if "response" in data:
        return data["response"][0]["id"]
    elif "error" in data:
        logger.error(f"Error was detected when requesting data from VK: {data['error']['error_msg']}")
    return None
