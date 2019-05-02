from unittest import TestCase
from unittest.mock import Mock

import pytest
from allegro_pl.oauth import TokenStore

from allegro_pl.soap import SoapApiProxy


class MyAuthHook:
    def __init__(self, refresh_fn):
        self.client_id = 'client id'
        self.access_token = 'access token'
        self.rest_relogin_wrapper = refresh_fn

@pytest.mark.xfail
class TestSoapApiProxy(TestCase):

    def test_login(self):
        def wrapper(fn):
            return fn

        c = SoapApiProxy(Mock(), MyAuthHook(wrapper), 1)
        with self.assertRaises(AttributeError):
            c.doLoginWithAccessToken()

    def test_get_items_info(self):
        def wrapper(fn):
            return fn

        client_mock = Mock()
        c = SoapApiProxy(client_mock, MyAuthHook(wrapper), 1)
        c._session_handle = 'session handle'

        # with self.assertRaises(AttributeError):
        c.doGetItemsInfo(itemsIdArray=[1, 2], getDesc=1)

        client_mock.doGetItemsInfo.assert_called_once_with('session handle', getDesc=1,
                                                           itemsIdArray=[1, 2])
