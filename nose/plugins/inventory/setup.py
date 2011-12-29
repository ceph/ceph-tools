"""
nose plugin for test-case inventory/description

    from this directory, run easy_install .
"""
import sys
try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass
from setuptools import setup

setup(
    name='Test Inventory plugin',
    version='0.1',
    author='Mark Kampe',
    author_email = 'mark.kampe@dreamhost.com',
    description = 'Test Inventory',
    license = 'LGPL',
    py_modules = ['inventory'],
    entry_points = {
        'nose.plugins': [
            'test_inventory = inventory:TestInventory'
            ]
        }
    )
