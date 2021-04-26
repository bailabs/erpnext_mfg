# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in erpnext_mfg/__init__.py
from erpnext_mfg import __version__ as version

setup(
	name='erpnext_mfg',
	version=version,
	description='ERPNext MFG',
	author='Bai Web and Mobile Lab',
	author_email='hello@bai.ph',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
