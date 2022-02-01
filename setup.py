from setuptools import find_packages, setup

VERSION = "0.7.0"
CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Framework :: Pyramid",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Programming Language :: Python",
]

REQUIRES = [
    "pyramid>=1.7",
    "marshmallow~=3.0",
    "zope.interface>=3.8.0",
]

EXTRAS_REQUIRE = {
    "openapi": [
        "apispec>=3.0,<6",
        "PyYAML>=5.4,<7",
    ],
    "testing": [
        "pytest~=6.2",
        "webtest~=2.0",
    ],
    "linting": [
        "black==20.8b1",
        "flake8~=3.8",
        "isort~=5.7",
    ],
}

DESCRIPTION = (
    "Validate request and response data with Marshmallow and optionally "
    "generate an OpenAPI spec."
)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pyramid-marshmallow",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Theron Luhn",
    author_email="theron@luhn.com",
    url="https://github.com/luhn/pyramid-marshmallow",
    packages=find_packages(),
    install_requires=REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "generate-spec=pyramid_marshmallow.openapi.generate:generate",
            "serve-spec=pyramid_marshmallow.openapi.serve:serve",
        ],
    },
)
