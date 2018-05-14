from apispec import APISpec


def list_paths(introspector):
    paths = dict()
    for item in introspector.get_category('views'):
        spect = item['introspectable']
        path = make_path(introspector, spect)
        if path is None:
            continue
        operations = paths.setdefault(path, dict())
        for method in (spect['request_methods'] or ['GET']):
            method = method.lower()
            operations[method] = spect
    return paths


def make_path(introspector, introspectable):
    if introspectable['route_name']:
        route = introspector.get('routes', introspectable['route_name'])
        return route['pattern']
    else:
        # key = ('traversal', spect['context'], spect['name'])
        return None


def add_definition(spec, schema):
    if isinstance(schema, dict):
        from pyramid_apispec import _make_schema
        return _make_schema(schema)
    else:
        name = type(schema).__name__
        spec.definition(name, schema=schema)
        return schema


def create_spec(introspector):
    spec = APISpec(
        title='Test',
        version='0.1.0',
        openapi_version='3.0.1',
        plugins=['apispec.ext.marshmallow'],
    )
    for path, operations in list_paths(introspector).items():
        final_ops = dict()
        for method, view in operations.items():
            op = final_ops.setdefault(method, {
                'responses': {},
            })
            docstring = (view['callable'].__doc__ or '').strip()
            if docstring:
                op['description'] = docstring
            if 'validate' in view and method != 'get':
                schema = add_definition(spec, view['validate'])
                op['requestBody'] = {
                    'content': {
                        'application/json': {
                            'schema': schema,
                        },
                    },
                }
            if 'marshal' in view:
                schema = add_definition(spec, view['marshal'])
                op['responses']['200'] = {
                    'description': '',
                    'content': {
                        'application/json': {
                            'schema': schema,
                        },
                    },
                }
            else:
                op['responses']['200'] = {
                    'description': '',
                }
        spec.add_path(path, operations=final_ops)
    return spec
