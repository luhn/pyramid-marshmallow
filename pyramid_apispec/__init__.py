from .exceptions import ValidationError


def includeme(config):
    config.add_view_deriver(view_validator)


def view_validator(view, info):
    schema = info.options.get('validate')
    if schema is None:
        return view

    def wrapped(context, request):
        result = schema.load(request.json_body)
        if result.errors:
            raise ValidationError(result.errors)
        request.data = result.data
        return view(context, request)

    return wrapped


view_validator.options = ('validate',)
