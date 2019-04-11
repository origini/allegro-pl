from unittest import TestCase

from allegro_pl import ClientCodeStore


class TestClientCodeStore(TestCase):
    def test_client_id(self):
        cs = ClientCodeStore('client_id', None)
        self.assertEqual('client_id', cs.client_id)

    def test_client_secret(self):
        cs = ClientCodeStore(None, 'client_secret')
        self.assertEqual('client_secret', cs.client_secret)
