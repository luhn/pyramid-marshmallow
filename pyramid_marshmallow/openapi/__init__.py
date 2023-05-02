import functools
import json

from pyramid.response import Response
from zope.interface import Interface, implementer

from .spec import create_spec, generate_html, generate_yaml


def includeme(config):
    config.registry.registerUtility(
        SpecGenerator(config.registry),
        ISpecGenerator,
    )
    config.add_directive("add_openapi_json_view", add_openapi_json_view)
    config.add_directive("add_openapi_html_view", add_openapi_html_view)
    config.add_directive("add_openapi_yaml_view", add_openapi_yaml_view)


class ISpecGenerator(Interface):
    """
    Interface for a simple callable that returns the spec.

    """

    def __call__(zone, merge):
        ...


@implementer(ISpecGenerator)
class SpecGenerator:
    """
    Generate and cache specs for the given registry.

    """

    def __init__(self, registry):
        self.registry = registry

    def __call__(self, zone, merge):
        return self._call(zone, tuple(merge) if merge else tuple())

    @functools.lru_cache
    def _call(self, zone, merge):
        return create_spec(self.registry, zone=zone, merge=merge)


def _inject_params(view, zone=None, merge=None):
    """
    Add `zone` and `merge` arguments to given view callable.

    Originally I was using `functools.partial` directly, but Pyramid would
    complain unless I added `functools.update_wrapper`.

    """
    wrapper = functools.partial(view, zone=zone, merge=merge)
    functools.update_wrapper(wrapper, view)
    return wrapper


def add_openapi_json_view(config, zone=None, merge=None, *args, **kwargs):
    """
    Add a view that returns the JSON spec with the given zone and mergefiles.
    Additional args are passed to `Configuration.add_view`.

    """
    config.add_view(
        _inject_params(json_view, zone=zone, merge=merge),
        *args,
        **kwargs,
    )


def json_view(request, zone=None, merge=None):
    generator = request.registry.getUtility(ISpecGenerator)
    indent = 2 if "pretty" in request.GET else None
    body = json.dumps(generator(zone, merge), indent=indent)
    return Response(
        body=body,
        content_type="application/json",
        charset="utf-8",
    )


def add_openapi_html_view(config, zone=None, merge=None, *args, **kwargs):
    """
    Add a view that returns a redoc page for a spec with the given zone and
    mergefiles.  Additional args are passed to `Configuration.add_view`.

    """
    config.add_view(
        _inject_params(html_view, zone=zone, merge=merge),
        *args,
        **kwargs,
    )


def html_view(request, zone=None, merge=None):
    generator = request.registry.getUtility(ISpecGenerator)
    body = generate_html(generator(zone, merge))
    return Response(
        body=body,
        content_type="text/html",
    )


def add_openapi_yaml_view(config, zone=None, merge=None, *args, **kwargs):
    """
    Add a view that returns a YAML spec with the given zone and mergefiles.
    Additional args are passed to `Configuration.add_view`.

    """
    config.add_view(
        _inject_params(yaml_view, zone=zone, merge=merge),
        *args,
        **kwargs,
    )


def yaml_view(request, zone=None, merge=None):
    generator = request.registry.getUtility(ISpecGenerator)
    body = generate_yaml(generator(zone, merge))
    return Response(
        body=body,
        content_type="text/yaml",
    )
