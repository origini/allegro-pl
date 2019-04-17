import abc
import json
import logging
import typing

import allegro_api.rest
import oauthlib.oauth2
import requests.exceptions
import requests_oauthlib
import tenacity
import zeep.exceptions

_ACCESS_TOKEN = 'access_token'
_REFRESH_TOKEN = 'refresh_token'

URL_TOKEN = 'https://allegro.pl/auth/oauth/token'
URL_AUTHORIZE = 'https://allegro.pl/auth/oauth/authorize'

logger = logging.getLogger(__name__)


class TokenStore(abc.ABC):
    def __init__(self, access_token: str = None, refresh_token: str = None):
        self._access_token: access_token
        self._refresh_token: refresh_token

    @abc.abstractmethod
    def save(self) -> None:
        logger.debug('Save tokens')

    @property
    def access_token(self) -> str:
        return self._access_token

    @access_token.setter
    def access_token(self, access_token: str) -> None:
        self._access_token = access_token

    @property
    def refresh_token(self) -> str:
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, refresh_token: str) -> None:
        self._refresh_token = refresh_token

    @classmethod
    def from_dict(cls: typing.Type['TokenStore'], data: dict) -> 'TokenStore':
        ts = cls()
        ts.update_from_dict(data)
        return ts

    def update_from_dict(self, data: dict) -> None:
        self.access_token = data.get(_ACCESS_TOKEN)
        self.refresh_token = data.get(_REFRESH_TOKEN)

    def to_dict(self) -> dict:
        d = {}
        if self._access_token:
            d[_ACCESS_TOKEN] = self.access_token
        if self._refresh_token:
            d[_REFRESH_TOKEN] = self.refresh_token
        return d


class PassTokenStore(TokenStore):
    """In-memory Token store implementation"""

    def save(self) -> None:
        pass


class ClientCodeStore:
    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def client_secret(self) -> str:
        return self._client_secret


class AllegroAuth:
    """Handle acquiring and refreshing access_token"""

    def __init__(self, code_store: ClientCodeStore, token_store: TokenStore):
        assert code_store is not None
        self._cs = code_store

        assert token_store is not None
        self._token_store = token_store

        self._notify_token_updated: typing.Callable[[], None] = self._on_token_updated_pass

    def _on_token_updated(self, token) -> None:
        logger.debug('Token updated')
        self._token_store.update_from_dict(token)
        self._token_store.save()
        self._notify_token_updated()

    def _on_token_updated_pass(self):
        pass

    def set_token_update_handler(self, f: typing.Callable[[], None]) -> None:
        self._notify_token_updated = f

    @property
    def token_store(self) -> TokenStore:
        return self._token_store

    @staticmethod
    def token_needs_refresh(retry_state: tenacity.RetryCallState) -> bool:
        x = retry_state.outcome.exception(0)
        if x is None:
            return False
        if isinstance(x, allegro_api.rest.ApiException) and x.status == 401:
            body = json.loads(x.body)
            logger.warning(body['error'])
            return body['error'] == 'invalid_token' and body['error_description'].startswith('Access token expired: ')
        elif isinstance(x, zeep.exceptions.Fault):
            logger.warning(x.code, x.message)
            return x.code == 'ERR_INVALID_ACCESS_TOKEN'
        elif isinstance(x, requests.exceptions.ConnectionError):
            logger.warning(x.args[0].args[0])
            return x.args[0].args[0] == 'Connection aborted.'
        elif isinstance(x, zeep.exceptions.ValidationError):
            logger.warning(x.message)
            return x.message == 'Missing element sessionHandle'
        else:
            return False

    @property
    def client_id(self):
        return self._cs.client_id

    @abc.abstractmethod
    def fetch_token(self) -> None:
        logger.info('Fetch token')

    @abc.abstractmethod
    def refresh_token(self) -> None:
        logger.info('Refresh token')


class ClientCredentialsAuth(AllegroAuth):
    """Authenticate with Client credentials flow"""

    def __init__(self, code_store: ClientCodeStore):
        super().__init__(code_store, PassTokenStore())

        client = oauthlib.oauth2.BackendApplicationClient(self._cs.client_id,
                                                          access_token=self.token_store.access_token)

        self.oauth = requests_oauthlib.OAuth2Session(client=client, token_updater=self._on_token_updated)

    def fetch_token(self):
        super().fetch_token()
        token = self.oauth.fetch_token(URL_TOKEN, client_id=self._cs.client_id, client_secret=self._cs.client_secret)
        self._on_token_updated(token)

    def refresh_token(self):
        super().refresh_token()
        self.fetch_token()


class AuthorizationCodeAuth(AllegroAuth):
    def __init__(self, cs: ClientCodeStore, ts: TokenStore, redirect_uri: str):
        super().__init__(cs, ts)
        client = oauthlib.oauth2.WebApplicationClient(self._cs.client_id, access_token=self._token_store.access_token)

        self._oauth = requests_oauthlib.OAuth2Session(self._cs.client_id, client, URL_TOKEN, redirect_uri=redirect_uri,
                                                      token_updater=self._token_store.access_token)

    def refresh_token(self):
        super().refresh_token()
        from requests.auth import HTTPBasicAuth
        try:
            # OAuth2 takes data in the body, but allegro expects it in the query
            url = mkurl(URL_TOKEN,
                        {'grant_type': _REFRESH_TOKEN,
                         'refresh_token': self.token_store.refresh_token,
                         'redirect_uri': self._oauth.redirect_uri
                         })
            token = self._oauth.refresh_token(url, auth=HTTPBasicAuth(self._cs.client_id,
                                                                      self._cs.client_secret))
            self._on_token_updated(token)
        except oauthlib.oauth2.rfc6749.errors.OAuth2Error as x:
            logger.warning('Refresh token failed %s', x.error)
            if x.description == 'Full authentication is required to access this resource' \
                    or x.description.startswith('Invalid refresh token: ') \
                    or x.error == 'invalid_token':
                self.fetch_token()
            else:
                raise


def mkurl(address, query):
    from urllib.parse import urlencode
    return address + '?' + urlencode(query)
