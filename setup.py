from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-deadoralive',
    version=version,
    description="A broken link checker extension for CKAN",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Sean Hammond',
    author_email='deadoralive@seanh.cc',
    url='https://github.com/ckan/ckanext-deadoralive',
    license='GNU AFFERO GENERAL PUBLIC LICENSE',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.deadoralive'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        # Add plugins here, e.g.
        deadoralive=ckanext.deadoralive.plugin:DeadOrAlivePlugin
    ''',
)
