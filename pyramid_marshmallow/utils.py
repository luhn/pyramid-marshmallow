from marshmallow import Schema


def make_schema(schema=None, **kwargs):
    """
    Create a schema from a dictionary.

    """
    if schema is None:
        schema = kwargs
    return type('_Schema', (Schema,), schema.copy())
