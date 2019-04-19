import json
from unittest import TestCase

import allegro_api.rest
import requests
import tenacity
import zeep.exceptions
from allegro_pl import AllegroAuth, ClientCodeStore, TokenStore
import unittest.mock


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

    def test_token_needs_refresh(self):
        def retry_state(e) -> tenacity.RetryCallState:
            state = tenacity.RetryCallState(None, None, [], {})
            state.set_exception((type(e), e, None))
            return state

        def make_connection_error(message):
            class MyCause:
                pass

            my_cause = MyCause
            my_cause.args = [message]

            return requests.exceptions.ConnectionError(my_cause)

        under_test = MyAllegroAuth(ClientCodeStore('', ''), TokenStore())

        exception = allegro_api.rest.ApiException(401)
        exception.body = json.dumps({'error': 'invalid_token', 'error_description': 'Access token expired: '})
        self.assertTrue(under_test.token_needs_refresh(retry_state(exception)))

        exception = allegro_api.rest.ApiException(401)
        exception.body = json.dumps({'error': 'other_problem', 'error_description': 'Access token expired: '})
        self.assertFalse(under_test.token_needs_refresh(retry_state(exception)))

        self.assertTrue(under_test.token_needs_refresh(
            retry_state(zeep.exceptions.Fault('Some message', 'ERR_INVALID_ACCESS_TOKEN'))))

        self.assertTrue(
            under_test.token_needs_refresh(retry_state(zeep.exceptions.Fault('Some message', 'ERR_NO_SESSION'))))

        self.assertFalse(
            under_test.token_needs_refresh(retry_state(zeep.exceptions.Fault('Some message', 'OTHER_PROBLEM'))))

        self.assertTrue(under_test.token_needs_refresh(
            retry_state(zeep.exceptions.ValidationError(message='Missing element sessionHandle'))))

        self.assertFalse(
            under_test.token_needs_refresh(retry_state(zeep.exceptions.ValidationError(message='Other problem'))))

        self.assertTrue(under_test.token_needs_refresh(retry_state(make_connection_error('Connection aborted.'))))
        self.assertFalse(under_test.token_needs_refresh(retry_state(make_connection_error('Other problem.'))))

    def test_client_id(self):
        under_test = MyAllegroAuth(ClientCodeStore('client id', ''), TokenStore())
        self.assertEqual('client id', under_test.client_id)
