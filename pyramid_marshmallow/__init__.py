from marshmallow import Schema, ValidationError
from pyramid.viewderivers import VIEW

from .utils import make_schema


__all__ = [
    'make_schema',
]


def includeme(config):
    config.add_view_deriver(view_validator)
    config.add_view_deriver(view_marshaller, under='rendered_view', over=VIEW)


def process_schema(schema):
    """
    Handle a schema passed in as a view deriver, creating a nonce schema if a
    dictionary.

    """
    if schema is None:
        return None
    elif isinstance(schema, Schema):
        return schema
    elif isinstance(schema, dict):
        _Schema = make_schema(schema)
        return _Schema()
    else:
        raise TypeError('Schema is of invalid type.')


def view_validator(view, info):
    schema = process_schema(info.options.get('validate'))
    if schema is None:
        return view

    def wrapped(context, request):
        if request.method == 'GET':
            data = dict()
            for k, v in request.GET.items():
                data[k] = v
        else:
            data = request.json_body
        request.data = schema.load(data)
        return view(context, request)

    return wrapped


view_validator.options = ('validate',)


def view_marshaller(view, info):
    schema = process_schema(info.options.get('marshal'))
    if schema is None:
        return view

    def wrapped(context, request):
        output = view(context, request)
        return schema.dump(output)

    return wrapped


view_marshaller.options = ('marshal',)
