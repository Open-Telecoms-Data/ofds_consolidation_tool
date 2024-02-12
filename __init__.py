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

    for old_handler in logger.handlers:
        # When we reload the plugin it creates and adds the handler again
        # so remove old handlers from past plugin loads.
        logger.removeHandler(old_handler)

    logger.addHandler(handler)

    return OFDSDedupPlugin(iface)
