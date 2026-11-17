from datetime import date as Date

from marshmallow import Schema, fields
from pyramid.httpexceptions import HTTPCreated
from pyramid.response import Response


def includeme(config):
    config.include("pyramid_marshmallow")

    # Traversal
    config.set_root_factory(Root)
    config.add_view(hello_world, context=Root, name="hello")
    config.add_view(
        list,
        context=AlbumContainer,
        marshal={
            "items": fields.List(fields.Nested(AlbumSchema)),
        },
        renderer="json",
    )
    config.add_view(
        view,
        context=Album,
        request_method="GET",
        marshal=AlbumSchema(),
        renderer="json",
    )
    config.add_view(
        update,
        context=Album,
        request_method="POST",
        validate=AlbumSchema(),
        marshal=AlbumSchema(),
        renderer="json",
    )
    config.add_view(
        update,
        context=Album,
        name="like",
        request_method="POST",
        renderer="json",
    )

    return config


class AlbumSchema(Schema):
    """
    Information about an album.

    """

    id = fields.Integer(dump_only=True)
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


def list(context, request):
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


def view(context, request):
    return {
        "id": context.album_id,
        "title": "Hunky Dory",
        "release_date": Date(1971, 12, 17),
    }


def update(context, request):
    assert request.data == {
        "title": "Hunky Dory",
        "release_date": Date(1971, 12, 17),
    }
    return {
        "id": context.album_id,
        "title": "Hunky Dory",
        "release_date": Date(1971, 12, 17),
    }


def like(context, request):
    """
    Indicate that you like an album.

    ---
    responses:
        201:
            description: |
                Indicates that the like was successfully recorded.

    """
    return HTTPCreated()
