import sys
from loguru import logger


def read_id() -> int:
    try:
        with open("./last_id.txt", "r") as file:
            return int(file.read())
    except ValueError:
        logger.critical(
            "The value of the last identifier is incorrect. "
            "Please check the contents of the file 'last_id.txt'."
        )
        sys.exit()


def write_id(new_id: int) -> None:
    with open("./last_id.txt", "w") as file:
        file.write(str(new_id))
    logger.info(f"New ID, written in the file: {new_id}")


def read_known_id() -> int:
    try:
        with open("./last_known_id.txt", "r") as file:
            return int(file.read())
    except ValueError:
        logger.critical(
            "The value of the last identifier is incorrect. "
            "Please check the contents of the file 'last_known_id.txt'."
        )
        sys.exit()


def write_known_id(new_id: int) -> None:
    with open("./last_known_id.txt", "w") as file:
        file.write(str(new_id))
    logger.info(f"New ID, written in the file: {new_id}")
