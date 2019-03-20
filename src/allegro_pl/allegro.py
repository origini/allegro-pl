import allegro_api.configuration
import allegro_api.rest
import tenacity
import zeep

from .oauth import AllegroAuth


class Allegro:
    def __init__(self, client_id, client_secret):
        self.oauth: AllegroAuth = AllegroAuth(client_id, client_secret)

    def rest_api_client(self):
        config = allegro_api.configuration.Configuration()
        config.host = 'https://api.allegro.pl'

        self.oauth.configure(config)
        return allegro_api.ApiClient(config)

    def retry(self, fn):
        return tenacity.retry(
            retry=AllegroAuth.token_needs_refresh,
            before=self.oauth.refresh_token,
            stop=tenacity.stop_after_attempt(2)
        )(fn)

    def web_api_client(self):
        zeep.client.Client('https://webapi.allegro.pl/service.php?wsdl')
