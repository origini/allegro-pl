import logging
import typing

import tenacity
import zeep
import zeep.exceptions

from .utils import is_connection_aborted

logger = logging.getLogger(__name__)


class SoapApiProxy:
    def __init__(self, client, decorator, login_decorator):
        """
        :param client: soap client
        :param decorator: decorator function that refreshes SOAP session on errors
        :param login_decorator: decorator function that refreshes OAuth session on SOAP login error, so we don't call
            login in recurrence
        """

        self._client = client
        self._decorator = decorator

        self.doLoginWithAccessToken = login_decorator(client.doLoginWithAccessToken)

    def __getattr__(self, name: str):
        result = self._decorator(getattr(self._client, name))
        setattr(self, name, result)
        return result

    def __dir__(self) -> typing.Iterable[str]:
        return dir(self._client)


class SoapHandler:
    def __init__(self, api_uri: str, client_id: str, refresh_access_token_fn):
        self._webapi_client = zeep.client.Client(api_uri)
        self._client_cache = {}
        self._refresh_access_token_fn = refresh_access_token_fn
        self._client_id = client_id
        self._webapi_session_handle: typing.Optional[str] = None
        self._access_token: typing.Optional[str] = None

        def before_call(retry_state: tenacity.RetryCallState):
            self._refresh_access_token_fn(retry_state)

        self._login_decorator = self._get_retrying(before_call).wraps

    def _set_access_token(self, value: str) -> None:
        if self._access_token != value:
            self._webapi_session_handle = None
        self._access_token = value

    access_token = property(fset=_set_access_token)

    @property
    def webapi_session_handle(self):
        return self._webapi_session_handle

    def client(self, country_code):
        """:return authenticated SOAP (WebAPI) client"""
        if country_code in self._client_cache:
            return self._client_cache[country_code]
        else:
            soap_client = SoapApiProxy(self._webapi_client.service, self._get_decorator(country_code),
                                       self._get_login_decorator())
            soap_client.get_type = self._webapi_client.get_type
            self._client_cache[country_code] = soap_client
            return soap_client

    def _get_login_decorator(self):
        def before_call(retry_state: tenacity.RetryCallState):
            # print(dir(retry_state.fn))
            self._refresh_access_token_fn(retry_state)

        return self._get_retrying(before_call).wraps

    def _get_decorator(self, country_code):
        def before_call(retry_state: tenacity.RetryCallState):
            # print(dir(retry_state.fn))
            if self._webapi_session_handle is None:
                self._login(country_code)

            else:
                self._refresh_access_token_fn(retry_state)

        return self._get_retrying(before_call).wraps

    @staticmethod
    def _get_retrying(before_fn):
        return tenacity.Retrying(
            retry=token_needs_refresh,
            before=before_fn,
            stop=tenacity.stop_after_attempt(2),
            reraise=True,
        )

    def _login(self, cc):
        logger.info('Login to webapi')
        client = self.client(cc)
        login_result = client.doLoginWithAccessToken(self._access_token, cc, self._client_id)
        self._webapi_session_handle = login_result.sessionHandlePart


def token_needs_refresh(retry_state: tenacity.RetryCallState) -> bool:
    x = retry_state.outcome.exception(0)
    if x is None:
        return False
    elif isinstance(x, zeep.exceptions.Fault):
        logger.warning("%s - %s", x.code, x.message)
        return x.code == 'ERR_INVALID_ACCESS_TOKEN' or x.code == 'ERR_NO_SESSION'
    elif isinstance(x, zeep.exceptions.ValidationError):
        logger.warning("%s %s", x.message, x.path)
        return x.message == 'Missing element sessionHandle'
    elif is_connection_aborted(x):
        return True
    else:
        return False



