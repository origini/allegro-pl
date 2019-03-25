import allegro_api.configuration
import allegro_api.rest
import tenacity
import zeep

from .oauth import AllegroAuth


class Allegro:
    def __init__(self, auth_handler: AllegroAuth):
        self.oauth = auth_handler
        if not self.oauth._token_store.access_token:
            if self.oauth._token_store.refresh_token:
                self.oauth.refresh_token()
            else:
                self.oauth.fetch_token()

        self._webclient = zeep.client.Client('https://webapi.allegro.pl/service.php?wsdl')
        if self.oauth._token_store.access_token:
            @self.retry
            def doLoginWithAccessToken(*args, **kwargs):
                self._webclient.service.doLoginWithAccessToken(*args, **kwargs)

            self.webapi_key = doLoginWithAccessToken(self.oauth._token_store.access_token, 1, self.oauth.client_id)

    def rest_api_client(self) -> allegro_api.ApiClient:
        """:return OAuth2 authenticated REST client"""
        config = allegro_api.configuration.Configuration()
        config.host = 'https://api.allegro.pl'

        self.oauth.configure(config)
        return allegro_api.ApiClient(config)

    def webapi_client(self):
        """:return authenticated SOAP (WebAPI) client"""
        return self._webclient

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
            before=self.oauth.retry_refresh_token,
            stop=tenacity.stop_after_attempt(2)
        )(fn)
