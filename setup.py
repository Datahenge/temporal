# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in temporal/__init__.py
from temporal import __version__ as version

setup(
	name='temporal',
	version=version,
	description='Time after Time',
	author='Datahenge LLC',
	author_email='brian@datahenge.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
