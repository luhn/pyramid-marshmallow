import argparse
import json
from importlib import import_module

from apispec import yaml_utils
from pyramid.paster import get_app

from .spec import create_spec, generate_html, merge

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
    "--zone",
    help=(
        "The API zone to generate spec for.  See documentation for more "
        "details.",
    ),
)
parser.add_argument(
    "--merge",
    help="A YAML file to merge with the generated spec.",
)
parser.add_argument(
    "--format",
    help='The output, one of "json", "yaml", or "html".',
    default="json",
)
parser.add_argument(
    "--output",
    help="The file to output to.",
    default="-",
)


def generate():
    args = parser.parse_args()
    if args.app and args.ini:
        raise ValueError("Cannot specify both [app] and --ini.")
    elif args.app:
        app = import_app(args.app)
    elif args.ini:
        app = get_app(args.ini)
    else:
        raise ValueError("Must specify one of [app] or --ini.")
    spec = create_spec(app.registry, zone=args.zone)
    spec_json = spec.to_dict()
    if args.merge:
        spec_json = merge(spec_json, args.merge)
    if args.format == "json":
        output = json.dumps(spec_json)
    elif args.format == "yaml":
        output = yaml_utils.dict_to_yaml(spec_json)
    elif args.format == "html":
        output = generate_html(spec_json)
    else:
        raise ValueError('Format must be one of "json", "yaml", or "html".')
    if args.output == "-":
        print(output)
    else:
        with open(args.output, "wb") as fh:
            if isinstance(output, str):
                output = output.encode("utf8")
            fh.write(output)


def import_app(name):
    module_name, _, var_name = name.partition(":")
    module = import_module(module_name)
    return getattr(module, var_name)


if __name__ == "__main__":
    generate()
