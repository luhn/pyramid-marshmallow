from datetime import date as Date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from marshmallow import Schema, ValidationError, fields
from pyramid.testing import DummyRequest
from webob.multidict import MultiDict

from pyramid_marshmallow import view_validator


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


class TaggedAlbumSchema(AlbumSchema):
    tags = fields.List(fields.Str())


class TestViewValidator:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.view = Mock()
        self.context = object()

    def wrap(self, **options):
        info = SimpleNamespace(options=options)
        return view_validator(self.view, info)

    def post(self, body):
        request = DummyRequest()
        request.method = "POST"
        request.json_body = body
        return request

    def get(self, params):
        request = DummyRequest()
        request.method = "GET"
        request.GET = MultiDict(params)
        return request

    def test_no_validate(self):
        assert self.wrap() is self.view

    def test_validate_none(self):
        assert self.wrap(validate=None) is self.view

    def test_post(self):
        wrapped = self.wrap(validate=AlbumSchema())
        request = self.post(
            {
                "title": "Hunky Dory",
                "release_date": "1971-12-17",
            }
        )
        result = wrapped(self.context, request)
        self.view.assert_called_once_with(self.context, request)
        assert result is self.view.return_value
        assert request.data == {
            "title": "Hunky Dory",
            "release_date": Date(1971, 12, 17),
        }

    def test_get(self):
        wrapped = self.wrap(validate=AlbumSchema())
        request = self.get(
            {
                "title": "Hunky Dory",
                "release_date": "1971-12-17",
            }
        )
        wrapped(self.context, request)
        self.view.assert_called_once_with(self.context, request)
        assert request.data == {
            "title": "Hunky Dory",
            "release_date": Date(1971, 12, 17),
        }

    def test_get_list(self):
        wrapped = self.wrap(validate=TaggedAlbumSchema())
        request = self.get(
            [
                ("title", "Hunky Dory"),
                ("tags", "glam"),
                ("tags", "art pop"),
            ]
        )
        wrapped(self.context, request)
        assert request.data == {
            "title": "Hunky Dory",
            "tags": ["glam", "art pop"],
        }

    def test_get_list_single(self):
        wrapped = self.wrap(validate=TaggedAlbumSchema())
        request = self.get([("tags", "glam")])
        wrapped(self.context, request)
        assert request.data == {"tags": ["glam"]}

    def test_get_non_list_repeated(self):
        """
        A repeated parameter for a non-list field takes the last value.

        """
        wrapped = self.wrap(validate=AlbumSchema())
        request = self.get(
            [
                ("title", "Space Oddity"),
                ("title", "Hunky Dory"),
            ]
        )
        wrapped(self.context, request)
        assert request.data == {"title": "Hunky Dory"}

    def test_schema_class(self):
        wrapped = self.wrap(validate=AlbumSchema)
        request = self.post({"release_date": "1971-12-17"})
        wrapped(self.context, request)
        assert request.data == {"release_date": Date(1971, 12, 17)}

    def test_dict_schema(self):
        wrapped = self.wrap(validate={"release_date": fields.Date()})
        request = self.post({"release_date": "1971-12-17"})
        wrapped(self.context, request)
        assert request.data == {"release_date": Date(1971, 12, 17)}

    def test_error(self):
        """
        Technically not necessary, since we just let marshmallow use its own
        error handling.  However, our documentation makes claims on how this
        works, so we test it.

        """
        wrapped = self.wrap(validate=AlbumSchema())
        request = self.post(
            {
                "title": "Hunky Dory",
                "release_date": "1971-14-17",
            }
        )
        with pytest.raises(ValidationError) as exc:
            wrapped(self.context, request)
        assert exc.value.messages == {"release_date": ["Not a valid date."]}
        assert exc.value.normalized_messages() == {
            "release_date": ["Not a valid date."]
        }
        self.view.assert_not_called()
