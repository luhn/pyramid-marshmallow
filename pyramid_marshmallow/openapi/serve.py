import os
import signal
from threading import Thread

import hupper
import waitress
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


def main():
    args = parser.parse_args()
    if args.watch:
        reloader = hupper.start_reloader(
            "pyramid_marshmallow.openapi.serve.main",
            shutdown_interval=10,
        )
        if args.merge:
            reloader.watch_files(args.merge)
    return serve(args)


def serve(args):
    app = import_app(args)
    wsgi_app = create_wsgi_app(args, app.registry)
    server = waitress.create_server(wsgi_app, host=args.host, port=args.port)
    print(f"Starting server on {args.host}:{args.port}")  # noqa: T201
    stopper = ServerStopper(server)
    stopper.register()
    server.run()
    return 1


class ServerStopper:
    def __init__(self, server):
        """
        A class that handles stopping the server on SIGINT or SIGTERM.
        """
        self.server = server

    def stop(self):
        """
        Stop the server.
        """
        t = Thread(target=self.server.close)
        t.start()

    def signal(self, signalnum, frame):
        """
        Handle a signal.
        """
        print("Stopping server...")  # noqa: T201
        self.stop()

    def register(self):
        """
        Register a SIGTERM and SIGINT handler.
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
    os.exit(serve())
