from importlib import import_module


def import_attr(spec):
    """
    Import an attribute from a module via a string specification, such as
    ``urllib.parse:urlparse``.  If the string ends with ``()``, the attribute
    is understood to be a function:  It will be executed with no arguments and
    the result returned.

    This function is used to load Pyramid application.
    """
    if spec.endswith("()"):
        is_function = True
        spec = spec[:-2]
    else:
        is_function = False
    module_name, _, attr_name = spec.partition(":")
    module = import_module(module_name)
    attr = getattr(module, attr_name)
    return attr() if is_function else attr
