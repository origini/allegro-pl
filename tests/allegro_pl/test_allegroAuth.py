import unittest.mock
from unittest import TestCase

from allegro_pl import AllegroAuth, ClientCodeStore, TokenStore


class MyAllegroAuth(AllegroAuth):
    def fetch_token(self) -> None:
        raise NotImplementedError()

    def refresh_token(self) -> None:
        raise NotImplementedError()


class TestAllegroAuth(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import logging
        import sys
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

    def test__on_token_updated_calls_token_store(self):
        token_store = unittest.mock.create_autospec(TokenStore)
        under_test = MyAllegroAuth(ClientCodeStore('', ''), token_store)
        token_dict = {'access_token': 'access token', 'refresh_token': 'refresh_token'}
        under_test._on_token_updated(token_dict)
        token_store.save.assert_called_once_with()
        token_store.update_from_dict.assert_called_once_with(token_dict)

    def test__on_token_updated_calls_notify(self):
        under_test = MyAllegroAuth(ClientCodeStore('', ''), TokenStore())
        under_test.notify_token_updated = unittest.mock.Mock()
        token_dict = {'access_token': 'access token', 'refresh_token': 'refresh_token'}

        under_test._on_token_updated(token_dict)
        under_test.notify_token_updated.assert_called_once_with()

    def test_token_store(self):
        ts = TokenStore()
        under_test = MyAllegroAuth(ClientCodeStore('', ''), ts)
        self.assertEqual(ts, under_test.token_store)

    def test_client_id(self):
        under_test = MyAllegroAuth(ClientCodeStore('client id', ''), TokenStore())
        self.assertEqual('client id', under_test.client_id)
