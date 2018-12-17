from io import BytesIO
import zipfile
import shutil
import pkg_resources
import argparse
import json
from pyramid.paster import get_app


parser = argparse.ArgumentParser()
parser.add_argument(
    'ini',
    help='The .ini config file for the Pyramid project.',
)
parser.add_argument(
    '--format',
    help='The output, one of "json", "yaml", or "zip".',
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
    spec = create_spec(title, version, introspector)
    if args.format == 'json':
        output = json.dumps(spec.to_dict())
    elif args.format == 'yaml':
        output = spec.to_yaml()
    else:
        output = generate_zip(spec)
        if args.output == '-':
            raise NotImplementedError('Cannot output zip file to stdout.')
    if args.output == '-':
        print(output)
    else:
        with open(args.output, 'wb') as fh:
            if isinstance(output, str):
                output = output.encode('utf8')
            fh.write(output)


def generate_zip(spec):
    swaggerjson = json.dumps(spec.to_dict())
    src = pkg_resources.resource_stream(
        'pyramid_marshmallow', 'assets/swagger-ui.zip',
    )
    with BytesIO() as fh:
        shutil.copyfileobj(src, fh)
        fh.seek(0)
        with zipfile.ZipFile(fh, 'a') as zip:
            zip.writestr('swagger.json', swaggerjson)
        return fh.getvalue()


if __name__ == '__main__':
    generate()
