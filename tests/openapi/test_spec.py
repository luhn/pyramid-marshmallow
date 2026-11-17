import pytest
from marshmallow import Schema, fields
from pyramid.config import Configurator

from pyramid_marshmallow.openapi.spec import list_paths, schema_name_resolver


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


class TestListPaths:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.config = Configurator()

    def call(self):
        self.config.commit()
        return [
            (path, method, intr["callable"])
            for path, method, intr in list_paths(
                self.config.registry.introspector
            )
        ]

    def test_route(self):
        def view(request):
            pass

        self.config.add_route("widgets", "/widgets")
        self.config.add_view(view, route_name="widgets", request_method="POST")
        assert self.call() == [("/widgets", "post", view)]

    def test_multiple_methods(self):
        def view(request):
            pass

        self.config.add_route("widgets", "/widgets")
        self.config.add_view(
            view, route_name="widgets", request_method=["PUT", "PATCH"]
        )
        assert sorted(self.call()) == [
            ("/widgets", "patch", view),
            ("/widgets", "put", view),
        ]

    def test_default_get(self):
        def view(request):
            pass

        self.config.add_route("widgets", "/widgets")
        self.config.add_view(view, route_name="widgets")
        assert self.call() == [("/widgets", "get", view)]

    def test_multiple_views_same_route(self):
        def post_view(request):
            pass

        def put_view(request):
            pass

        self.config.add_route("widgets", "/widgets")
        self.config.add_view(
            post_view, route_name="widgets", request_method="POST"
        )
        self.config.add_view(
            put_view, route_name="widgets", request_method="PUT"
        )
        assert self.call() == [
            ("/widgets", "post", post_view),
            ("/widgets", "put", put_view),
        ]

    def test_traversal(self):
        class Context:
            __path__ = "/widgets"

        def view(request):
            pass

        self.config.add_view(view, context=Context, name="list")
        assert self.call() == [("/widgets/list", "get", view)]

    def test_traversal_no_name(self):
        class Context:
            __path__ = "/widgets"

        def view(request):
            pass

        self.config.add_view(view, context=Context)
        assert self.call() == [("/widgets/", "get", view)]

    def test_traversal_no_path(self):
        class Context:
            pass

        def view(request):
            pass

        self.config.add_view(view, context=Context, name="list")
        assert self.call() == []

    def test_no_route_or_context(self):
        def view(request):
            pass

        self.config.add_view(view)
        assert self.call() == []

    def test_no_views(self):
        assert self.call() == []
