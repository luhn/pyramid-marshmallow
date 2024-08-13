
lint:
	isort pyramid_marshmallow tests
	black pyramid_marshmallow tests
	flake8 pyramid_marshmallow tests

test: lint
	pytest tests

build:
	rm -r dist/ || true
	pip install -q build
	python -m build --sdist --wheel --outdir dist/

publish: build
	pip install -q twine
	python -m twine upload dist/*

.PHONY: lint test build publish
