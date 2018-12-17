

class SchemaError(Exception):
    def __init__(self, errors):
        self.errors = errors


class ValidationError(SchemaError):
    pass


class MarshalError(SchemaError):
    pass
