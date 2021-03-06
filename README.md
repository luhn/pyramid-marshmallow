# pyramid-marshmallow

pyramid-marshmallow is a simple Pyramid plugin that allows you to validate and marshal a JSON HTTP request or response using [Marshmallow](http://marshmallow.readthedocs.io/) schemas.
You can then leverage this to automatically generate an OpenAPI specification for your API.

> **Version 0.5 and greater requires Marshmallow 3.x.  For Marshmallow 2.x, use version 0.4.**

## Basic usage

Install the project with `pip install pyramid-marshmallow`.

Activate it by adding `config.include('pyramid_marshmallow')` into your config function or adding `pyramid.includes = pyramid_marshmallow` into your ini file.

To validate incoming data, set `validate` to a Marshmallow schema in your `view_config`.
The request body is parsed as JSON then passed through the schema's `load` function.
You can access the processed data with `request.data`.

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

For GET requests, the URL parameters are passed into the schema.
Value lists are not currently supported.

Setting `marshal` in your `view_config` will run the view output through marshmallow (i.e. `Schema.dump`) before going to the renderer.
You probably will want to set the renderer to `json`.

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

`validate` and `marshal` operate independently, so can be used separately or together.

As a convenience, you can pass in a dictionary to `validate` or `marshal` and pyramid-marshmallow will turn it into a schema for you.

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

You can also get a schema made from a dictionary by using Marshmallow's `Schema.from_dict` classmethod.
This can be useful for `Nested` fields.


### Error handling

pyramid-marshmallow passes through exceptions from marshmallow.
So errors during validation will raise a `marshmallow.exceptions.ValidationError` exception.
([Documentation](https://marshmallow.readthedocs.io/en/stable/api_reference.html#marshmallow.exceptions.ValidationError))

You may want to attach a view to this exception to expose the error messages to the user.

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

By adding validation and marshalling to your views, we have the opportunity to utilize that data to generate documentation.
pyramid-marshmallow includes an utility that uses [apispec](https://apispec.readthedocs.io/en/stable/) to generate an [OpenAPI](https://swagger.io/resources/open-api/) specification for your application.

First, you'll need to install some extra dependencies.

```bash
pip install pyramid-marshmallow[openapi]
```

You can generate your spec by calling the `generate-spec` command with your application as the first argument, formatted as `[module]:[name]`.

```bash
generate-spec myproject:app
```

If you configure your application via an ini file (Paste), you can also use that.

```bash
generate-spec --ini development.ini
```

This will output the spec to stdout as JSON.
You can set the `--output` flag to output the results to a file.

You can set `--format yaml` to output the spec as YAML instead or `--format html` to output the spec as an HTML file, powered by [ReDoc](https://github.com/Redocly/redoc).

By default, your spec will be titled "Untitled" and versioned "0.1.0".
You can change this by setting `openapi.title` and `openapi.version` in your ini file.

### Documenting Your API

Documentation will be autogenerated from the structure of your Pyramid app and your `validate` and `marshal` declarations.
You can document schema fields by setting the `description` property.

```python
class Hello(Schema):
    name = String(required=True, description='Your first and last name.')
```

The first line of a view callable's docstring will be used as the `summary` property.
The following lines will be used for the `description`.


Documentation for the endpoint will be pulled from the view callable's docstring.
The first line becomes the `summary` and the remaining lines become the `description`.

You can also a line with three hyphens followed by a YAML object.
This will be merged with the auto-generated [operation object](https://swagger.io/specification/#operationObject) and can be used to manually augment the spec.

```python
@view_config(
    context=WidgetResource,
    method='post',
    validate=WidgetSchema(),
)
def create_widget(context, request):
    """
    Create new widget

    Creates a new widget with an attached plumbus.

    ---
    responses:
        201:
            description: Indicates the widget was successfully created.
    """
    widget.make()
    return HTTPCreated()
```

You can also pass a dictionary as the `api_spec` property to `Configurator.add_view` or `@view_config`, which will be merged with the spec in the same way.
This can be advantageous if a single function services multiple views.

```python
@view_config(
    context=WidgetResource,
    method='post',
    validate=WidgetSchema(),
    api_spec={
        'summary': 'Create widget',
    },
)
@view_config(
    context=WidgetResource,
    method='put',
    validate=WidgetSchema(),
    api_spec={
        'summary': 'Update widget',
    },
)
def create_widget(context, request):
    """
    Create/update new widget

    ---
    responses:
        201:
            description: Indicates the widget was successfully created.
    """
    widget.create_or_update()
    return HTTPCreated()
```

## URL Traversal

If you're using Pyramid's URL traversal, the generated spec may be mostly empty.
This is because pyramid-marshmallow has no way of knowing where in the resource tree a resource is.
You can denote this by setting the `__path__` property on each resource.

```python
class Widget(Resource):
    __path__ = '/widget'
```

Views attached to this resource will then be added to the spec.

You can add parameters to your path via the `__params__` property.
You can also tag all attached views via `__tag__`.
Once you define a tag in one resource, you can use it elsewhere by setting `__tag__` to the tag name.

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

## Mergefile

You likely will wish to augment your API spec with a description, additional components, and more.
This can be achieved with a mergefile.
Write a YAML file with the parts of the spec you wish to augment and pass the filename as the `--merge` flag with `generate-spec`.
You can also reference a package resource in the format `[package]:[path]`.
The file will be loaded and merged into the generated spec.
You can use the `--merge` flag multiple times to merge in multiple files.
You can also add a merge file by adding the path to the `pyramid_marshmallow.merge` setting in your Pyramid application.
Multiple mergefiles can be separated with a comma.

## Zones

It may be that not all endpoints are made available to all users.
For example, you may have all endpoints available internally but only select ones available publicly.
You would then want separate API docs for internal users versus external users.
This can be achieved using zones.

Tag each endpoint by setting `api_zone` in `Configuration.add_view` or `@view_config`.
By default, all endpoints regardless of zone will be added to the spec.
Set the `--zone` flag in `generate-spec` to only put endpoints assigned to that zone in the spec.

## Prior Art

[pyramid-apispec](https://pypi.org/project/pyramid-apispec/) allows you to augment view callable docstrings with OpenAPI definitions and can reference Marshmallow schemas with the apispec Marshmallow plugin.
It does not support validating input and marshalling output.
Schemas and routes must be manually declared.

[Cornice](https://cornice.readthedocs.io/en/latest/schema.html#using-marshmallow) supports validation with Marshmallow schemas, however only on Cornice resources, not arbitrary Pyramid endpoints.
It does not support auto-generating OpenAPI documentation.
