import json
import sys

from .cli import base_parser, import_app
from .spec import create_spec, generate_html, generate_yaml

parser = base_parser()
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
    app = import_app(args)
    spec_json = create_spec(app.registry, zone=args.zone, merge=args.merge)
    if args.format == "json":
        output = json.dumps(spec_json, sort_keys=True)
    elif args.format == "yaml":
        output = generate_yaml(spec_json)
    elif args.format == "html":
        output = generate_html(spec_json)
    else:
        raise ValueError('Format must be one of "json", "yaml", or "html".')
    if args.output == "-":
        sys.stdout.write(output)
        sys.stdout.write("\n")
    else:
        with open(args.output, "wb") as fh:
            if isinstance(output, str):
                output = output.encode("utf8")
            fh.write(output)


if __name__ == "__main__":
    generate()
