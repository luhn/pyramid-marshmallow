import pytest
from pyramid.config import Configurator
from webtest import TestApp


class TestBasicApp:
    @pytest.fixture(autouse=True)
    def _setup(self):
        config = Configurator()
        config.include("tests.pkgs.basicapp")
        wsgi = config.make_wsgi_app()
        self.app = TestApp(wsgi)

    def test_hello_world(self):
        "Just to make sure our sample application is working properly."
        r = self.app.get("/hello")
        assert r.text == "Hello World!"

    def test_post_validate_integration(self):
        response = self.app.post_json(
            "/validate",
            {
                "title": "Hunky Dory",
                "release_date": "1971-12-17",
            },
        )
        assert response.text == "Hunky Dory"

    def test_get_validate_integration(self):
        response = self.app.get(
            "/validate",
            {
                "title": "Hunky Dory",
                "release_date": "1971-12-17",
            },
        )
        assert response.text == "Hunky Dory"

    def test_marshal_integration(self):
        response = self.app.get("/marshal")
        assert response.json == {
            "title": "Hunky Dory",
            "release_date": "1971-12-17",
        }

    def test_get_validate_list_integration(self):
        response = self.app.get(
            "/validate-list",
            {
                "title": "Hunky Dory",
                "artists": ["Bowie", "Wowie"],
            },
        )
        assert response.text == "Bowie, Wowie"


class TestTraversalApp:
    @pytest.fixture(autouse=True)
    def _setup(self):
        config = Configurator()
        config.include("tests.pkgs.traversal")
        wsgi = config.make_wsgi_app()
        self.app = TestApp(wsgi)

    def test_traversal_hello(self):
        r = self.app.get("/album/1")
        assert r.json == {
            "id": 1,
            "title": "Hunky Dory",
            "release_date": "1971-12-17",
        }
