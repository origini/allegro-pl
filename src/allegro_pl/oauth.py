import abc
import concurrent.futures
import json
import typing

import allegro_api.rest
import oauthlib.oauth2
import requests_oauthlib
import zeep.exceptions

URL_TOKEN = 'https://allegro.pl/auth/oauth/token'


class TokenStore(abc.ABC):
    def __init__(self):
        self._access_token: typing.Optional = None
        self._refresh_token: typing.Optional = None

    @abc.abstractmethod
    def save(self):
        pass

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
    def from_dict(cls: type, data: dict) -> 'TokenStore':
        ts = cls()
        ts.update_from_dict(data)
        return ts

    def update_from_dict(self, data: dict) -> None:
        self._access_token = data.get('access_token')
        self._refresh_token = data.get('refresh_token')

    def to_dict(self):
        d = {}
        if self._access_token:
            d['access_token'] = self._access_token
        if self._refresh_token:
            d['refresh_token'] = self._refresh_token
        return d


class PassTokenStore(TokenStore):
    """In-memory Token store implementation"""

    def save(self):
        pass


class AllegroAuth:
    """Handle acquiring and refreshing access_token"""

    def __init__(self, client_id: str, client_secret: str, token_store: TokenStore):
        self.client_id: str = client_id
        self.client_secret: str = client_secret

        assert token_store is not None
        self._token_store = token_store

        self._config: allegro_api.configuration.Configuration = None

    @abc.abstractmethod
    def fetch_token(self):
        pass

    def configure(self, config: allegro_api.configuration.Configuration):
        """Keep the access_token in allegro_api configuration up to date"""
        self._config = config
        self.update_configuration()

    def update_configuration(self):
        if self._config:
            self._config.access_token = self._token_store.access_token

    def retry_refresh_token(self, _, attempt) -> None:
        if attempt <= 1:
            return

        self.refresh_token()

    @abc.abstractmethod
    def refresh_token(self):
        pass

    @staticmethod
    def token_needs_refresh(f: concurrent.futures.Future) -> bool:
        x = f.exception(0)
        if x is None:
            return False
        if isinstance(x, allegro_api.rest.ApiException) and x.status == 401:
            body = json.loads(x.body)
            return body['error'] == 'invalid_token' and body['error_description'].startswith('Access token expired: ')
        elif isinstance(x, zeep.exceptions.Fault):
            if x.code == 'ERR_INVALID_ACCESS_TOKEN':
                return True
            else:
                raise x
        else:
            raise x


class ClientCredentialsAuth(AllegroAuth):
    """Authenticate with Client credentials flow"""

    def __init__(self, client_id, client_secret):
        super().__init__(client_id, client_secret, PassTokenStore())

        client = oauthlib.oauth2.BackendApplicationClient(self.client_id, access_token=self._token_store.access_token)

        self.oauth = requests_oauthlib.OAuth2Session(client=client, token_updater=self._token_store.access_token)

    def fetch_token(self):
        token = self.oauth.fetch_token(URL_TOKEN, client_id=self.client_id,
                                       client_secret=self.client_secret)

        self._token_store.access_token = token['access_token']

    def refresh_token(self):
        return self.fetch_token()
