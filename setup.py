from setuptools import setup, find_packages


REQUIRES = [
    'pyramid>=1.7,<2',
    'marshmallow>=2.0,<3',
    'apispec>=0.37,<0.38',
]


setup(
    name='pyramid-apispec',
    version='0.1.1',
    description='TODO',
    long_description=open('README.rst').read(),
    author='Theron Luhn',
    author_email='theron@luhn.com',
    url='https://github.com/luhn/pyramid-apispec',
    packages=find_packages(),
    install_requires=REQUIRES,
    license='MIT',
)
