Python client for Allegro.pl API
================================

Supports both Rest and SOAP APIs

Usage:

.. highlights::

    client_id = os.environ['ALLEGRO_CLIENT_ID']
    client_secret = os.environ['ALLEGRO_CLIENT_SECRET']

    auth = ClientCredentialsAuth(client_id, client_secret)
    client_factory = allegro_pl.Allegro(auth)

    rest_client = client_factory.rest_api_client()
    soap_client = client_factory.webapi_client()
