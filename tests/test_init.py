from datetime import date as Date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from marshmallow import Schema, ValidationError, fields
from pyramid.httpexceptions import HTTPNoContent
from pyramid.response import Response
from pyramid.testing import DummyRequest
from webob.multidict import MultiDict

from pyramid_marshmallow import (
    ensure_schema,
    make_schema,
    process_schema,
    view_marshaller,
    view_validator,
)


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


class TaggedAlbumSchema(AlbumSchema):
    tags = fields.List(fields.Str())


class TestEnsureSchema:
    def call(self, schema):
        return ensure_schema(schema)

    def test_null(self):
        assert self.call(None) is None

    def test_schema(self):
        schema = AlbumSchema()
        assert self.call(schema) is schema

    def test_schema_class(self):
        schema = self.call(AlbumSchema)
        assert isinstance(schema, AlbumSchema)

    def test_dict(self):
        schema = self.call(
            {
                "title": fields.Str(),
                "release_date": fields.Date(),
            }
        )
        assert isinstance(schema, Schema)
        assert schema.load(
            {
                "title": "Hunky Dory",
                "release_date": "1971-12-17",
            }
        ) == {
            "title": "Hunky Dory",
            "release_date": Date(1971, 12, 17),
        }

    def test_invalid(self):
        with pytest.raises(TypeError):
            self.call("not a schema")

    def test_invalid_class(self):
        with pytest.raises(TypeError):
            self.call(dict)

    def test_alias(self):
        assert process_schema is ensure_schema


class TestMakeSchema:
    def call(self, *args, **kwargs):
        return make_schema(*args, **kwargs)

    def test_dict(self):
        _Schema = self.call(
            {
                "title": fields.Str(),
                "release_date": fields.Date(),
            }
        )
        assert issubclass(_Schema, Schema)
        assert _Schema().load(
            {
                "title": "Hunky Dory",
                "release_date": "1971-12-17",
            }
        ) == {
            "title": "Hunky Dory",
            "release_date": Date(1971, 12, 17),
        }

    def test_kwargs(self):
        _Schema = self.call(
            title=fields.Str(),
            release_date=fields.Date(),
        )
        assert issubclass(_Schema, Schema)
        assert _Schema().load(
            {
                "title": "Hunky Dory",
                "release_date": "1971-12-17",
            }
        ) == {
            "title": "Hunky Dory",
            "release_date": Date(1971, 12, 17),
        }


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


class TestViewMarshaller:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.view = Mock()
        self.context = object()
        self.request = DummyRequest()

    def wrap(self, **options):
        info = SimpleNamespace(options=options)
        return view_marshaller(self.view, info)

    def call(self, wrapped, output):
        self.view.return_value = output
        result = wrapped(self.context, self.request)
        self.view.assert_called_once_with(self.context, self.request)
        return result

    def test_no_marshal(self):
        assert self.wrap() is self.view

    def test_marshal_none(self):
        assert self.wrap(marshal=None) is self.view

    def test_dict(self):
        wrapped = self.wrap(marshal=AlbumSchema())
        result = self.call(
            wrapped,
            {
                "title": "Hunky Dory",
                "release_date": Date(1971, 12, 17),
            },
        )
        assert result == {
            "title": "Hunky Dory",
            "release_date": "1971-12-17",
        }

    def test_object(self):
        wrapped = self.wrap(marshal=AlbumSchema())
        result = self.call(
            wrapped,
            SimpleNamespace(
                title="Hunky Dory",
                release_date=Date(1971, 12, 17),
            ),
        )
        assert result == {
            "title": "Hunky Dory",
            "release_date": "1971-12-17",
        }

    def test_excludes_undeclared(self):
        wrapped = self.wrap(marshal=AlbumSchema())
        result = self.call(
            wrapped,
            {
                "title": "Hunky Dory",
                "label": "RCA",
            },
        )
        assert result == {"title": "Hunky Dory"}

    def test_many(self):
        wrapped = self.wrap(marshal=AlbumSchema(many=True))
        result = self.call(
            wrapped,
            [
                {"title": "Hunky Dory", "release_date": Date(1971, 12, 17)},
                {"title": "Low", "release_date": Date(1977, 1, 14)},
            ],
        )
        assert result == [
            {"title": "Hunky Dory", "release_date": "1971-12-17"},
            {"title": "Low", "release_date": "1977-01-14"},
        ]

    def test_schema_class(self):
        wrapped = self.wrap(marshal=AlbumSchema)
        result = self.call(wrapped, {"release_date": Date(1971, 12, 17)})
        assert result == {"release_date": "1971-12-17"}

    def test_dict_schema(self):
        wrapped = self.wrap(marshal={"release_date": fields.Date()})
        result = self.call(wrapped, {"release_date": Date(1971, 12, 17)})
        assert result == {"release_date": "1971-12-17"}

    def test_response(self):
        wrapped = self.wrap(marshal=AlbumSchema())
        response = Response()
        assert self.call(wrapped, response) is response

    def test_http_exception(self):
        wrapped = self.wrap(marshal=AlbumSchema())
        response = HTTPNoContent()
        assert self.call(wrapped, response) is response
