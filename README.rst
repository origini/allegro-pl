Python client for Allegro.pl API
================================

.. image:: https://travis-ci.com/mattesilver/allegro-pl.svg?branch=master
    :target: https://travis-ci.org/mattesilver/allegro-pl

.. image:: https://img.shields.io/pypi/v/mattes-allegro-pl.svg
    :target: https://pypi.org/project/mattes-allegro-pl/

.. image:: https://codecov.io/gh/mattesilver/allegro-pl/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/mattesilver/allegro-pl


Supports both Rest and SOAP APIs

Usage:

.. code-block::

    import allegro_pl
    cs = ClientCodeStore('CLIENT ID','CLIENT SECRET')
    ts = TokenStore('ACCESS TOKEN','REFRESH TOKEN)

    auth = ClientCredentialsAuth(cs, ts)
    allegro = allegro_pl.Allegro(auth)

    rest_client = allegro.rest_api_client()
    soap_client = allegro.webapi_client()

    cat_service = allegro_api.api.CategoriesAndParametersApi(rest_client)

    # retry will authenticate the client in REST and SOAP services nad call the metod once again
    @allegro.retry
    def get_categories(**kwargs):
        return cat_service.get_categories_using_get(**kwargs)

    categories = get_categories(...)
