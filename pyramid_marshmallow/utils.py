from marshmallow import Schema


def make_schema(schema=None, **kwargs):
    """
    Create a schema from a dictionary.

    """
    if schema is None:
        schema = kwargs
    return type('_Schema', (Schema,), schema.copy())


to_define = []


def define(schema):
    """
    Mark a schema to be defined in the spec.

    """
    to_define.append(schema)
    return schema


def pending_definitions():
    return to_define
