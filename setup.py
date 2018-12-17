from setuptools import setup, find_packages


REQUIRES = [
    'pyramid>=1.7,<2',
    'marshmallow>=2.0,<3',
    'apispec>=0.37,<0.38',
]


setup(
    name='pyramid-marshmallow',
    version='0.4.0',
    description='TODO',
    long_description=open('README.rst').read(),
    license='MIT',
    author='Theron Luhn',
    author_email='theron@luhn.com',
    url='https://github.com/luhn/pyramid-marshmallow',
    packages=find_packages(),
    package_data={
        'pyramid_marshmallow': ['assets/*'],
    },
    install_requires=REQUIRES,
    entry_points={
        'console_scripts': [
            'generate-apispec=pyramid_marshmallow.scripts:generate',
        ],
    },
)
