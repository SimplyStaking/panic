import logging
import logging.config
import logging.handlers

DUMMY_LOGGER = logging.getLogger('dummy')


def create_logger(file: str, name: str, level: str, rotating: bool = False) \
        -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # If logger already has handler, assume it was already created
    if len(logger.handlers) == 1:
        return logger

    if rotating:
        handler = logging.handlers.RotatingFileHandler(
            file, maxBytes=10000000, backupCount=3)
    else:
        handler = logging.FileHandler(file)

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S %p')

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
