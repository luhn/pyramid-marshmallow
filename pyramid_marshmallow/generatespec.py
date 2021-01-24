import argparse
import json

from apispec import yaml_utils
from pyramid.paster import get_app

from .spec import create_spec, generate_html, merge

parser = argparse.ArgumentParser()
parser.add_argument(
    "ini",
    help="The .ini config file for the Pyramid project.",
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
    app = get_app(args.ini)
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


if __name__ == "__main__":
    generate()
