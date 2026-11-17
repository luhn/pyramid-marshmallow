import json

import pkg_resources
from pyramid.path import DottedNameResolver

from pyramid_marshmallow import ensure_schema

try:
    import yaml
    from apispec import APISpec, utils, yaml_utils
    from apispec.ext.marshmallow.common import (
        resolve_schema_cls,
        resolve_schema_instance,
    )
except ImportError:
    raise ImportError(
        "You must have the `apispec` package installed to use this feature.  "
        "You can install it with `pip install pyramid_marshmallow[openapi]."
    )


def schema_name_resolver(schema):
    """
    Determine a name for the schema.  Takes the class name by default,
    stripping the ``Schema`` suffix if necessary.  Returns false for schemas
    that should not be named in the spec, such as unregistered schemas created
    by ``Schema.from_dict``.
    """
    cls = resolve_schema_cls(schema)
    instance = resolve_schema_instance(schema)
    name = cls.__name__
    if not cls.opts.register:
        # Unregistered schemas are put inline.
        return False
    if instance.only or instance.exclude:
        # If schema includes only select fields, treat it as nonce
        return False
    if name.endswith("Schema"):
        name = name[:-6] or name
    if instance.partial:
        name = "Partial" + name
    return name


def list_paths(introspector):
    """
    Iterate over the views registered with a Pyramid introspector
    (``registry.introspector``) and yield a ``(path, method, introspectable)``
    tuple for each HTTP method each view accepts.

    ``path`` is the URL path for the view:  the route pattern for URL dispatch
    views, or ``context.__path__ + "/" + view_name`` for traversal views.
    Views for which no path can be determined are skipped.

    ``method`` is the lowercase HTTP method.  Views without a
    ``request_method`` predicate are treated as ``GET`` only.

    ``introspectable`` is the view's introspectable.

    """
    for item in introspector.get_category("views", default=[]):
        introspectable = item["introspectable"]
        path = _make_path(introspector, introspectable)
        if path is None:
            continue
        methods = introspectable["request_methods"] or ["GET"]
        if isinstance(methods, str):
            methods = [methods]
        for method in methods:
            yield path, method.lower(), introspectable


def _make_path(introspector, introspectable):
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


def split_docstring(docstring):
    """
    Split a view's docstring into a summary, description, and OpenAPI
    operation overrides.

    The docstring is dedented, then divided at the first line beginning with
    "---".  Above the delimiter, the first line is the summary and the
    remaining lines are the description.  Everything from the delimiter on is
    parsed as YAML.  For example::

        Get a widget.

        Fetches a single widget by its ID.

        ---
        tags:
            - widgets

    produces ``("Get a widget.", "Fetches a single widget by its ID.",
    {"tags": ["widgets"]})``.

    :param docstring:  The docstring to split.  May be ``None``.
    :returns:  A ``(summary, description, operation)`` tuple.  ``summary``
        and ``description`` are ``None`` if absent or blank.  ``operation``
        is the parsed YAML, or an empty dict if there is no YAML.

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

    if cut_from > 0:
        summary = split_lines[0].strip() or None
    else:
        summary = None
    docs = "\n".join(split_lines[1:cut_from]).strip() or None
    yaml_string = "\n".join(split_lines[cut_from:])
    parsed = yaml.safe_load(yaml_string) if yaml_string else None
    return summary, docs, parsed or dict()


def set_request_body(spec, op, view):
    op["requestBody"] = {
        "content": {
            "application/json": {
                "schema": ensure_schema(view["validate"]),
            },
        },
    }


def set_query_params(spec, op, view):
    op["parameters"].append(
        {
            "in": "query",
            "schema": ensure_schema(view["validate"]),
        }
    )


def set_response_body(spec, op, view):
    op["responses"]["200"] = {
        "description": "",
        "content": {
            "application/json": {
                "schema": ensure_schema(view["marshal"]),
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


def create_spec(registry, zone=None, merge=None):
    settings = registry.settings
    REQUIRED_SETTINGS = [
        "openapi.title",
        "openapi.version",
        "openapi.openapi_version",
    ]
    for key in REQUIRED_SETTINGS:
        if key not in settings:
            raise ValueError(f"`{key}` setting is required.")

    name_resolver = DottedNameResolver()
    MarshmallowPlugin = name_resolver.maybe_resolve(
        settings.get(
            "openapi.plugin", "apispec.ext.marshmallow.MarshmallowPlugin"
        )
    )
    marshmallow_plugin = MarshmallowPlugin(
        schema_name_resolver=schema_name_resolver
    )
    spec = APISpec(
        title=settings["openapi.title"],
        version=settings["openapi.version"],
        openapi_version=settings["openapi.openapi_version"],
        plugins=[marshmallow_plugin],
    )
    plugin_hook = settings.get("openapi.plugin_hook")
    if plugin_hook:
        plugin_hook = name_resolver.maybe_resolve(plugin_hook)
        plugin_hook(registry, spec, marshmallow_plugin)
    for path, method, view in list_paths(registry.introspector):
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
        spec.path(path, operations={method: final_op})

    json = spec.to_dict()
    return _perform_merges(json, merge, settings.get("openapi.merge"))


def _perform_merges(json, mergefile, merge_setting):
    # Perform merges
    if mergefile is None:
        merges = []
    elif isinstance(mergefile, str):
        merges = [mergefile]
    else:
        merges = mergefile
    if not merge_setting:
        pass
    elif isinstance(merge_setting, str):
        merges.extend(x.strip() for x in merge_setting.split(","))
    else:
        merges.extend(merge_setting)
    for mergefile in merges:
        json = merge(json, mergefile)
    return json


def merge(spec, mergefile):
    if ":" in mergefile:
        module, _, path = mergefile.partition(":")
        fh = pkg_resources.resource_stream(module, path)
    else:
        fh = open(mergefile)
    with fh:
        to_merge = yaml.safe_load(fh)
    return utils.deepupdate(spec, to_merge)


def generate_html(spec):
    data = json.dumps(spec, sort_keys=True)
    return HTML_TEMPLATE.format(
        title=spec["info"]["title"],
        version=spec["info"]["version"],
        spec=data,
    )


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
    <head>
        <title>{title} {version}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400\
,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <div id="redoc"></div>
        <script type="text/json" id="spec">{spec}</script>
        <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalon\
e.js"></script>
        <script>
            window.addEventListener('load', function() {{
                var el = document.getElementById('redoc');
                var spec = JSON.parse(document.getElementById('spec').text);
                Redoc.init(spec, {{}}, el);
            }});
        </script>
    </body>
</html>
"""


def generate_yaml(spec):
    return yaml_utils.dict_to_yaml(spec)
