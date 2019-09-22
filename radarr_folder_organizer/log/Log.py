import logging
import os
import sys

ROOT_LOGGER_NAME = "root"


def setup_logger(name=ROOT_LOGGER_NAME):
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s")

    # File logger
    os.makedirs("./logs", exist_ok=True)
    file_handler = logging.FileHandler("./logs/organizer.log")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    # Console logger
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    return logger
