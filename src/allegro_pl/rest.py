import json
import logging
import typing

import allegro_api
import allegro_api.rest
import oauthlib
import oauthlib.oauth2
import tenacity

from .utils import is_connection_aborted

logger = logging.getLogger(__name__)


class RestApiProxy:
    def __init__(self, target, decorator_fn, api_client: typing.Optional[allegro_api.ApiClient]):
        self._target = target
        self._api_client = api_client
        self._decorator_fn = decorator_fn
        self._object_cache = {}

    def __getattr__(self, name):
        if name in self._object_cache:
            return self._object_cache[name]
        else:
            attr = getattr(self._target, name)
            if isinstance(attr, type):
                obj = attr(self._api_client)
                obj = RestApiProxy(obj, self._decorator_fn, None)
            elif callable(attr):
                obj = self._decorator_fn(attr)
            else:
                obj = attr

            self._object_cache[name] = obj
            return obj



    def __dir__(self) -> typing.Iterable[str]:
        return dir(self._target)


class RestHandler:
    def __init__(self, api_uri: str, refresh_token_fn):
        self._config = config = allegro_api.configuration.Configuration()
        config.host = api_uri

        self._refresh_token = refresh_token_fn

        self._client = RestApiProxy(allegro_api.api,
                                         self._retry_rest,
                                         allegro_api.ApiClient(config))

    def client(self):
        return self._client

    def set_access_token(self, access_token: str):
        self._config.access_token = access_token

    access_token = property(fset=set_access_token)

    def _retry_rest(self, fn):
        return tenacity.retry(
            retry=_token_needs_refresh,
            before=self._refresh_token,
            stop=tenacity.stop_after_attempt(2),
            reraise=True,
        )(fn)


def _token_needs_refresh(retry_state: tenacity.RetryCallState) -> bool:
    x = retry_state.outcome.exception(0)
    if x is None:
        return False
    if isinstance(x, oauthlib.oauth2.rfc6749.errors.InvalidGrantError):
        return True
    if isinstance(x, allegro_api.rest.ApiException) and x.status == 401:
        body = json.loads(x.body)
        logger.warning(body['error'])
        return body['error'] == 'invalid_token' and body['error_description'].startswith('Access token expired: ')
    elif is_connection_aborted(x):
        return True
    else:
        return False
