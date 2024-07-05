import logging

from logging.handlers import RotatingFileHandler


def setup_logger(name, log_file, level=logging.DEBUG):
    """
    Настройка логгеров


    Параметры
    ---------
    formatter
        настройка вывода инфорамации в лог
            levelname - уровень важности
            asctime - время регистрации записи
            name - название модуля, который создал запись
            message - сама запись
    handler
        обработчик ротации файлов. если текущее сообщение вот-вот
        позволит файлу журнала превысить максимальный размер,
        то обработчик закроет текущий файл и откроет следующий.
            maxBytes - максимальный размер лог-файла, 50 Мб
            backupCount - количество лог-файлов

    """
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
