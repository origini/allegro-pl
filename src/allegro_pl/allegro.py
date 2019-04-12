import logging
import typing

import allegro_api.configuration
import allegro_api.rest
import tenacity
import zeep

from .oauth import AllegroAuth

logger = logging.getLogger(__name__)


class Allegro:
    def __init__(self, auth_handler: AllegroAuth):
        self._webapi_session_handle: typing.Optional[str] = None

        self.oauth = auth_handler
        self.oauth.set_token_update_handler(self._on_token_updated)

        self._init_rest_client()
        self._init_webapi_client()

    def _init_rest_client(self):
        config = allegro_api.configuration.Configuration()
        config.host = 'https://api.allegro.pl'
        config.access_token = self.oauth.token_store.access_token

        self.oauth.configuration = config
        self._rest_client = allegro_api.ApiClient(config)

    def _init_webapi_client(self):
        self._webapi_client = zeep.client.Client('https://webapi.allegro.pl/service.php?wsdl')

    def _on_token_updated(self):
        ts = self.oauth.token_store
        self._rest_client.configuration.access_token = ts.access_token
        self._webapi_client_login()

    def rest_api_client(self) -> allegro_api.ApiClient:
        """:return OAuth2 authenticated REST client"""
        return self._rest_client

    def webapi_client(self):
        """:return authenticated SOAP (WebAPI) client"""
        return self._webapi_client

    def _retry_refresh_token(self, retry_state) -> None:
        if retry_state.attempt_number <= 1:
            return

        self.oauth.refresh_token()

    def retry(self, fn):
        """Decorator to handle expired access token exceptions.

        Example:

        .. code-block:: python
            allegro = allegro_api.Allegro(...)
            @allegro.retry
            def get_cats(**kwargs):
                return self._cat_api.get_categories_using_get(**kwargs)

        """

        return tenacity.retry(
            retry=AllegroAuth.token_needs_refresh,
            before=self._retry_refresh_token,
            stop=tenacity.stop_after_attempt(2)
        )(fn)

    def _webapi_client_login(self):
        if not self._webapi_client:
            return

        @self.retry
        def do_webapi_client_login():
            logger.info('Login to webapi')
            self._webapi_session_handle = self._webapi_client.service.doLoginWithAccessToken(
                self.oauth.token_store.access_token, 1, self.oauth.client_id).sessionHandlePart

        do_webapi_client_login()

    @property
    def webapi_session_handle(self):
        return self._webapi_session_handle
