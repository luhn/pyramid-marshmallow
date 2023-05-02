from datetime import date as Date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from marshmallow import Schema, fields
from pyramid.httpexceptions import HTTPNoContent

from pyramid_marshmallow import view_marshaller


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


@pytest.fixture
def wrap_view():
    def wrap(view):
        info = SimpleNamespace(
            options={
                "marshal": AlbumSchema(),
            }
        )
        return view_marshaller(view, info)

    return wrap


def test_marshal(wrap_view):
    unwrapped = Mock(
        return_value={
            "title": "Hunky Dory",
            "release_date": Date(1971, 12, 17),
        }
    )
    view = wrap_view(unwrapped)
    assert view("context", "request") == {
        "title": "Hunky Dory",
        "release_date": "1971-12-17",
    }
    unwrapped.assert_called_once_with("context", "request")


def test_marshal_http_response(wrap_view):
    unwrapped = Mock(return_value=HTTPNoContent())
    view = wrap_view(unwrapped)
    resp = view("context", "request")
    assert isinstance(resp, HTTPNoContent)
