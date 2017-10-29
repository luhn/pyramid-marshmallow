

def test_hello_world(app):
    r = app.get('/hello')
    assert r.text == 'Hello World!'
