import logging

from .plugin import OFDSDedupPlugin

_created_log_handlers = set()


def setup_logging():
    global _created_log_handlers

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
        if old_handler in _created_log_handlers:
            logger.removeHandler(old_handler)
            _created_log_handlers.remove(old_handler)

    logger.addHandler(handler)
    _created_log_handlers.add(handler)


def classFactory(iface):

    # Setup logging
    setup_logging()

    return OFDSDedupPlugin()
