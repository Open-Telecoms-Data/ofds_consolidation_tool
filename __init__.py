import logging
from .plugin import OFDSDedupPlugin


def classFactory(iface):

    # Setup logging
    # TODO: change log level by env var
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return OFDSDedupPlugin(iface)
