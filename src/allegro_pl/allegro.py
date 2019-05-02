import logging

import allegro_api
import tenacity

from .oauth import AllegroAuth
from .rest import RestHandler
from .soap import SoapHandler

logger = logging.getLogger(__name__)


class Allegro:
    def __init__(self, auth_handler: AllegroAuth):
        self._auth = auth_handler
        self._auth.notify_token_updated = self._on_token_updated

        self._rest_handler = RestHandler('https://api.allegro.pl', self._auth.retry_refresh_token)
        self._soap_handler = SoapHandler('https://webapi.allegro.pl/service.php?wsdl',
                                         auth_handler.client_id,
                                         self._auth.retry_refresh_token
                                         )

        self._on_token_updated()

    def _on_token_updated(self):
        self._rest_handler.access_token = self._auth.token_store.access_token
        self._soap_handler.access_token = self._auth.token_store.access_token

    def rest_api_client(self) -> allegro_api.api:
        """:return OAuth2 authenticated REST client"""

        return self._rest_handler.client()

    def webapi_client(self, country_code=1):
        """:return authenticated SOAP (WebAPI) client"""

        return self._soap_handler.client(country_code)

    @property
    def webapi_session_handle(self):
        return self._soap_handler.webapi_session_handle
