import logging

import allegro_api.rest
import allegro_pl.rest
import allegro_pl.soap
import zeep.client

from .oauth import AllegroAuth

logger = logging.getLogger(__name__)


class Allegro:
    def __init__(self, auth_handler: AllegroAuth):
        self._auth = auth_handler
        self._auth.notify_token_updated = self._on_token_updated

        self._rest_client, self._rest_service = allegro_pl.rest.get_client_and_service('https://api.allegro.pl',
                                                                                       self._auth.retry_refresh_token)
        self._soap_client, self._soap_service = allegro_pl.soap.get_client_and_service(
            'https://webapi.allegro.pl/service.php?wsdl',
            auth_handler.client_id,
            1,
            self._auth.retry_refresh_token
        )

        self._on_token_updated()

    def _on_token_updated(self) -> None:
        self._rest_service.access_token = self._auth.token_store.access_token
        self._soap_service.access_token = self._auth.token_store.access_token

    def rest_client(self) -> allegro_api.ApiClient:
        """:return OAuth2 authenticated REST client"""
        return self._rest_client

    def rest_service(self) -> allegro_pl.rest.AllegroRestService:
        return self._rest_service

    def soap_client(self) -> zeep.client.Client:
        return self._soap_client

    def soap_service(self) -> allegro_pl.soap.AllegroSoapService:
        return self._soap_service

    def _retry_refresh_token(self, retry_state) -> None:
        if retry_state.attempt_number <= 1:
            return

        self._auth.refresh_token()
