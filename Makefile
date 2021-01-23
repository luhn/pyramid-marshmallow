
lint:
	isort pyramid_marshmallow tests
	black pyramid_marshmallow tests
	flake8 pyramid_marshmallow tests

test: lint
	pytest tests

.PHONY: lint test
