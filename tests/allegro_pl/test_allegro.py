from unittest import TestCase
from unittest.mock import Mock

from allegro_pl import Allegro, AllegroAuth, ClientCodeStore, TokenStore


class MyAllegroAuth(AllegroAuth):
    def fetch_token(self) -> None:
        raise NotImplementedError()

    def refresh_token(self) -> None:
        raise NotImplementedError()


class TestAllegro(TestCase):
    def test_init_initializes_clients(self):
        Allegro._init_rest_client = Mock()
        Allegro._init_webapi_client = Mock()
        allegro_auth = Mock()
        a = Allegro(allegro_auth)
        a._init_rest_client.assert_called_once_with()
        a._init_webapi_client.assert_called_once_with()

    def test__on_token_updated(self):
        Allegro._webapi_client_login = Mock()
        a = Allegro(MyAllegroAuth(ClientCodeStore('client id', 'client secret'), TokenStore('access token')))

        a._on_token_updated()

        a._webapi_client_login.assert_called_once_with()
        self.assertEqual('access token', a._rest_client.configuration.access_token)
