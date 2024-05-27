import logging

from logging.handlers import RotatingFileHandler


def setup_logger(name, log_file, level=logging.DEBUG):
    """Настройка логгеров"""
    BACKUP_COUNT = 5
    MAX_LOG_WEIGHT = 52428800

    formatter = logging.Formatter(
        "%(levelname)s - %(asctime)s - %(name)s - %(message)s"
    )
    handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_WEIGHT, backupCount=BACKUP_COUNT
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
