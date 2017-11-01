from datetime import date as Date
from marshmallow import Schema, fields
from pyramid_apispec import _make_schema


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


def test_make_schema_null():
    assert _make_schema(None) is None


def test_make_schema_schema():
    schema = AlbumSchema()
    assert _make_schema(schema) is schema


def test_make_schema_dict():
    schema = _make_schema({
        'title': fields.Str(),
        'release_date': fields.Date(),
    })
    assert isinstance(schema, Schema)
    assert schema.load({
        'title': 'Hunky Dory',
        'release_date': '1971-12-17',
    }).data == {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }
