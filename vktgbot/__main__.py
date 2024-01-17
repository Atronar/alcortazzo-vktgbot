"""
Telegram Bot for automated reposting from VKontakte community pages
to Telegram channels.

v3.1
by @alcortazzo
"""

import asyncio
import sys

from loguru import logger

from config import SINGLE_START
from start_script import start_script
import tools

logger.add(
    "./logs/debug.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="1 week",
    retention="1 month",
    compression="zip",
)

logger.info("Script is started.")


@logger.catch(reraise=True)
def main():
    asyncio.run(start_script())
    tools.prepare_temp_folder()

if __name__ == "__main__":
    while True:
        try:
            main()
            if SINGLE_START:
                logger.info("Script has successfully completed its execution")
                sys.exit()
        except KeyboardInterrupt:
            logger.info("Script is stopped by the user.")
            sys.exit()
