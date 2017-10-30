from .exceptions import ValidationError


def includeme(config):
    config.add_view_deriver(view_validator)


def view_validator(view, info):
    schema = info.options.get('validate')
    if schema is None:
        return view

    def wrapped(context, request):
        if request.method == 'GET':
            data = dict(request.GET)
        else:
            data = request.json_body
        result = schema.load(data)
        if result.errors:
            raise ValidationError(result.errors)
        request.data = result.data
        return view(context, request)

    return wrapped


view_validator.options = ('validate',)
