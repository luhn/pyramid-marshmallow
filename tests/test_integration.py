def test_hello_world(app):
    "Just to make sure our sample application is working properly."
    r = app.get("/hello")
    assert r.text == "Hello World!"


def test_traversal_hello(app):
    r = app.get("/album/hello")
    assert r.text == "Hello World!"


def test_post_validate_integration(app):
    assert (
        app.post_json(
            "/validate",
            {
                "title": "Hunky Dory",
                "release_date": "1971-12-17",
            },
        ).text
        == "Hunky Dory"
    )


def test_get_validate_integration(app):
    assert (
        app.get(
            "/validate",
            {
                "title": "Hunky Dory",
                "release_date": "1971-12-17",
            },
        ).text
        == "Hunky Dory"
    )


def test_get_validate_list_integration(app):
    assert (
        app.get(
            "/validate-list",
            {
                "title": "Hunky Dory",
                "artists": ["Bowie", "Wowie"],
            },
        ).text
        == "Bowie, Wowie"
    )


def test_marshal_integration(app):
    assert app.get("/marshal").json == {
        "title": "Hunky Dory",
        "release_date": "1971-12-17",
    }
