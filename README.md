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
`view_config`.  The deserialized data (i.e. the output of `Schema.load`) is
placed in `request.data`.

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


## Error handling

If the validation fails, a `pyramid_marshmallow.ValidationError` is raised.
The `errors` property of the exception contains a dictionary of error messages,
just like the `Schema.load` method returns.

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
        'errors': context.errors,
    }
```

A failure during marshalling will result in a
`pyramid_marshmallow.MarshalError` which behaves in the same manner.  It's
usually less useful to attach a view to that exception, since marshalling
errors are usually not encountered during standard operation.
