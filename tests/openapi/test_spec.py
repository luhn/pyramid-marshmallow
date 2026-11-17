from marshmallow import Schema, fields

from pyramid_marshmallow.openapi.spec import schema_name_resolver


class TestSchemaNameResolver:
    def call(self, schema):
        return schema_name_resolver(schema)

    def test_take_class_name(self):
        class ClassNameTest(Schema):
            id = fields.Integer()

        assert self.call(ClassNameTest) == "ClassNameTest"

    def test_take_instance_name(self):
        class InstanceNameTest(Schema):
            id = fields.Integer()

        assert self.call(InstanceNameTest()) == "InstanceNameTest"

    def test_strip_schema(self):
        class StripSchema(Schema):
            id = fields.Integer()

        assert self.call(StripSchema) == "Strip"

    def test_unregistered(self):
        MySchema = Schema.from_dict(
            {
                "id": fields.Integer(),
            }
        )

        assert self.call(MySchema) is False

    def test_only(self):
        class OnlyTest(Schema):
            id = fields.Integer()
            name = fields.String()

        assert self.call(OnlyTest(only=["name"])) is False

    def test_exclude(self):
        class ExcludeTest(Schema):
            id = fields.Integer()
            name = fields.String()

        assert self.call(ExcludeTest(exclude=["id"])) is False

    def test_partial(self):
        class PartialTest(Schema):
            id = fields.Integer()
            name = fields.String()

        assert self.call(PartialTest(partial=True)) == "PartialPartialTest"
