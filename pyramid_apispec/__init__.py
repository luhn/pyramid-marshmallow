from .exceptions import SchemaError, ValidationError, MarshalError
from pyramid.viewderivers import VIEW


__all__ = [
    'SchemaError',
    'ValidationError',
    'MarshalError',
]


def includeme(config):
    config.add_view_deriver(view_validator)
    config.add_view_deriver(view_marshaller, under='rendered_view', over=VIEW)


def view_validator(view, info):
    schema = info.options.get('validate')
    if schema is None:
        return view

    def wrapped(context, request):
        if request.method == 'GET':
            data = dict(request.GET)
        else:
            data = request.json_body
        result = schema.load(data)
        if result.errors:
            raise ValidationError(result.errors)
        request.data = result.data
        return view(context, request)

    return wrapped


view_validator.options = ('validate',)


def view_marshaller(view, info):
    schema = info.options.get('marshal')
    if schema is None:
        return view

    def wrapped(context, request):
        output = view(context, request)
        result = schema.dump(output)
        if result.errors:
            raise MarshalError(result.errors)
        return result.data

    return wrapped


view_marshaller.options = ('marshal',)
