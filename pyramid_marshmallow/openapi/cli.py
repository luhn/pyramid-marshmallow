import argparse
from importlib import import_module

from pyramid import paster


def import_attr(spec):
    """
    Import an attribute from a module via a string specification, such as
    ``urllib.parse:urlparse``.  If the string ends with ``()``, the attribute
    is understood to be a function:  It will be executed with no arguments and
    the result returned.

    This function is used to load Pyramid application.
    """
    if spec.endswith("()"):
        is_function = True
        spec = spec[:-2]
    else:
        is_function = False
    module_name, _, attr_name = spec.partition(":")
    module = import_module(module_name)
    attr = getattr(module, attr_name)
    return attr() if is_function else attr


def import_app(args):
    """
    Given the arguments from :func:`base_parser`, return the specified Pyramid
    application.
    """
    if args.app and args.ini:
        raise ValueError("Cannot specify both [app] and --ini.")
    elif args.app:
        return import_attr(args.app)
    elif args.ini:
        return paster.get_app(args.ini)
    else:
        raise ValueError("Must specify one of [app] or --ini.")


def base_parser():
    """
    Return an :class:`argpase.ArgumentParser` populated with arguments shared
    between ``serve-spec`` and ``generate-spec``.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "app",
        nargs="?",
        help=(
            "The application to load, in the format `module:attribute`.  If "
            "ending in `()`, the attribute will be invoked with no arguments "
            "and the result used as the application."
        ),
    )
    parser.add_argument(
        "--ini",
        help="If specified, load the app via Paste from an ini file.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help=(
            "If set, files will be watched for changes and the spec "
            "regenerated."
        ),
    )
    parser.add_argument(
        "--zone",
        help=(
            "The API zone to generate spec for.  See documentation for more "
            "details."
        ),
    )
    parser.add_argument(
        "--merge",
        help="A YAML file to merge with the generated spec.",
        nargs="*",
    )
    return parser
