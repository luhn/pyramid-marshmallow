import argparse
import json
from pyramid.paster import get_app


parser = argparse.ArgumentParser()
parser.add_argument(
    'ini',
    help='The .ini config file for the Pyramid project.',
)
parser.add_argument(
    '--zone',
    help=(
        'The API zone to generate spec for.  See documentation for more '
        'details.',
    ),
    default='json',
)
parser.add_argument(
    '--format',
    help='The output, one of "json", "yaml", or "html".',
    default='json',
)
parser.add_argument(
    '--output',
    help='The file to output to.',
    default='-',
)


def generate():
    from .spec import create_spec
    args = parser.parse_args()
    app = get_app(args.ini)
    settings = app.registry.settings
    title = settings.get('openapi.title', 'Untitled')
    version = settings.get('openapi.version', '0.0.0')
    introspector = app.registry.introspector
    spec = create_spec(title, version, introspector, zone=args.zone)
    if args.format == 'json':
        output = json.dumps(spec.to_dict())
    elif args.format == 'yaml':
        output = spec.to_yaml()
    elif args.format == 'html':
        output = generate_html(spec)
    else:
        raise ValueError('Format must be one of "json", "yaml", or "html".')
    if args.output == '-':
        print(output)
    else:
        with open(args.output, 'wb') as fh:
            if isinstance(output, str):
                output = output.encode('utf8')
            fh.write(output)


def generate_html(spec):
    data = json.dumps(spec.to_dict())
    return HTML_TEMPLATE.format(
        title=spec.title,
        version=spec.version,
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


if __name__ == '__main__':
    generate()
