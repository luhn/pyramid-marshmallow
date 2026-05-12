import signal
from threading import Thread
from wsgiref.simple_server import make_server

from pyramid.config import Configurator

from . import ISpecGenerator, SpecGenerator
from .cli import base_parser, import_app

parser = base_parser()
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


def serve():
    args = parser.parse_args()
    app = import_app(args)
    wsgi_app = create_wsgi_app(args, app.registry)
    return start_server(args.host, args.port, wsgi_app)


def start_server(host, port, wsgi_app):
    server = make_server(host, port, wsgi_app)
    print(f"Starting server on {host}:{port}")  # noqa: T201
    stopper = ServerStopper(server)
    stopper.register()
    server.serve_forever()
    return 1


class ServerStopper:
    def __init__(self, server):
        """
        A class that handles signals and stops the server.
        """
        self.server = server

    def stop(self):
        """
        Stop the server.
        """
        t = Thread(target=self.server.shutdown)
        t.start()

    def signal(self, signalnum, frame):
        """
        Handle a signal.
        """
        print("Stopping server...")  # noqa: T201
        self.stop()

    def register(self):
        """
        Register a SIGTERM handler.
        """
        signal.signal(signal.SIGTERM, self.signal)
        signal.signal(signal.SIGINT, self.signal)


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


if __name__ == "__main__":
    serve()
