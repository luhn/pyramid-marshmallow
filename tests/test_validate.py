import pytest
from unittest.mock import Mock
from types import SimpleNamespace
from marshmallow import Schema, fields, ValidationError
from datetime import date as Date
from pyramid.testing import DummyRequest
from webob.multidict import MultiDict

from pyramid_marshmallow import view_validator


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


@pytest.fixture
def view():
    return Mock()


@pytest.fixture
def wrapped(view):
    info = SimpleNamespace(options={
        'validate': AlbumSchema(),
    })
    return view_validator(view, info)


def test_no_validate():
    view = Mock()
    info = SimpleNamespace(options={})
    assert view_validator(view, info) is view


def test_validate(wrapped, view):
    request = DummyRequest()
    request.method = 'POST'
    request.json_body = {
        'title': 'Hunky Dory',
        'release_date': '1971-12-17',
    }
    context = object()
    wrapped(context, request)
    view.assert_called_once_with(context, request)
    assert request.data == {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }


def test_validate_get(wrapped, view):
    request = DummyRequest()
    request.method = 'GET'
    request.GET = MultiDict({
        'title': 'Hunky Dory',
        'release_date': '1971-12-17',
    })
    context = object()
    wrapped(context, request)
    view.assert_called_once_with(context, request)
    assert request.data == {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }


def test_validate_error(wrapped, view):
    """
    Technically not necessary, since we just let marshmallow use its own error
    handling.  However, our documentation makes claims on how this works, so we
    test it.

    """
    request = DummyRequest()
    request.method = 'POST'
    request.json_body = {
        'title': 'Hunky Dory',
        'release_date': '1971-14-17',
    }
    context = object()
    with pytest.raises(ValidationError) as exc:
        wrapped(context, request)
    assert exc.value.messages == {'release_date': ['Not a valid date.']}
    assert(
        exc.value.normalized_messages()
        == {'release_date': ['Not a valid date.']}
    )
