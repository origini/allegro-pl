Python client for Allegro.pl API
================================

Supports both Rest and SOAP APIs

Usage:

.. code-block:: python

    client_id = os.environ['ALLEGRO_CLIENT_ID']
    client_secret = os.environ['ALLEGRO_CLIENT_SECRET']

    auth = ClientCredentialsAuth(client_id, client_secret)
    allegro = allegro_pl.Allegro(auth)

    rest_client = allegro.rest_api_client()
    soap_client = allegro.webapi_client()

    cat_service = allegro_api.api.CategoriesAndParametersApi(rest_client)

    # retry will authenticate the client in REST and SOAP services nad call the metod once again
    @allegro.retry
    def get_categories(**kwargs):
        return cat_service.get_categories_using_get(**kwargs)
