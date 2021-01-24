import argparse
import json

import yaml
from apispec import utils, yaml_utils
from pyramid.paster import get_app

from .spec import create_spec

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


def merge(spec, mergefile):
    with open(mergefile) as fh:
        to_merge = yaml.safe_load(fh)
    return utils.deepupdate(spec, to_merge)


def generate_html(spec):
    data = json.dumps(spec)
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
        <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.sta\
ndalone.js"></script>
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


if __name__ == "__main__":
    generate()
