
lint:
	poetry run flake8 pyramid_apispec tests

test: lint
	poetry run pytest tests/

.PHONY: lint test
