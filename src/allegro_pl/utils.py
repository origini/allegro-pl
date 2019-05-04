import logging

logger = logging.getLogger(__name__)


def is_connection_aborted(x: Exception) -> bool:
    import requests
    if isinstance(x, requests.exceptions.ConnectionError):
        logger.warning(x.args[0].args[0])
        return x.args[0].args[0] == 'Connection aborted.'
    else:
        return False
