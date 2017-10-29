
init:
	pipenv install --dev
	pipenv run python setup.py develop

lint: init
	pipenv run flake8 pyramid_apispec tests

test: init lint
	pipenv run py.test tests/
