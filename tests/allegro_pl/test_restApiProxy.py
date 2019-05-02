from unittest import TestCase
from unittest.mock import Mock

import allegro_api
from allegro_pl.rest import RestApiProxy


class TestClass:
    def test_method(self):
        pass


class TestRestApiProxy(TestCase):
    def test_attribute_returns_proxy(self):
        client_mock = Mock()
        decorator_mock = Mock()
        p = RestApiProxy(allegro_api.api, decorator_mock, client_mock)
        r = p.PublicOfferInformationApi

        # print(r)

        self.assertIsInstance(r, RestApiProxy)
        self.assertIsInstance(r._target, allegro_api.api.PublicOfferInformationApi)

    def test_callable(self):
        def decorator(a):
            return a

        decorator = Mock().wraps(decorator)
        test = Mock().wraps(TestClass())

        api_client = Mock()
        p = RestApiProxy(test, decorator, api_client)

        p.test_method()

        decorator.assert_called_once()
