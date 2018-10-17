"""
Setup.py for budget-app
"""
from setuptools import setup, find_packages

setup(
    name='budget_app',
    version='0.0.1',
    description='Budget mkononi demo app',
    license='Apache 2.0',
    author='Ona Kenya',
    author_email='tech@ona.io',
    packages=find_packages(exclude=['docs', 'tests']),
    install_requires=[
        'django-micro',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
)