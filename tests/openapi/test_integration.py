import pytest
from pyramid.config import Configurator

from pyramid_marshmallow.openapi.spec import create_spec


class TestBasicApp:
    @pytest.fixture(autouse=True)
    def _setup(self):
        config = Configurator(
            settings={
                "openapi.title": "Albums",
                "openapi.version": "1.0.0",
                "openapi.openapi_version": "3.0.2",
            }
        )
        config.include("tests.pkgs.basicapp")
        config.commit()
        self.spec = create_spec(config.registry)

    def test_settings(self):
        assert self.spec["openapi"] == "3.0.2"
        assert self.spec["info"] == {"title": "Albums", "version": "1.0.0"}

    def test_schema(self):
        assert self.spec["components"]["schemas"]["Album"] == {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "release_date": {
                    "type": "string",
                    "format": "date",
                    "nullable": True,
                },
                "artists": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        }

    def test_view(self):
        assert self.spec["paths"]["/marshal"] == {
            "get": {
                "summary": (
                    "Returns JSON-serialized information about the album."
                ),
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Album",
                                },
                            },
                        },
                    },
                },
            },
        }


class TestTraversalApp:
    @pytest.fixture(autouse=True)
    def _setup(self):
        config = Configurator(
            settings={
                "openapi.title": "Albums",
                "openapi.version": "1.0.0",
                "openapi.openapi_version": "3.0.2",
            }
        )
        config.include("tests.pkgs.traversal")
        config.commit()
        self.spec = create_spec(config.registry)

    def test_settings(self):
        assert self.spec["openapi"] == "3.0.2"
        assert self.spec["info"] == {"title": "Albums", "version": "1.0.0"}

    def test_schema(self):
        assert self.spec["components"]["schemas"]["Album"] == {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "readOnly": True},
                "title": {"type": "string"},
                "release_date": {
                    "type": "string",
                    "format": "date",
                    "nullable": True,
                },
                "artists": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        }

    def test_view(self):
        assert self.spec["paths"]["/album/{albumId}/"]["post"] == {
            "parameters": [
                {
                    "name": "albumId",
                    "description": "The ID of the album.",
                    "schema": {"type": "integer"},
                    "in": "path",
                    "required": True,
                },
            ],
            "tags": ["album"],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Album"},
                    },
                },
            },
            "responses": {
                "200": {
                    "description": "",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Album"},
                        },
                    },
                },
            },
        }
