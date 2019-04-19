from unittest import TestCase

from allegro_pl import TokenStore


class TestTokenStore(TestCase):
    def test_init(self):
        ts = TokenStore('a', 'b')
        self.assertEqual('a', ts.access_token)
        self.assertEqual('b', ts.refresh_token)

    def test_from_dict_ok(self):
        ts = TokenStore.from_dict({'access_token': 'a', 'refresh_token': 'b'})
        self.assertEqual('a', ts.access_token)
        self.assertEqual('b', ts.refresh_token)

    def test_from_dict_None(self):
        with self.assertRaises(ValueError):
            TokenStore.from_dict(None)

    def test_from_dict_empty(self):
        ts = TokenStore.from_dict({})
        self.assertIsNone(ts.access_token)
        self.assertIsNone(ts.refresh_token)

    def test_from_dict_invalid(self):
        ts = TokenStore.from_dict({'invalid_key': 'value'})
        self.assertIsNone(ts.access_token)
        self.assertIsNone(ts.refresh_token)
