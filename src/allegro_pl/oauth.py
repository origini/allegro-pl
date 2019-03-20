import json
from concurrent import futures

import allegro_api.rest
import oauthlib.oauth2
import requests_oauthlib


class AllegroAuth:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self._access_token: str = None
        self._config: allegro_api.configuration.Configuration = None

        client = oauthlib.oauth2.BackendApplicationClient(self.client_id, access_token=self.access_token)

        self.oauth = requests_oauthlib.OAuth2Session(client=client, token_updater=self.access_token)
        self.fetch_token()

    @property
    def access_token(self) -> str:
        return self._access_token

    @access_token.setter
    def access_token(self, access_token: str) -> None:
        self._access_token = access_token
        self.update_configuration()

    def fetch_token(self):
        token = self.oauth.fetch_token('https://allegro.pl/auth/oauth/token', client_id=self.client_id,
                                       client_secret=self.client_secret)

        self.access_token = token['access_token']

    def configure(self, config: allegro_api.configuration.Configuration):
        self._config = config
        self.update_configuration()

    def update_configuration(self):
        if self._config:
            self._config.access_token = self._access_token

    def refresh_token(self, _, attempt) -> None:
        if attempt <= 1:
            return

        self.fetch_token()

    @staticmethod
    def token_needs_refresh(f: futures.Future) -> bool:
        x = f.exception(0)
        if isinstance(x, allegro_api.rest.ApiException) and x.status == 401:
            body = json.loads(x.body)
            return body['error'] == 'invalid_token' and body['error_description'].startswith('Access token expired: ')
        else:
            return False
