from datetime import date as Date
from marshmallow import Schema, fields
from pyramid_apispec import make_schema, process_schema


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


def test_process_schema_null():
    assert process_schema(None) is None


def test_process_schema_schema():
    schema = AlbumSchema()
    assert process_schema(schema) is schema


def test_process_schema_dict():
    schema = process_schema({
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


def test_make_schema_dict():
    _Schema = make_schema({
        'title': fields.Str(),
        'release_date': fields.Date(),
    })
    assert issubclass(_Schema, Schema)
    assert _Schema(strict=True).load({
        'title': 'Hunky Dory',
        'release_date': '1971-12-17',
    }).data == {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }


def test_make_schema_kwargs():
    _Schema = make_schema(
        title=fields.Str(),
        release_date=fields.Date(),
    )
    assert issubclass(_Schema, Schema)
    assert _Schema(strict=True).load({
        'title': 'Hunky Dory',
        'release_date': '1971-12-17',
    }).data == {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }
