

def test_hello_world(app):
    "Just to make sure our sample application is working properly."
    r = app.get('/hello')
    assert r.text == 'Hello World!'


def test_validate_integration(app):
    assert app.post_json('/validate', {
        'title': 'Hunky Dory',
        'release_date': '1971-12-17',
    }).text == 'Hunky Dory'
