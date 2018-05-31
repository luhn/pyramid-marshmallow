import yaml
from apispec import APISpec, utils


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


def split_docstring(docstring):
    """
    Split a docstring in half, delineated with a "---".  The first half is
    returned verbatim, the second half is parsed as YAML.

    """
    split_lines = utils.trim_docstring(docstring).split('\n')

    # Cut YAML from rest of docstring
    for index, line in enumerate(split_lines):
        line = line.strip()
        if line.startswith('---'):
            cut_from = index
            break
    else:
        return (docstring or '').strip(), dict()

    docs = '\n'.join(split_lines[:cut_from]).strip()
    yaml_string = '\n'.join(split_lines[cut_from:])
    yaml_string = utils.dedent(yaml_string)
    parsed = yaml.load(yaml_string)
    return docs, parsed


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
            docstring, op = split_docstring(view['callable'].__doc__)
            op.setdefault('responses', dict())
            op.setdefault('description', docstring)
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
            # We are required to have some response, so make one up.
            if not op['responses']:
                op['responses']['200'] = {
                    'description': '',
                }
            final_ops[method] = op
        spec.add_path(path, operations=final_ops)
    return spec
