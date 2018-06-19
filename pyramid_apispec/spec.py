import yaml
from apispec import APISpec, utils
from . import make_schema


def list_paths(introspector):
    for item in introspector.get_category('views'):
        spect = item['introspectable']
        path = make_path(introspector, spect)
        if path is None:
            continue
        operations = dict()
        methods = spect['request_methods'] or ['GET']
        if isinstance(methods, str):
            methods = [methods]
        for method in methods:
            method = method.lower()
            operations[method] = spect
        yield path, operations


def make_path(introspector, introspectable):
    if introspectable['route_name']:
        route = introspector.get('routes', introspectable['route_name'])
        return route['pattern']
    elif introspectable['context']:
        context = introspectable['context']
        base = getattr(context, '__path__', None)
        if not base:
            return None
        else:
            return base + '/' + (introspectable['name'] or '')
    else:
        return None


def add_definition(spec, schema):
    if isinstance(schema, dict):
        return make_schema(schema)
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


def set_request_body(spec, op, view):
    schema = add_definition(spec, view['validate'])
    op['requestBody'] = {
        'content': {
            'application/json': {
                'schema': schema,
            },
        },
    }


def set_query_params(spec, op, view):
    schema = add_definition(spec, view['validate'])
    op['parameters'].append({
        'in': 'query',
        'schema': schema,
    })


def set_response_body(spec, op, view):
    schema = add_definition(spec, view['marshal'])
    op['responses']['200'] = {
        'description': '',
        'content': {
            'application/json': {
                'schema': schema,
            },
        },
    }


def set_url_params(spec, op, view):
    context = view['context']
    if not context:
        return
    params = getattr(context, '__params__', [])
    for param in params:
        param['in'] = 'path'
        param['required'] = True
    op['parameters'].extend(params)


def set_tag(spec, op, view):
    context = view['context']
    if not context:
        return
    tag = getattr(context, '__tag__', None)
    if not tag:
        return
    if isinstance(tag, dict):
        # Cheating and using the private variable spec._tags
        if not any(x['name'] == tag['name'] for x in spec._tags):
            spec.add_tag(tag)
        tag_name = tag['name']
    else:
        tag_name = tag
    op.setdefault('tags', []).append(tag_name)


def create_spec(title, version, introspector):
    spec = APISpec(
        title=title,
        version=version,
        openapi_version='3.0.1',
        plugins=['apispec.ext.marshmallow'],
    )
    for path, operations in list_paths(introspector):
        final_ops = dict()
        for method, view in operations.items():
            docstring, op = split_docstring(view['callable'].__doc__)
            op.setdefault('responses', dict())
            op.setdefault('description', docstring)
            op.setdefault('parameters', [])
            set_url_params(spec, op, view)
            if 'validate' in view and method != 'get':
                set_request_body(spec, op, view)
            elif 'validate' in view:
                set_query_params(spec, op, view)
            if 'marshal' in view:
                set_response_body(spec, op, view)
            set_tag(spec, op, view)
            # We are required to have some response, so make one up.
            if not op['responses']:
                op['responses']['200'] = {
                    'description': '',
                }
            final_ops[method] = op
        spec.add_path(path, operations=final_ops)
    return spec
