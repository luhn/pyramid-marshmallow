
lint:
	ruff check pyramid_marshmallow tests
	ruff format --check pyramid_marshmallow tests

format:
	ruff format pyramid_marshmallow tests

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
