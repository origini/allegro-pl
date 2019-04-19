import contextlib
from io import StringIO
from unittest import TestCase
from unittest.mock import patch, Mock

import sys
from allegro_pl import AuthorizationCodeAuth, ClientCodeStore, TokenStore, TokenError
from oauthlib.oauth2.rfc6749.errors import CustomOAuth2Error
from requests_oauthlib import OAuth2Session


class TestAuthorizationCodeAuth(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import logging
        import sys
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

    def test_refresh_token(self):
        class MyAllegroAuth(AuthorizationCodeAuth):
            def fetch_token(self) -> None:
                raise TokenError()

        with patch.object(OAuth2Session, 'refresh_token',
                          side_effect=CustomOAuth2Error(error='invalid_token',
                                                        description='Invalid refresh token: [SENSITIVE DATA]')):
            under_test = MyAllegroAuth(ClientCodeStore('client_id', 'client_secret'), TokenStore(), 'redirect_uri')

            try:
                under_test.refresh_token()
            except TokenError:
                buf = StringIO()
                with contextlib.redirect_stderr(buf):
                    sys.excepthook(*sys.exc_info())
                self.assertNotIn('[SENSITIVE DATA]', buf.getvalue())
            else:
                self.fail()

    def test_refresh_token_unknown_exception(self):
        class MyAllegroAuth(AuthorizationCodeAuth):
            def fetch_token(self) -> None:
                raise NotImplementedError()

        with patch.object(OAuth2Session, 'refresh_token', side_effect=Exception('UNKNOWN')):
            tested = MyAllegroAuth(ClientCodeStore('client_id', 'client_secret'), TokenStore(), 'redirect_uri')

            self.assertRaises(Exception, tested.refresh_token)
