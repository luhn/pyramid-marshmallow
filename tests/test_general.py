from datetime import date as Date

import pytest
from marshmallow import Schema, fields

from pyramid_marshmallow import ensure_schema, make_schema, process_schema


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


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
