
init:
	pipenv install --dev
	pipenv run python setup.py develop

test: init
	pipenv run py.test tests/
