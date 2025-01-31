import os
import re
import shutil

from loguru import logger


def blacklist_check(blacklist: list | None, text: str) -> bool:
    """Checks if the text contains blacklisted words.

    Args:
        blacklist (list | None): List of blacklisted words.
        text (str): Text to check.

    Returns:
        bool: True if the text contains blacklisted words, False otherwise.
    """
    if blacklist:
        text_lower = text.lower()
        for black_word in blacklist:
            if black_word.lower() in text_lower:
                logger.info(
                    "Post was skipped due to the detection of blacklisted word: "
                    f"{black_word}."
                )
                return True

    return False


def whitelist_check(whitelist: list | None, text: str) -> bool:
    """Checks if the text contains whitelisted words.

    Args:
        whitelist (list | None): List of whitelisted words.
        text (str): Text to check.

    Returns:
        bool: True if the text contains whitelisted words, False otherwise.
    """
    if whitelist:
        text_lower = text.lower()
        for white_word in whitelist:
            if white_word.lower() in text_lower:
                return False
        logger.info("The post was skipped because no whitelist words were found.")
        return True

    return False


def prepare_folder(subfolder_name: str, root_folder: str | None = None):
    """Creates temp folder if it does not exist or clears it if it does.

    Args:
        subfolder_name (str): Name of the subfolder.
        root_folder (str | None, optional): Root folder. Defaults to None.
    """
    path = f"./{root_folder}/{subfolder_name}" if root_folder else f"./{subfolder_name}"
    if subfolder_name in os.listdir(root_folder):
        shutil.rmtree(path)
    os.mkdir(path)


def prepare_temp_folder():
    return prepare_folder("temp")


def prepare_text_for_reposts(text: str, item: dict, item_type: str, group_name: str) -> str:
    """Prepares text for reposts.

    Args:
        text (str): Text to prepare.
        item (dict): Item of the post.
        item_type (str): Type of the item.
        group_name (str): Name of the group.

    Returns:
        str: Prepared text.
    """
    if item_type == "post" and text:
        from_id = item["copy_history"][0]["from_id"]
        post_id = item["copy_history"][0]["id"]
        link_to_repost = f"https://vk.com/wall{from_id}_{post_id}"
        text = f'{text}\n\n<a href="{link_to_repost}"><b>REPOST ↓ {prepare_text_for_html(group_name)}</b></a>'
    if item_type == "repost":
        from_id = item["from_id"]
        post_id = item["id"]
        link_to_repost = f"https://vk.com/wall{from_id}_{post_id}"
        text = f'<a href="{link_to_repost}"><b>REPOST ↓ {prepare_text_for_html(group_name)}</b></a>\n\n{text}'

    return text


def prepare_text_for_html(text: str) -> str:
    """Prepares text for HTML formatting.

    Args:
        text (str): Text to prepare.

    Returns:
        str: Prepared text.
    """
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def add_urls_to_text(text: str, urls: list, videos: list) -> str:
    """Adds URLs to the text.

    Args:
        text (str): Text to add URLs to.
        urls (list): List of URLs.
        videos (list): List of URLs to videos.

    Returns:
        str: Text with URLs.
    """
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
    """Splits text into fragments to fit the maximum Telegram message length.

    Args:
        text (str): Text to split.
        fragment_size (int): Size of the fragment.

    Returns:
        list: List of fragments.
    """
    fragments = []
    for fragment in range(0, len(text), fragment_size):
        fragments.append(text[fragment : fragment + fragment_size])
    return fragments


def reformat_vk_links(text: str) -> str:
    """Reformats VK links to Telegram links."""
    match = re.search(r"\[([\w.:/]+?)\|(.+?)\]", text)
    while match:
        left_text = text[: match.span()[0]]
        right_text = text[match.span()[1] :]
        matching_text = text[match.span()[0] : match.span()[1]]

        link_domain, link_text = re.findall(r"\[(.+?)\|(.+?)\]", matching_text)[0]
        text = (
            left_text +
            f"""<a href="{f'https://vk.com/{link_domain}'}">{link_text}</a>"""
            + right_text
        )
        match = re.search(r"\[([\w.:/]+?)\|(.+?)\]", text)

    return text

def slug_filename(filename: str) -> str:
    """
    # Make title file system safe
    # https://stackoverflow.com/questions/7406102/create-sane-safe-filename-from-any-unsafe-string
    """
    illegal_chars = "/\\?%*:|\"<>"
    illegal_unprintable = {chr(c) for c in (*range(31), 127)}
    reserved_words = {
        'CON', 'CONIN$', 'CONOUT$', 'PRN', 'AUX', 'CLOCK$', 'NUL',
        'COM0', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT0', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
        'LST', 'KEYBD$', 'SCREEN$', '$IDLE$', 'CONFIG$'
    }
    if os.path.splitext(filename)[0].upper() in reserved_words: return f"__{filename}"
    if set(filename)=={'.'}: return filename.replace('.', '\uff0e', 1)
    return "".join(
        chr(ord(c)+65248) if c in illegal_chars else c
        for c in filename
        if c not in illegal_unprintable
    ).rstrip()
