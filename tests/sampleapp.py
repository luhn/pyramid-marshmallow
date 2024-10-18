from datetime import date as Date

import pytest
from marshmallow import Schema, fields
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNoContent
from pyramid.response import Response
from webtest import TestApp


class AlbumSchema(Schema):
    """
    Information about an album.

    """

    title = fields.String()
    release_date = fields.Date(allow_none=True)
    artists = fields.List(fields.String())


class Root(dict):
    def __init__(self, request):
        super().__init__(
            {
                "album": AlbumContainer(request),
            }
        )


class AlbumContainer(dict):
    __path__ = "/album"
    __tag__ = {
        "name": "album",
        "description": "A collection of songs.",
    }

    def __init__(self, request):
        self.request = request
        super().__init__()

    def __getitem__(self, key):
        if key.isdigit():
            return Album(self.request, int(key))
        return super().__getitem__(key)


class Album(dict):
    __path__ = "/album/{albumId}"
    __params__ = [
        {
            "name": "albumId",
            "description": "The ID of the album.",
            "schema": {
                "type": "integer",
            },
        }
    ]
    __tag__ = "album"

    def __init__(self, request, album_id):
        self.album_id = album_id


def hello_world(request):
    return Response("Hello World!")


def validate(request):
    assert request.data == {
        "title": "Hunky Dory",
        "release_date": Date(1971, 12, 17),
    }
    return Response(request.data["title"])


def validate_list(request):
    assert request.data == {
        "title": "Hunky Dory",
        "artists": ["Bowie", "Wowie"],
    }
    return Response(", ".join(request.data["artists"]))


def marshal(request):
    """
    Returns JSON-serialized information about the album.

    """
    return {
        "title": "Hunky Dory",
        "release_date": Date(1971, 12, 17),
    }


def list():
    return {
        "items": [
            {
                "title": "Hunky Dory",
                "release_date": Date(1971, 12, 17),
            },
            {
                "title": "Spiders From Mars",
                "release_date": Date(1973, 11, 10),
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


@pytest.fixture(scope="session")
def config():
    with Configurator(settings={}) as config:
        config.include("pyramid_marshmallow")

        # Hello world
        config.add_route("hello", "/hello")
        config.add_view(hello_world, route_name="hello")

        # Validator
        config.add_route("validate", "/validate")
        config.add_view(
            validate,
            route_name="validate",
            validate=AlbumSchema(),
            request_method=("GET", "POST"),
        )

        config.add_route("validate-list", "/validate-list")
        config.add_view(
            validate_list,
            route_name="validate-list",
            validate=AlbumSchema(),
            request_method=("GET", "POST"),
        )

        # Marshaller
        config.add_route("marshal", "/marshal")
        config.add_view(
            marshal,
            route_name="marshal",
            marshal=AlbumSchema(),
            renderer="json",
        )

        # List
        config.add_route("list", "/list")
        config.add_view(
            list,
            route_name="list",
            marshal={
                "items": fields.Nested(AlbumSchema(many=True)),
                "whatever": fields.Str(allow_none=True),
            },
            renderer="json",
        )

        # Traversal
        config.set_root_factory(Root)
        config.add_view(hello_world, context=AlbumContainer, name="hello")
        config.add_view(like, context=Album, name="like")
        config.add_view(
            validate,
            context=Album,
            name="validate",
            validate=AlbumSchema(),
        )
        config.add_view(
            marshal,
            context=Album,
            name="marshal",
            marshal=AlbumSchema(),
            renderer="json",
        )

        return config


@pytest.fixture(scope="session")
def app(config):
    wsgi = config.make_wsgi_app()
    return TestApp(wsgi)
