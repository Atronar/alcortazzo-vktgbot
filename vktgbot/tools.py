import os
import re
import time

from loguru import logger


def blacklist_check(blacklist: list | None, text: str) -> bool:
    if blacklist:
        text_lower = text.lower()
        for black_word in blacklist:
            if black_word.lower() in text_lower:
                logger.info(f"Post was skipped due to the detection of blacklisted word: {black_word}.")
                return True

    return False


def whitelist_check(whitelist: list | None, text: str) -> bool:
    if whitelist:
        text_lower = text.lower()
        for white_word in whitelist:
            if white_word.lower() in text_lower:
                return False
        logger.info("The post was skipped because no whitelist words were found.")
        return True

    return False


def prepare_temp_folder():
    if "temp" in os.listdir():
        for root, dirs, files in os.walk("temp"):
            for file in files:
                os.remove(os.path.join(root, file))
    else:
        os.mkdir("temp")


def prepare_text_for_reposts(text: str, item: dict, item_type: str, group_name: str) -> str:
    if item_type == "post" and text:
        from_id = item["copy_history"][0]["owner_id"]
        id = item["copy_history"][0]["id"]
        link_to_repost = f"https://vk.com/wall{from_id}_{id}"
        text = f'{text}\n\n<a href="{link_to_repost}"><b>REPOST ↓ {group_name}</b>\n' \
               f'<i>{time.strftime("%d %b %Y %H:%M:%S", time.localtime(item["date"]))}</i></a>'
    if item_type == "repost":
        from_id = item["owner_id"]
        id = item["id"]
        link_to_repost = f"https://vk.com/wall{from_id}_{id}"
        text = f'<a href="{link_to_repost}"><b>REPOST ↓ {group_name}</b>\n' \
               f'<i>{time.strftime("%d %b %Y %H:%M:%S", time.localtime(item["date"]))}</i></a>\n\n{text}'

    return text


def prepare_text_for_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def add_urls_to_text(text: str, urls: list, videos: list) -> str:
    first_link = True
    urls = videos + urls

    if not urls:
        return text

    for url in urls:
        if url not in text:
            if first_link:
                text = f'<a href="{url}"> </a>{text}\n\n{url}' if text else url
                first_link = False
            else:
                text += f"\n{url}"
    return text


def split_text(text: str, fragment_size: int) -> list:
    fragments = []
    for fragment in range(0, len(text), fragment_size):
        fragments.append(text[fragment : fragment + fragment_size])
    return fragments


def reformat_vk_links(text: str) -> str:
    match = re.search(r"\[([\w.:/]+?)\|(.+?)\]", text)
    while match:
        left_text = text[: match.span()[0]]
        right_text = text[match.span()[1] :]
        matching_text = text[match.span()[0] : match.span()[1]]

        link_domain, link_text = re.findall(r"\[(.+?)\|(.+?)\]", matching_text)[0]
        text = left_text + f"""<a href="{f'https://vk.com/{link_domain}'}">{link_text}</a>""" + right_text
        match = re.search(r"\[([\w.:/]+?)\|(.+?)\]", text)

    return text

def slug_filename(text: str) -> str:
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        text = text.replace(char, '')
    return text
