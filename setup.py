from setuptools import setup, find_packages


REQUIRES = [
    'pyramid>=1.7,<2',
    'marshmallow>=2.0,<3',
    'apispec>=0.37,<0.38',
]


setup(
    name='pyramid-apispec',
    version='0.2.0',
    description='TODO',
    long_description=open('README.rst').read(),
    license='MIT',
    author='Theron Luhn',
    author_email='theron@luhn.com',
    url='https://github.com/luhn/pyramid-apispec',
    packages=find_packages(),
    package_data={
        'pyramid_apispec': ['assets/*'],
    },
    install_requires=REQUIRES,
    entry_points={
        'console_scripts': [
            'generate-apispec=pyramid_apispec.scripts:generate',
        ],
    },
)
