import pytest
from webtest import TestApp
from datetime import date as Date
from marshmallow import Schema, fields

from pyramid.config import Configurator
from pyramid.response import Response


def hello_world(request):
    return Response('Hello World!')


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


def validate(request):
    assert request.data == {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }
    return Response(request.data['title'])


@pytest.fixture(scope='session')
def wsgi():
    with Configurator() as config:
        config.include('pyramid_apispec')

        # Hello world
        config.add_route('hello', '/hello')
        config.add_view(hello_world, route_name='hello')

        # Validator
        config.add_route('validate', '/validate')
        config.add_view(
            validate, route_name='validate', validate=AlbumSchema(),
        )

        return config.make_wsgi_app()


@pytest.fixture(scope='session')
def app(wsgi):
    return TestApp(wsgi)
