# pyramid-marshmallow

pyramid-marshmallow is a simple Pyramid plugin that allows you to validate and
marshal a JSON HTTP request or response using
[Marshmallow](http://marshmallow.readthedocs.io/) schemas.  You can then
leverage this to automatically generate an OpenAPI specification for your API.

## Basic usage

Install the project with `pip install pyramid-marshmallow`.

Activate it by adding `config.include('pyramid_marshmallow')` into your config
function or adding `pyramid.includes = pyramid_marshmallow` into your ini file.

To validate incoming data, set `validate` to a Marshmallow schema in your
`view_config`.  The request body is parsed as JSON then passed through the
schema's `load` function.  You can access the processed data with
`request.data`.

```python
from marshmallow import Schema, String


class HelloSchema(Schema):
    name = String()


@view_config(
    context=Root,
    name='hello',
    request_method='post',
    validate=HelloSchema(),
)
def hello(context, request):
    return Response(body='Hello, {}'.format(
        request.data['name']
    ))
```

For GET requests, the URL parameters are passed into the schema.  Value lists
are not currently supported.

Setting `marshal` in your `view_config` will run the view output through
marshmallow (i.e. `Schema.dump`) before going to the renderer.  You probably
will want to set the renderer to `json`.

```
@view_config(
    context=Root,
    name='hello',
    request_method='get',
    marshal=HelloSchema(),
    renderer='json',
)
def hello(context, request):
    name = fetch_name()
    return {
        'name': name,
    }
```

`validate` and `marshal` operate independently, so can be used separately or
together.

As a convenience, you can pass in a dictionary to `validate` or `marshal` and
pyramid-marshmallow will turn it into a schema for you.

```python
@view_config(
    context=Root,
    name='hello',
    request_method='post',
    validate={
        'name': String(),
    },
)
```

You can also get a schema made from a dictionary by using the
`pyramid_marshmallow.make_schema` function.  This can be useful for `Nested`
fields.


### Error handling

pyramid-marshmallow passes through exceptions from marshmallow.  So errors
during validation will raise a `marshmallow.exceptions.ValidationError`
exception.
([Documentation](https://marshmallow.readthedocs.io/en/stable/api_reference.html#marshmallow.exceptions.ValidationError))

You may want to attach a view to this exception to expose the error messages to
the user.

```python
@view_config(
    context=ValidationError,
    renderer='json',
)
def validation_error(context, request):
    request.response.status = 401  # HTTP Bad Request
    return {
        'errors': context.normalized_messages(),
    }
```

## OpenAPI

By adding validation and marshalling to your views, we have the opportunity to
utilize that data to generate documentation.  pyramid-marshmallow includes an
utility that uses [apispec](https://apispec.readthedocs.io/en/stable/) to
generate an [OpenAPI](https://swagger.io/resources/open-api/) specification for
your application.

First, you'll need to install some extra dependencies.

```bash
pip install pyramid-marshmallow[openapi]
```

Now you can generate your spec by simply passing in an ini file.
pyramid-marshmallow needs to run your application in order to inspect it, so
the ini file should contain all the necessary configuration to do so.

```bash
generate-spec development.ini
```

This will output the spec to stdout as JSON.  You can set the `--output` flag
to output the results to a file.

You can set `--format yaml` to output the spec as YAML instead or
`--format zip` to output a zip file containing the spec and
[Swagger UI](https://swagger.io/tools/swagger-ui/), a web interface for viewing
the spec.

By default, your spec will be titled "Untitled" and versioned "0.1.0".  You can
change this by setting `openapi.title` and `openapi.version` in your ini file.

### Additional Documentation

To add additional documentation to schema fields, you can set the `description`
property.

```python
class Hello(Schema):
    name = String(required=True, description='Your first and last name.')
```

Documentation for the endpoint will be pulled from the view callable's
docstring.

You can also augment the spec by adding a line of three hyphens followed by
YAML.  The YAML will be parsed and merged into to the endpoint's spec.  This
can be useful for documenting endpoints that cannot be validated or marshalled,
such as endpoints that return an empty body.

```python
@view_config(
    context=WidgetResource,
    method='post',
    validate=WidgetSchema(),
)
def create_widget(context, request):
    """
    Create a new widget.
    ---
    responses:
        201:
            description: Indicates the widget was successfully created.
    """
    create_widget()
    return HTTPCreated()
```

## URL Traversal

If you're using Pyramid's URL traversal, the generated spec may be mostly
empty.  This is because pyramid-marshmallow has no way of knowing where in the
resource tree a resource is.  You can denote this by setting the `__path__`
property on each resource.

```python
class Widget(Resource):
    __path__ = '/widget'
```

Views attached to this resource will then be added to the spec.

You can add parameters to your path via the `__params__` property.  You can
also tag all attached views via `__tag__`.  Once you define a tag in one
resource, you can use it elsewhere by setting `__tag__` to the tag name.

```python
class Widget(Resource):
    __path__ = '/widget/{widgetId}'
    __params__ = [{
        'name': 'widgetId',
        'schema': {
            'type': 'integer',
        },
    }]
    __tag__ = {
        'name': 'widgets',
        'description': 'Endpoints for managing a widget.',
    }
```

## Prior Art

[pyramid-apispec](https://pypi.org/project/pyramid-apispec/) allows you to
augment view callable docstrings with OpenAPI definitions and can reference
Marshmallow schemas with the apispec Marshmallow plugin.  It does not support
validating input and marshalling output.  Schemas and routes must be manually
declared.

[Cornice](https://cornice.readthedocs.io/en/latest/schema.html#using-marshmallow)
supports validation with Marshmallow schemas, however only on Cornice
resources, not arbitrary Pyramid endpoints.  It does not support
auto-generating OpenAPI documentation.
