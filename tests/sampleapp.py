import pytest
from webtest import TestApp

from pyramid.config import Configurator
from pyramid.response import Response


def hello_world(request):
    return Response('Hello World!')


@pytest.fixture(scope='session')
def wsgi():
    with Configurator() as config:
        config.include('pyramid_apispec')
        config.add_route('hello', '/hello')
        config.add_view(hello_world, route_name='hello')
        return config.make_wsgi_app()


@pytest.fixture(scope='session')
def app(wsgi):
    return TestApp(wsgi)
