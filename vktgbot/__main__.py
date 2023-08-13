"""
Telegram Bot for automated reposting from VKontakte community pages
to Telegram channels.

v3.1
by @alcortazzo
"""

import asyncio

from loguru import logger

from config import SINGLE_START
from start_script import start_script
from tools import prepare_temp_folder

logger.add(
    "./logs/debug.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="1 week",
    compression="zip",
)

logger.info("Script is started.")


@logger.catch
def main():
    asyncio.run(start_script())
    prepare_temp_folder()


while True:
    try:
        main()
        if SINGLE_START:
            logger.info("Script has successfully completed its execution")
            exit()
    except KeyboardInterrupt:
        logger.info("Script is stopped by the user.")
        exit()
