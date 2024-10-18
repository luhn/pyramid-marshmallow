import argparse
from importlib import import_module
from wsgiref.simple_server import make_server

from pyramid.config import Configurator
from pyramid.paster import get_app

from . import ISpecGenerator, SpecGenerator

parser = argparse.ArgumentParser()
parser.add_argument(
    "app",
    nargs="?",
    help="The app module.  In the format `module:variable`.",
)
parser.add_argument(
    "--ini",
    help="If specified, load the app via Paste from an ini file.",
)
parser.add_argument(
    "--host",
    help="The host to bind to.  Defaults to 0.0.0.0.",
    default="0.0.0.0",
)
parser.add_argument(
    "--port",
    type=int,
    help="The port to bind to.  Defaults to 8080.",
    default=8080,
)
parser.add_argument(
    "--zone",
    help=(
        "The API zone to generate spec for.  See documentation for more "
        "details.",
    ),
)
parser.add_argument(
    "--merge",
    help="A YAML file to merge with the generated spec.",
    nargs="*",
)


def serve():
    args = parser.parse_args()
    if args.app and args.ini:
        raise ValueError("Cannot specify both [app] and --ini.")
    elif args.app:
        app = import_app(args.app)
    elif args.ini:
        app = get_app(args.ini)
    else:
        raise ValueError("Must specify one of [app] or --ini.")
    wsgi_app = create_wsgi_app(args, app.registry)
    server = make_server(args.host, args.port, wsgi_app)
    print(f"Starting server on { args.host }:{ args.port }")  # noqa: T201
    server.serve_forever()


def create_wsgi_app(args, registry):
    config = Configurator()
    config.include("pyramid_marshmallow.openapi")
    config.registry.registerUtility(SpecGenerator(registry), ISpecGenerator)
    config.add_route("index", "/")
    config.add_openapi_html_view(
        zone=args.zone,
        merge=args.merge,
        route_name="index",
    )
    config.add_route("json", "/spec.json")
    config.add_openapi_json_view(
        zone=args.zone,
        merge=args.merge,
        route_name="json",
    )
    config.add_route("yaml", "/spec.yaml")
    config.add_openapi_yaml_view(
        zone=args.zone,
        merge=args.merge,
        route_name="yaml",
    )
    return config.make_wsgi_app()


def import_app(name):
    module_name, _, var_name = name.partition(":")
    module = import_module(module_name)
    return getattr(module, var_name)


if __name__ == "__main__":
    serve()
