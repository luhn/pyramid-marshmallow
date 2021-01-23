from .utils import make_schema, NonceSchema

try:
    from apispec import APISpec, utils
    from apispec.ext.marshmallow import MarshmallowPlugin
    from apispec.ext.marshmallow.common import (
        resolve_schema_cls,
        resolve_schema_instance,
    )
    import yaml
except ImportError:
    raise ImportError(
        "You must have the `apispec` package installed to use this feature.  "
        "You can install it with `pip install pyramid_marshmallow[openapi]."
    )


def schema_name_resolver(schema):
    cls = resolve_schema_cls(schema)
    instance = resolve_schema_instance(schema)
    name = cls.__name__
    if issubclass(cls, NonceSchema):
        # Nonce schemas are defined inline
        return False
    if instance.only:
        # If schema includes only select fields, treat it as nonce
        return False
    if name.endswith("Schema"):
        return name[:-6] or name
    if instance.partial:
        name = "Partial" + name
    return name


def list_paths(introspector):
    for item in introspector.get_category("views"):
        spect = item["introspectable"]
        path = make_path(introspector, spect)
        if path is None:
            continue
        operations = dict()
        methods = spect["request_methods"] or ["GET"]
        if isinstance(methods, str):
            methods = [methods]
        for method in methods:
            method = method.lower()
            operations[method] = spect
        yield path, operations


def make_path(introspector, introspectable):
    if introspectable["route_name"]:
        route = introspector.get("routes", introspectable["route_name"])
        return route["pattern"]
    elif introspectable["context"]:
        context = introspectable["context"]
        base = getattr(context, "__path__", None)
        if base is None:
            return None
        else:
            return base + "/" + (introspectable["name"] or "")
    else:
        return None


def _schema(schema):
    if isinstance(schema, dict):
        return make_schema(schema)
    else:
        return schema


def split_docstring(docstring):
    """
    Split a docstring in half, delineated with a "---".  The first half is
    returned verbatim, the second half is parsed as YAML.

    """
    split_lines = utils.trim_docstring(docstring).split("\n")

    # Cut YAML from rest of docstring
    for index, line in enumerate(split_lines):
        line = line.strip()
        if line.startswith("---"):
            cut_from = index
            break
    else:
        cut_from = len(split_lines)

    summary = split_lines[0].strip() or None
    docs = "\n".join(split_lines[1:cut_from]).strip() or None
    yaml_string = "\n".join(split_lines[cut_from:])
    if yaml_string:
        parsed = yaml.load(yaml_string)
    else:
        parsed = dict()
    return summary, docs, parsed


def set_request_body(spec, op, view):
    op["requestBody"] = {
        "content": {
            "application/json": {
                "schema": _schema(view["validate"]),
            },
        },
    }


def set_query_params(spec, op, view):
    op["parameters"].append(
        {
            "in": "query",
            "schema": _schema(view["validate"]),
        }
    )


def set_response_body(spec, op, view):
    op["responses"]["200"] = {
        "description": "",
        "content": {
            "application/json": {
                "schema": _schema(view["marshal"]),
            },
        },
    }


def set_url_params(spec, op, view):
    context = view["context"]
    if not context:
        return
    params = getattr(context, "__params__", [])
    for param in params:
        param["in"] = "path"
        param["required"] = True
    op["parameters"].extend(params)


def set_tag(spec, op, view):
    context = view["context"]
    if not context:
        return
    tag = getattr(context, "__tag__", None)
    if not tag:
        return
    if isinstance(tag, dict):
        # Cheating and using the private variable spec._tags
        if not any(x["name"] == tag["name"] for x in spec._tags):
            spec.tag(tag)
        tag_name = tag["name"]
    else:
        tag_name = tag
    op.setdefault("tags", []).append(tag_name)


def create_spec(title, version, introspector, zone=None):
    marshmallow_plugin = MarshmallowPlugin(
        schema_name_resolver=schema_name_resolver,
    )
    spec = APISpec(
        title=title,
        version=version,
        openapi_version="3.0.2",
        plugins=[marshmallow_plugin],
    )
    for path, operations in list_paths(introspector):
        final_ops = dict()
        for method, view in operations.items():
            if zone is not None and zone != view.get("api_zone"):
                continue
            summary, descr, user_op = split_docstring(view["callable"].__doc__)
            op = {
                "responses": dict(),
                "parameters": [],
            }
            if summary:
                op["summary"] = summary
            if descr:
                op["description"] = descr
            set_url_params(spec, op, view)
            if "validate" in view:
                if method == "get":
                    set_query_params(spec, op, view)
                else:
                    set_request_body(spec, op, view)
            if "marshal" in view:
                set_response_body(spec, op, view)
            set_tag(spec, op, view)
            final_op = utils.deepupdate(op, user_op)
            final_op = utils.deepupdate(final_op, view.get("api_spec", dict()))

            # We are required to have some response, so make one up.
            if not final_op["responses"]:
                final_op["responses"]["200"] = {
                    "description": "",
                }
            final_ops[method] = final_op
        spec.path(path, operations=final_ops)

    return spec
