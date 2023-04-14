import logging
import time

logging.Formatter.converter = time.gmtime


class Base:
    """
    Base class for all classes
    """

    logger: logging.Logger

    def __init__(self):
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}",
        )
