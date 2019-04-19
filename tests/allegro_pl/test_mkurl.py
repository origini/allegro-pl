from unittest import TestCase
from allegro_pl.oauth import mkurl


class TestMkurl(TestCase):
    def test_mkurl_simple(self):
        result = mkurl('prefix', {'a': 'b'})
        self.assertEqual('prefix?a=b', result)

    def test_mkurl_params_none(self):
        self.assertEqual('prefix', mkurl('prefix', None))

    def test_mkurl_params_empty(self):
        self.assertEqual('prefix', mkurl('prefix', {}))

    def test_mkurl_params_sublist(self):
        self.assertEqual('prefix?a=b&a=c', mkurl('prefix', {'a': ['b', 'c']}))
