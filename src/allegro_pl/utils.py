import logging

import requests

logger = logging.getLogger(__name__)


def is_connection_aborted(x) -> bool:
    if isinstance(x, requests.exceptions.ConnectionError):
        logger.warning(x.args[0].args[0])
        return x.args[0].args[0] == 'Connection aborted.'
    else:
        return False
