"""
Telegram Bot for automated reposting from VKontakte community pages
to Telegram channels.

v3.1
by @alcortazzo
"""

import time
import asyncio

from loguru import logger

from config import SINGLE_START, TIME_TO_SLEEP, SHORT_TIME_TO_SLEEP
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
    exit_code = asyncio.run(start_script())
    prepare_temp_folder()
    return exit_code


while True:
    try:
        exit_code = main()
        if SINGLE_START:
            logger.info("Script has successfully completed its execution")
            exit()
        else:
            if exit_code == 1:
               logger.info(f"Script went to sleep for {SHORT_TIME_TO_SLEEP} seconds.")
               time.sleep(SHORT_TIME_TO_SLEEP)
            else:
               logger.info(f"Script went to sleep for {TIME_TO_SLEEP} seconds.")
               time.sleep(TIME_TO_SLEEP)
    except KeyboardInterrupt:
        logger.info("Script is stopped by the user.")
        exit()
