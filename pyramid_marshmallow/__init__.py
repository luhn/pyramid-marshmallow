from marshmallow import Schema, ValidationError
from pyramid.response import Response
from pyramid.viewderivers import VIEW

__all__ = [
    "ValidationError",
]


def includeme(config):
    config.add_view_deriver(view_validator)
    config.add_view_deriver(view_marshaller, under="rendered_view", over=VIEW)
    config.add_view_deriver(view_api_spec)


def make_schema(schema=None, **kwargs):
    """
    Create a schema from a dictionary.

    **Deprecated**:  Use `Schema.from_dict` instead.

    """
    return Schema.from_dict(schema or kwargs)


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
        return Schema.from_dict(schema)()
    else:
        raise TypeError("Schema is of invalid type.")


def view_validator(view, info):
    schema = process_schema(info.options.get("validate"))
    if schema is None:
        return view

    def wrapped(context, request):
        if request.method == "GET":
            data = dict()
            for k, v in request.GET.items():
                data[k] = v
        else:
            data = request.json_body
        request.data = schema.load(data)
        return view(context, request)

    return wrapped


view_validator.options = ("validate",)


def view_marshaller(view, info):
    schema = process_schema(info.options.get("marshal"))
    if schema is None:
        return view

    def wrapped(context, request):
        output = view(context, request)
        if isinstance(output, Response):
            return output
        else:
            return schema.dump(output)

    return wrapped


view_marshaller.options = ("marshal",)


def view_api_spec(view, info):
    return view


view_api_spec.options = ("api_spec", "api_zone")
