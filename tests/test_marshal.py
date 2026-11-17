from datetime import date as Date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from marshmallow import Schema, fields
from pyramid.httpexceptions import HTTPNoContent
from pyramid.response import Response
from pyramid.testing import DummyRequest

from pyramid_marshmallow import view_marshaller


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


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
