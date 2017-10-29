from setuptools import setup, find_packages


REQUIRES = [
]


setup(
    name='pyramid-apispec',
    version='0.1.0',
    description='TODO',
    long_description=read('README.rst'),
    author='Theron Luhn',
    author_email='theron@luhn.com',
    url='https://github.com/luhn/pyramid-apispec',
    packages=find_packages(),
    install_requires=REQUIRES,
    license='MIT',
)
