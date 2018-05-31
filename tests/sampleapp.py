import pytest
from webtest import TestApp
from datetime import date as Date
from marshmallow import Schema, fields

from pyramid.config import Configurator
from pyramid.response import Response


class AlbumSchema(Schema):
    """
    Information about an album.

    """
    title = fields.Str()
    release_date = fields.Date(allow_null=True)


class Root(dict):
    def __init__(self, request):
        super().__init__({
            'traversal': Traversal(request),
        })


class Traversal(dict):
    def __init__(self, request):
        super().__init__()


def hello_world(request):
    return Response('Hello World!')


def validate(request):
    assert request.data == {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }
    return Response(request.data['title'])


def marshal(request):
    """
    Returns JSON-serialized information about the album.

    """
    return {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }


def list():
    return {
        'items': [
            {
                'title': 'Hunky Dory',
                'release_date': Date(1971, 12, 17),
            },
            {
                'title': 'Spiders From Mars',
                'release_date': Date(1973, 11, 10),
            },
        ],
    }


def like():
    """
    Indicate that you like an album.

    ---
    responses:
        204:
            description: |
                Indicates that the like was successfully recorded.

    """
    return HTTPNoContent()


@pytest.fixture(scope='session')
def config():
    with Configurator(settings={}) as config:
        config.include('pyramid_apispec')

        # Hello world
        config.add_route('hello', '/hello')
        config.add_view(hello_world, route_name='hello')

        # Validator
        config.add_route('validate', '/validate')
        config.add_view(
            validate, route_name='validate', validate=AlbumSchema(),
            request_method=('GET', 'POST'),
        )

        # Marshaller
        config.add_route('marshal', '/marshal')
        config.add_view(
            marshal, route_name='marshal', marshal=AlbumSchema(),
            renderer='json',
        )

        # List
        config.add_route('list', '/list')
        config.add_view(
            list,
            route_name='list',
            marshal={
                'items': fields.Nested(AlbumSchema(many=True)),
                'whatever': fields.Str(allow_none=True),
            },
            renderer='json',
        )

        # Like
        config.add_route('like', '/like')
        config.add_view(like, route_name='like')

        # Traversal
        config.set_root_factory(Root)
        config.add_view(hello_world, context=Traversal, name='hello')
        config.add_view(
            validate, context=Traversal, name='validate',
            validate=AlbumSchema(),
        )
        config.add_view(
            marshal, context=Traversal, name='marshal', marshal=AlbumSchema(),
            renderer='json',
        )

        return config


@pytest.fixture(scope='session')
def app(config):
    wsgi = config.make_wsgi_app()
    return TestApp(wsgi)
