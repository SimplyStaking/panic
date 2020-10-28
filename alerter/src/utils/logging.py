import logging
import logging.config
import logging.handlers
import sys


def create_logger(file: str, name: str, level: str, rotating: bool = False,
                  propagate: bool = True) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = propagate
    logger.setLevel(level)

    # If logger already has handler, assume it was already created
    if len(logger.handlers) >= 1:
        return logger

    if rotating:
        handler = logging.handlers.RotatingFileHandler(
            file, maxBytes=10000000, backupCount=3, encoding='utf-8')
    else:
        handler = logging.FileHandler(file)

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S %p')

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def log_and_print(text: str, logger: logging.Logger):
    logger.info(text)
    print(text)
    sys.stdout.flush()
