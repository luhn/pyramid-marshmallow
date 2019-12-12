from marshmallow import Schema


class NonceSchema(Schema):
    """
    Base class for nonce schemas (schemas created on-the-fly from
    dictionaries).

    """
    pass


def make_schema(schema=None, **kwargs):
    """
    Create a schema from a dictionary.

    """
    if schema is None:
        schema = kwargs
    schema = schema.copy()
    schema['__module__'] = NonceSchema.__module__
    cls = type('_NonceSchema', (NonceSchema,), schema)
    return cls
